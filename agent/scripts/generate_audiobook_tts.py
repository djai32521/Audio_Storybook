#!/usr/bin/env python3
"""Synthesize multi-voice audiobook readings for all 5 books using Gemini 3.8 Flash TTS
(gemini-3.8-flash-tts) and the persistent custom voices created in Voice Design.

Saves:
- audio/turns/<book_id>_turn_<idx:02d>.wav (individual 24kHz WAV per turn)
- audio/<book_id>_master.wav (assembled chapter audio with natural turn-taking pauses
  and 2.5s title card intro + 1.0s chapter outro)
- audio/timeline_manifest.json (exact millisecond timestamps for every turn and scene)
"""

import argparse
import base64
import concurrent.futures
import json
import os
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path
import numpy as np

from books_spec import BOOKS_SPEC

ROOT = Path(__file__).resolve().parent.parent
VOICES_MANIFEST = ROOT / "voices" / "voices_manifest.json"
AUDIO_DIR = ROOT / "audio"
TURNS_DIR = AUDIO_DIR / "turns"
TIMELINE_PATH = AUDIO_DIR / "timeline_manifest.json"

SAMPLE_RATE = 24000
TITLE_CARD_HOLD_SEC = 2.6
CHAPTER_OUTRO_SEC = 1.0


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


def synthesize_turn(
    tts_text: str,
    style: str,
    voice_id: str,
    out_wav_path: Path,
    api_key: str,
    retries: int = 4,
) -> Path:
    url = "https://generativelanguage.googleapis.com/v1beta/interactions"
    annotation = {"type": "speech_metadata"}
    if style:
        annotation["style"] = style

    payload = {
        "model": "gemini-3.8-flash-tts",
        "input": [
            {
                "type": "user_input",
                "content": [
                    {
                        "type": "text",
                        "text": tts_text,
                        "annotations": [annotation],
                    }
                ],
            }
        ],
        "response_format": {
            "type": "audio",
            "mime_type": "audio/wav",
            "sample_rate": SAMPLE_RATE,
        },
        "generation_config": {
            "speech_config": [
                {"voice": voice_id},
            ]
        },
    }

    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "x-goog-api-key": api_key,
                    "Content-Type": "application/json",
                    "Api-Revision": "2026-05-20",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            for step in data.get("steps", []):
                for block in step.get("content", []):
                    if block.get("type") == "audio" and block.get("data"):
                        raw = base64.b64decode(block["data"])
                        out_wav_path.parent.mkdir(parents=True, exist_ok=True)
                        out_wav_path.write_bytes(raw)
                        return out_wav_path
            raise RuntimeError(f"No audio block returned: {json.dumps(data)[:300]}")
        except Exception as e:
            if attempt == retries:
                raise
            print(f"[RETRY {attempt}/{retries}] {out_wav_path.name}: {e}")
            time.sleep(2 * attempt)
    raise RuntimeError(f"Failed to synthesize {out_wav_path}")


from voice_mastering import warm_master_voice_turn


