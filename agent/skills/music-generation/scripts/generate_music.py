#!/usr/bin/env python3
"""Generates a 30-second instrumental ambient score using lyria-3-clip-preview."""

import argparse
from pathlib import Path
from google import genai
from google.genai import types


def main():
  parser = argparse.ArgumentParser(description="Generate ambient music via lyria-3-clip-preview")
  parser.add_argument("--prompt", required=True, help="Instrumental music prompt")
  parser.add_argument("--out", default="./workspace/audio/ambient.mp3", help="Output MP3 path")
  args = parser.parse_args()

  out_path = Path(args.out)
  out_path.parent.mkdir(parents=True, exist_ok=True)

  client = genai.Client()
  prompt = args.prompt
  if "instrumental" not in prompt.lower():
    prompt = f"{prompt}, instrumental only, no vocals"

  response = client.models.generate_content(
      model="lyria-3-clip-preview",
      contents=prompt,
      config=types.GenerateContentConfig(
          response_modalities=["AUDIO"],
      ),
  )

  for part in response.candidates[0].content.parts:
    if part.inline_data and part.inline_data.data:
      out_path.write_bytes(part.inline_data.data)
      print(f"[Lyria] Saved ambient score to {out_path} ({out_path.stat().st_size} bytes)")
      return

  raise RuntimeError("No audio data returned by lyria-3-clip-preview")


if __name__ == "__main__":
  main()
