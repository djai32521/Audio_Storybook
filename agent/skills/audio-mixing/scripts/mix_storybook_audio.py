#!/usr/bin/env python3
"""Mixes page narrations and ambient music into a full dramatized audiobook and updates storybook.json."""

import argparse
import json
from pathlib import Path
from pydub import AudioSegment


def loop_to_length(track: AudioSegment, target_ms: int) -> AudioSegment:
  if len(track) <= 0:
    return AudioSegment.silent(duration=target_ms)
  out = track
  while len(out) < target_ms + 2000:
    out = out.append(track, crossfade=min(1500, len(track) // 4))
  return out[:target_ms]


def main():
  parser = argparse.ArgumentParser(description="Mix page narrations and ambient score")
  parser.add_argument("--storybook", required=True, help="Path to storybook.json")
  parser.add_argument("--audio-dir", default="./workspace/audio", help="Audio directory")
  args = parser.parse_args()

  storybook_path = Path(args.storybook)
  audio_dir = Path(args.audio_dir)
  data = json.loads(storybook_path.read_text(encoding="utf-8"))

  ambient_path = audio_dir / "ambient.mp3"
  ambient = None
  if ambient_path.exists() and ambient_path.stat().st_size > 0:
    try:
      ambient = AudioSegment.from_file(str(ambient_path))
    except Exception as exc:
      print(f"[Mix] Warning loading ambient.mp3: {exc}")

  master_voice = AudioSegment.silent(duration=1800)  # 1.8s musical intro
  inter_page_pause = AudioSegment.silent(duration=1400)

  for page in data.get("pages", []):
    pnum = page.get("pageNumber", 1)
    page_mp3 = audio_dir / f"page_{pnum}.mp3"
    if not page_mp3.exists():
      continue
    seg = AudioSegment.from_file(str(page_mp3))
    page["durationSeconds"] = round(len(seg) / 1000.0, 1)
    master_voice += seg + inter_page_pause

  master_voice += AudioSegment.silent(duration=2000)  # 2.0s musical outro

  if ambient is not None:
    bed = loop_to_length(ambient - 16, len(master_voice))
    bed = bed.fade_in(1200).fade_out(1800)
    final_mix = bed.overlay(master_voice)
  else:
    final_mix = master_voice

  full_out = audio_dir / "full_storybook.mp3"
  final_mix.export(str(full_out), format="mp3", bitrate="192k")
  data["fullAudiobookUrl"] = "audio/full_storybook.mp3"
  data["totalDurationSeconds"] = round(len(final_mix) / 1000.0, 1)
  storybook_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
  print(f"[Mix] Exported full_storybook.mp3 ({data['totalDurationSeconds']}s)")


if __name__ == "__main__":
  main()