def read_wav_pcm16(wav_path: Path) -> np.ndarray:
    """Read a WAV file (or raw PCM fallback) as 1D int16 numpy array at 24kHz mono,
    trimming leading/trailing dead digital silence > 80ms, applying warm zero-phase
    chest/presence/de-esser mastering, and applying a gentle 15ms fade-in/fade-out.
    """
    raw_bytes = wav_path.read_bytes()
    if raw_bytes[:4] == b"RIFF":
        with wave.open(str(wav_path), "rb") as wf:
            frames = wf.readframes(wf.getnframes())
            samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
    else:
        samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32)

    # Trim excessive leading/trailing silence (threshold ~120 out of 32768)
    abs_s = np.abs(samples)
    non_silent = np.where(abs_s > 120)[0]
    if len(non_silent) > 0:
        pad = int(0.05 * SAMPLE_RATE)  # keep 50ms natural breath pad
        start = max(0, int(non_silent[0]) - pad)
        end = min(len(samples), int(non_silent[-1]) + pad)
        samples = samples[start:end]

    # Gentle 15ms fade-in and fade-out
    fade_len = min(int(0.015 * SAMPLE_RATE), len(samples) // 4)
    if fade_len > 0:
        fade_in = np.linspace(0.0, 1.0, fade_len, dtype=np.float32)
        fade_out = np.linspace(1.0, 0.0, fade_len, dtype=np.float32)
        samples[:fade_len] *= fade_in
        samples[-fade_len:] *= fade_out

    norm = warm_master_voice_turn(samples / 32768.0, sr=SAMPLE_RATE, target_rms=3450.0 / 32768.0)
    if fade_len > 0:
        norm[:fade_len] *= fade_in
        norm[-fade_len:] *= fade_out

    return np.clip(norm * 32767.0, -32767, 32767).astype(np.int16)


def write_wav_pcm16(wav_path: Path, samples: np.ndarray):
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(samples.astype(np.int16).tobytes())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", help="Optional book_id filter")
    parser.add_argument("--turn", type=int, help="Optional 0-based turn index to regenerate")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if not VOICES_MANIFEST.exists():
        raise RuntimeError(f"Voices manifest not found at {VOICES_MANIFEST}. Run create_voices.py first.")
    voices_map = json.loads(VOICES_MANIFEST.read_text())
    api_key = get_api_key()

    TURNS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Synthesize all turns in parallel (bounded concurrency)
    tasks = []
    for book in BOOKS_SPEC:
        if args.book and book["id"] != args.book:
            continue
        for t_idx, turn in enumerate(book["turns"]):
            if args.turn is not None and t_idx != args.turn:
                continue
            wav_path = TURNS_DIR / f"{book['id']}_turn_{t_idx:02d}.wav"
            if args.force or args.turn is not None or not wav_path.exists():
                v_info = voices_map[turn["speaker"]]
                voice_id = v_info["voice_id"]
                persona_style = v_info.get("persona_style", "").strip()
                turn_style = turn.get("style", "").strip()
                if persona_style and turn_style:
                    full_style = f"{persona_style}. Delivery: {turn_style}"
                else:
                    full_style = persona_style or turn_style
                tasks.append((book["id"], t_idx, turn, full_style, voice_id, wav_path))

    if tasks:
        print(f"Synthesizing {len(tasks)} audiobook turns via Gemini 3.8 Flash TTS...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
            futs = {
                ex.submit(
                    synthesize_turn,
                    turn["tts_text"],
                    full_style,
                    voice_id,
                    wav_path,
                    api_key,
                ): (book_id, t_idx, wav_path)
                for (book_id, t_idx, turn, full_style, voice_id, wav_path) in tasks
            }
            for fut in concurrent.futures.as_completed(futs):
                book_id, t_idx, wav_path = futs[fut]
                fut.result()
                print(f"[OK] {wav_path.name} ({wav_path.stat().st_size} bytes)")

    # 2. Assemble each book's master WAV and build timeline_manifest.json
    timeline = {"sample_rate": SAMPLE_RATE, "books": []}
    for book in BOOKS_SPEC:
        book_id = book["id"]
        chunks = []

        # Leading silence during the 2.6s Chapter Title Card
        title_samples = int(round(TITLE_CARD_HOLD_SEC * SAMPLE_RATE))
        chunks.append(np.zeros(title_samples, dtype=np.int16))
        cursor_samples = title_samples

        turn_records = []
        for t_idx, turn in enumerate(book["turns"]):
            wav_path = TURNS_DIR / f"{book_id}_turn_{t_idx:02d}.wav"
            pcm = read_wav_pcm16(wav_path)
            start_sec = cursor_samples / SAMPLE_RATE
            dur_sec = len(pcm) / SAMPLE_RATE
            end_sec = start_sec + dur_sec

            pause_sec = turn.get("pause_after_ms", 380) / 1000.0
            pause_samples = int(round(pause_sec * SAMPLE_RATE))

            chunks.append(pcm)
            chunks.append(np.zeros(pause_samples, dtype=np.int16))
            cursor_samples += len(pcm) + pause_samples

            voice_info = voices_map[turn["speaker"]]
            turn_records.append({
                "turn_idx": t_idx,
                "speaker_key": turn["speaker"],
                "speaker_label": turn["label"],
                "voice_id": voice_info["voice_id"],
                "voice_display_name": voice_info["display_name"],
                "is_dialogue": turn["is_dialogue"],
                "scene_idx": turn["scene_idx"],
                "display_text": turn["display_text"],
                "tts_text": turn["tts_text"],
                "style": turn["style"],
                "start_sec": round(start_sec, 4),
                "end_sec": round(end_sec, 4),
                "duration_sec": round(dur_sec, 4),
                "pause_after_sec": round(pause_sec, 4),
                "wav_file": str(wav_path.relative_to(ROOT)),
            })

        # Trailing chapter outro silence
        outro_samples = int(round(CHAPTER_OUTRO_SEC * SAMPLE_RATE))
        chunks.append(np.zeros(outro_samples, dtype=np.int16))
        cursor_samples += outro_samples

        total_duration_sec = cursor_samples / SAMPLE_RATE
        master_pcm = np.concatenate(chunks)
        master_wav_path = AUDIO_DIR / f"{book_id}_master.wav"
        write_wav_pcm16(master_wav_path, master_pcm)

        # Compute scene windows [start_sec, end_sec]
        scene_windows = []
        for s_idx, scene in enumerate(book["scenes"]):
            s_turns = [t for t in turn_records if t["scene_idx"] == s_idx]
            s_start = TITLE_CARD_HOLD_SEC if s_idx == 0 else s_turns[0]["start_sec"]
            if s_idx < len(book["scenes"]) - 1:
                next_turns = [t for t in turn_records if t["scene_idx"] == s_idx + 1]
                s_end = next_turns[0]["start_sec"]
            else:
                s_end = total_duration_sec
            scene_windows.append({
                "scene_idx": s_idx,
                "scene_id": scene["id"],
                "caption": scene["caption"],
                "image_file": f"illustrations/{book_id}_scene_{s_idx + 1}.jpg",
                "start_sec": round(s_start, 4),
                "end_sec": round(s_end, 4),
                "duration_sec": round(s_end - s_start, 4),
            })

        book_record = {
            "id": book_id,
            "roman": book["roman"],
            "title": book["title"],
            "author": book["author"],
            "year": book["year"],
            "chapter_title": book["chapter_title"],
            "genre": book["genre"],
            "setting": book["setting"],
            "palette": book["palette"],
            "title_card_end_sec": TITLE_CARD_HOLD_SEC,
            "total_duration_sec": round(total_duration_sec, 4),
            "master_wav": str(master_wav_path.relative_to(ROOT)),
            "char_sheet_image": f"illustrations/{book_id}_char_sheet.jpg",
            "scenes": scene_windows,
            "turns": turn_records,
        }
        timeline["books"].append(book_record)
        print(
            f"[MASTER WAV] {book_id}: {total_duration_sec:.2f}s"
            f" ({len(turn_records)} turns, {len(scene_windows)} scenes)"
        )

    TIMELINE_PATH.write_text(json.dumps(timeline, indent=2))
    print(f"Saved timeline manifest to {TIMELINE_PATH}")


if __name__ == "__main__":
    main()
