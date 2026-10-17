#!/usr/bin/env python3
"""Audit all 67 synthesized TTS turns and 5 master chapter WAVs:
1. Deterministic acoustic checks (duration, speech rate chars/s, RMS dBFS, peak dBFS).
2. Multimodal Gemini 3.8 Flash audio listening audit on each book's master WAV
   to verify pronunciation, voice distinction, and natural restraint.
"""

import base64
import concurrent.futures
import json
import math
import os
import urllib.request
import wave
from pathlib import Path
import numpy as np

from books_spec import BOOKS_SPEC

ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = ROOT / "audio"
TURNS_DIR = AUDIO_DIR / "turns"


def get_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key.startswith("AQ."):
        return key
    profile = Path.home() / ".profile"
    if profile.exists():
        for line in profile.read_text().splitlines():
            if line.strip().startswith("export GEMINI_API_KEY="):
                return line.strip().split("=", 1)[1].strip()
    if key:
        return key
    raise RuntimeError("GEMINI_API_KEY not found")


def analyze_wav(path: Path) -> dict:
    with wave.open(str(path), "rb") as wf:
        sr = wf.getframerate()
        n = wf.getnframes()
        raw = wf.readframes(n)
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    dur = n / float(sr)
    peak = float(np.max(np.abs(samples))) if len(samples) else 0.0
    rms = float(np.sqrt(np.mean(samples ** 2))) if len(samples) else 0.0
    peak_db = 20.0 * math.log10(max(peak, 1e-7))
    rms_db = 20.0 * math.log10(max(rms, 1e-7))
    return {
        "duration_s": round(dur, 3),
        "peak_dbfs": round(peak_db, 2),
        "rms_dbfs": round(rms_db, 2),
    }


def gemini_listen_audit(book: dict, master_wav: Path, api_key: str) -> dict:
    b64_audio = base64.b64encode(master_wav.read_bytes()).decode("utf-8")
    expected_turns = [
        f"Turn {idx:02d} [{t['speaker']}]: {t['display_text']}"
        for idx, t in enumerate(book["turns"])
    ]
    prompt = (
        f"Listen carefully to this audiobook recording of {book['title']} by {book['author']}.\n"
        "Here are the expected turns in order:\n"
        + "\n".join(expected_turns)
        + "\n\nEvaluate strictly and return JSON with keys:\n"
        "- overall_score (1-10)\n"
        "- pronunciation_ok (boolean)\n"
        "- pronunciation_notes (string: confirm how key words like Netherfield, chaise, Penang, ferrule, recondite, Filby, etc. were pronounced)\n"
        "- voice_distinction_ok (boolean: are narrator and character voices distinct and consistent?)\n"
        "- pacing_and_tone_notes (string: is the acting interesting yet restrained, or is any turn overdone/rushed/cut off?)\n"
        "- flagged_turns (list of integer turn indices that have any pronunciation error, cutoff, glitch, or overdone acting; empty list if all turns are clean)"
    )

    payload = {
        "model": "gemini-3.8-flash",
        "input": [
            {"type": "audio", "data": b64_audio, "mime_type": "audio/wav"},
            {"type": "text", "text": prompt},
        ],
    }
    req = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/interactions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-goog-api-key": api_key,
            "Content-Type": "application/json",
            "Api-Revision": "2026-05-20",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    text_out = ""
    for step in data.get("steps", []):
        for block in step.get("content", []):
            if block.get("type") == "text":
                text_out += block.get("text", "")
    return {"book_id": book["id"], "audit_response": text_out.strip()}


def main():
    print("=== 1. Deterministic Turn-Level Acoustic Check ===")
    anomalies = []
    for book in BOOKS_SPEC:
        book_id = book["id"]
        for idx, turn in enumerate(book["turns"]):
            wav_path = TURNS_DIR / f"{book_id}_turn_{idx:02d}.wav"
            stats = analyze_wav(wav_path)
            clean_text = turn["tts_text"].replace("<short pause>", "")
            cps = len(clean_text) / max(stats["duration_s"], 0.1)
            flag = ""
            if stats["rms_dbfs"] < -38.0:
                flag += " LOW_RMS"
            if len(clean_text) > 20 and (cps > 23.0 or cps < 7.0):
                flag += f" ABNORMAL_CPS({cps:.1f})"
            if flag:
                anomalies.append((wav_path.name, stats, cps, flag, clean_text))
            print(
                f"  {wav_path.name}: dur={stats['duration_s']:5.2f}s | "
                f"cps={cps:4.1f} | rms={stats['rms_dbfs']:6.2f} dB | "
                f"peak={stats['peak_dbfs']:5.2f} dB | [{turn['speaker']}] {flag}"
            )

    if anomalies:
        print(f"\nFound {len(anomalies)} acoustic anomalies:")
        for item in anomalies:
            print(" ", item)
    else:
        print("\nAll 67 turns passed deterministic acoustic checks.")

    print("\n=== 2. Gemini 3.8 Flash Multimodal Listening Audit ===")
    api_key = get_api_key()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        futs = [
            ex.submit(
                gemini_listen_audit,
                book,
                AUDIO_DIR / f"{book['id']}_master.wav",
                api_key,
            )
            for book in BOOKS_SPEC
        ]
        results = [f.result() for f in futs]

    for r in results:
        print(f"\n--- {r['book_id']} ---")
        print(r["audit_response"])

    (AUDIO_DIR / "audio_audit_report.json").write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
