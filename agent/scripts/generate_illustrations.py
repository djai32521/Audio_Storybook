#!/usr/bin/env python3
"""Generate Character & Style Reference Sheets and Scene Illustrations for all 5 books
using Nano Banana 2 Lite (gemini-3.1-flash-lite-image) via the Gemini Interactions API.

Workflow per book:
1. Generate <book_id>_char_sheet.jpg (16:9) from char_sheet_prompt.
2. Pass <book_id>_char_sheet.jpg as an input reference image to generate
   <book_id>_scene_1.jpg, <book_id>_scene_2.jpg, and <book_id>_scene_3.jpg (16:9),
   ensuring consistent character appearances and consistent minimal style.
"""

import argparse
import base64
import concurrent.futures
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from books_spec import BOOKS_SPEC

ROOT = Path(__file__).resolve().parent.parent
ILLUST_DIR = ROOT / "illustrations"


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


def call_nano_banana_lite(
    prompt: str,
    output_path: Path,
    api_key: str,
    ref_image_path: Path | None = None,
    aspect_ratio: str = "16:9",
    retries: int = 3,
) -> Path:
    url = "https://generativelanguage.googleapis.com/v1beta/interactions"
    inputs = []
    if ref_image_path and ref_image_path.exists():
        b64_ref = base64.b64encode(ref_image_path.read_bytes()).decode("utf-8")
        inputs.append({
            "type": "image",
            "data": b64_ref,
            "mime_type": "image/jpeg",
        })
    inputs.append({"type": "text", "text": prompt})

    payload = {
        "model": "gemini-3.1-flash-lite-image",
        "input": inputs,
        "response_format": {
            "type": "image",
            "aspect_ratio": aspect_ratio,
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
                    if block.get("type") == "image" and block.get("data"):
                        raw = base64.b64decode(block["data"])
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        output_path.write_bytes(raw)
                        return output_path
            raise RuntimeError(f"No image block in response: {json.dumps(data)[:300]}")
        except Exception as e:
            if attempt == retries:
                raise
            print(f"[RETRY {attempt}/{retries}] {output_path.name}: {e}")
            time.sleep(2 * attempt)
    raise RuntimeError(f"Failed to generate {output_path}")


def generate_book_illustrations(book: dict, api_key: str, force: bool = False):
    book_id = book["id"]
    char_sheet_path = ILLUST_DIR / f"{book_id}_char_sheet.jpg"

    if force or not char_sheet_path.exists():
        print(f"[CHAR SHEET] Generating {char_sheet_path.name}...")
        call_nano_banana_lite(
            prompt=book["char_sheet_prompt"],
            output_path=char_sheet_path,
            api_key=api_key,
            ref_image_path=None,
            aspect_ratio="16:9",
        )
        print(f"[OK] {char_sheet_path.name} ({char_sheet_path.stat().st_size} bytes)")

    for idx, scene in enumerate(book["scenes"], start=1):
        scene_path = ILLUST_DIR / f"{book_id}_scene_{idx}.jpg"
        if force or not scene_path.exists():
            print(f"[SCENE {idx}] Generating {scene_path.name} (referencing {char_sheet_path.name})...")
            full_prompt = (
                scene["prompt"]
                + " Flat 2D illustration directly on uniform archival paper filling"
                " the entire 16:9 canvas edge-to-edge, no borders, no frames, no"
                " tabletop surface, no text."
            )
            call_nano_banana_lite(
                prompt=full_prompt,
                output_path=scene_path,
                api_key=api_key,
                ref_image_path=char_sheet_path,
                aspect_ratio="16:9",
            )
            print(f"[OK] {scene_path.name} ({scene_path.stat().st_size} bytes)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", help="Optional book_id filter")
    parser.add_argument("--scene", type=int, help="Optional 1-based scene index to regenerate")
    parser.add_argument("--char-sheet-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    ILLUST_DIR.mkdir(parents=True, exist_ok=True)
    api_key = get_api_key()

    books = [b for b in BOOKS_SPEC if not args.book or b["id"] == args.book]
    if args.scene:
        for b in books:
            book_id = b["id"]
            char_sheet_path = ILLUST_DIR / f"{book_id}_char_sheet.jpg"
            scene = b["scenes"][args.scene - 1]
            scene_path = ILLUST_DIR / f"{book_id}_scene_{args.scene}.jpg"
            call_nano_banana_lite(
                prompt=scene["prompt"],
                output_path=scene_path,
                api_key=api_key,
                ref_image_path=char_sheet_path,
                aspect_ratio="16:9",
            )
            print(f"[OK] Regenerated {scene_path.name}")
        return

    if args.char_sheet_only:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            futs = [
                ex.submit(
                    call_nano_banana_lite,
                    b["char_sheet_prompt"],
                    ILLUST_DIR / f"{b['id']}_char_sheet.jpg",
                    api_key,
                    None,
                    "16:9",
                )
                for b in books
                if args.force or not (ILLUST_DIR / f"{b['id']}_char_sheet.jpg").exists()
            ]
            for f in concurrent.futures.as_completed(futs):
                p = f.result()
                print(f"[OK] {p.name}")
        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        futs = [ex.submit(generate_book_illustrations, b, api_key, args.force) for b in books]
        for f in concurrent.futures.as_completed(futs):
            f.result()


if __name__ == "__main__":
    main()
