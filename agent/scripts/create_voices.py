#!/usr/bin/env python3
"""Create all 15 custom character and narrator voices using Gemini 3.8 Flash TTS Voice Design
(POST /v1beta/voices with type='prompted', model='gemini-3.8-flash-tts').

Saves:
- voices/voices_manifest.json (mapping speaker_key -> voice_id, metadata)
- voices/<speaker_key>_preview.wav (sample_audio returned by CreateVoice)
"""

import base64
import concurrent.futures
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

from books_spec import VOICES_SPEC

ROOT = Path(__file__).resolve().parent.parent
VOICES_DIR = ROOT / "voices"
MANIFEST_PATH = VOICES_DIR / "voices_manifest.json"


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


def create_one_voice(speaker_key: str, spec: dict, api_key: str) -> tuple[str, dict]:
    url = "https://generativelanguage.googleapis.com/v1beta/voices"
    payload = {
        "store": True,
        "voice": {
            "model": "gemini-3.8-flash-tts",
            "type": "prompted",
            "display_name": spec["display_name"],
            "gender": spec["gender"],
            "language_code": spec["language_code"],
            "prompted": {
                "input": spec["prompt"],
            },
        },
    }
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
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    voice_id = data["id"]
    preview_path = VOICES_DIR / f"{speaker_key}_preview.wav"
    sample = data.get("sample_audio", {})
    if sample and sample.get("data"):
        preview_path.write_bytes(base64.b64decode(sample["data"]))

    info = {
        "speaker_key": speaker_key,
        "voice_id": voice_id,
        "display_name": spec["display_name"],
        "gender": spec["gender"],
        "language_code": spec["language_code"],
        "prompt": spec["prompt"],
        "preview_wav": str(preview_path.relative_to(ROOT)),
    }
    print(f"[OK] {speaker_key:18s} -> {voice_id} ({spec['display_name']})")
    return speaker_key, info


def main():
    VOICES_DIR.mkdir(parents=True, exist_ok=True)

    manifest = {}
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text())

    updated = False
    to_create = {}
    for k, v in VOICES_SPEC.items():
        if v.get("voice_id"):
            preview_path = VOICES_DIR / f"{k}_preview.wav"
            info = {
                "speaker_key": k,
                "voice_id": v["voice_id"],
                "display_name": v["display_name"],
                "gender": v["gender"],
                "language_code": v["language_code"],
                "persona_style": v.get("persona_style", ""),
                "prompt": v["prompt"],
                "preview_wav": str(preview_path.relative_to(ROOT)),
            }
            if manifest.get(k) != info:
                manifest[k] = info
                updated = True
        elif k not in manifest:
            to_create[k] = v

    if updated:
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"Updated prebuilt studio voices in {MANIFEST_PATH}")

    if not to_create:
        print(f"All {len(manifest)} voices ready in {MANIFEST_PATH}")
        return

    api_key = get_api_key()
    print(f"Creating {len(to_create)} custom voices via Gemini 3.8 Flash TTS Voice Design...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        futures = {
            ex.submit(create_one_voice, k, v, api_key): k
            for k, v in to_create.items()
        }
        for fut in concurrent.futures.as_completed(futures):
            k = futures[fut]
            try:
                _, info = fut.result()
                manifest[k] = info
                MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
            except Exception as e:
                print(f"[ERR] {k}: {e}")
                raise

    print(f"Saved {len(manifest)} voices to {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
