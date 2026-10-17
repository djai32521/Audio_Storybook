---
name: music-generation
description: Generate a custom 30-second instrumental ambient score for the storybook using `lyria-3-clip-preview`.
---

# Ambient Storybook Score Generation Skill (`lyria-3-clip-preview`)

Use this skill to compose an original 30-second instrumental musical score (`./workspace/audio/ambient.mp3`) matched to the storybook's mood and literary era.

## Usage

```bash
python3 /.agents/skills/music-generation/scripts/generate_music.py \
  --prompt "Gentle Victorian chamber harp, celesta, and warm pastoral strings, instrumental only, 80 BPM" \
  --out ./workspace/audio/ambient.mp3
```
