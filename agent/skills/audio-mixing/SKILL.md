---
name: audio-mixing
description: Mix the dramatized page narrations with the ambient musical score into a mastered full-storybook audiobook (`full_storybook.mp3`) using `pydub`.
---

# Mastered Audiobook Mixing Skill

Use this skill to combine `./workspace/audio/page_*.mp3` and `./workspace/audio/ambient.mp3` into a theatrical full-length audiobook (`./workspace/audio/full_storybook.mp3`) with gentle music intro, ducked background score (`-16dB` under speech), inter-page musical swells, and a warm fade-out.

## Usage

```bash
python3 /.agents/skills/audio-mixing/scripts/mix_storybook_audio.py \
  --storybook ./workspace/data/storybook.json \
  --audio-dir ./workspace/audio
```
