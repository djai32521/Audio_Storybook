#!/usr/bin/env python3
"""Create the 6 custom voices for Voltaire's Candide (Chapters I-XII) using
Gemini 3.8 Flash TTS Voice Design (POST /v1beta/voices with type='prompted')
and merge them into voices/voices_manifest.json.
"""

import base64
import concurrent.futures
import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOICES_DIR = ROOT / "voices"
MANIFEST_PATH = VOICES_DIR / "voices_manifest.json"

CANDIDE_VOICES_SPEC = {
    "voltaire_narrator": {
        "display_name": "Voltaire Narrator",
        "gender": "MALE",
        "language_code": "en-GB",
        "prompt": (
            "A cultured, urbane British male literary narrator in his late forties with a"
            " crisp, velvet baritone voice. He reads 18th-century Enlightenment philosophical"
            " satire with effortless precision, dry deadpan wit, and aristocratic poise,"
            " letting the absurdity of events speak for itself without overacting."
        ),
    },
    "candide": {
        "display_name": "Candide",
        "gender": "MALE",
        "language_code": "en-GB",
        "prompt": (
            "An earnest, gentle-hearted, sincere young British man in his early twenties"
            " with a clear, warm tenor-baritone voice. He sounds innocent, open-hearted,"
            " polite, and genuinely bewildered by the cruelty of the world while clinging"
            " faithfully to his teacher's philosophy."
        ),
    },
    "pangloss": {
        "display_name": "Doctor Pangloss",
        "gender": "MALE",
        "language_code": "en-GB",
        "prompt": (
            "An older, pedantic, unshakably cheerful 18th-century British academic"
            " philosopher in his sixties. He speaks in a resonant, slightly theatrical"
            " baritone with scholarly self-satisfaction and grand declarative cadence,"
            " treating every catastrophe as a triumph of sufficient reason."
        ),
    },
    "cunegonde": {
        "display_name": "Lady Cunegonde",
        "gender": "FEMALE",
        "language_code": "en-GB",
        "prompt": (
            "A spirited, poised young British noblewoman in her late teens with a clear,"
            " expressive soprano-alto voice. She speaks with vivid dramatic candour,"
            " aristocratic articulation, and a blend of romantic tenderness and resilient"
            " matter-of-factness as she recounts her extraordinary survival."
        ),
    },
    "old_woman": {
        "display_name": "The Old Woman",
        "gender": "FEMALE",
        "language_code": "en-GB",
        "prompt": (
            "A seasoned, world-weary, fiercely resilient elderly European woman in her"
            " seventies with a warm, textured, low contralto voice. She speaks with"
            " unsentimental wisdom, dry pragmatism, and quiet noble dignity born of surviving"
            " every imaginable misfortune."
        ),
    },
    "james_anabaptist": {
        "display_name": "James and Supporting Men",
        "gender": "MALE",
        "language_code": "en-GB",
        "prompt": (
            "A grounded, resonant, mature British-European baritone in his forties with"
            " clear diction, strong presence, and natural dramatic versatility for supporting"
            " roles including soldiers, magistrates, and the kind Anabaptist merchant."
        ),
    },
}


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
    api_key = get_api_key()
    manifest = json.loads(MANIFEST_PATH.read_text()) if MANIFEST_PATH.exists() else {}

    to_create = {k: v for k, v in CANDIDE_VOICES_SPEC.items() if k not in manifest}
    if not to_create:
        print("All Candide voices already created.")
        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(create_one_voice, k, v, api_key): k for k, v in to_create.items()}
        for f in concurrent.futures.as_completed(futs):
            k, info = f.result()
            manifest[k] = info
            MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))

    print(f"Saved {len(manifest)} total voices in {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
