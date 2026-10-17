---
name: tts-generation
description: Synthesize dramatized multi-voice narration for each page of the storybook using `gemini-3.1-flash-tts-preview`.
---

# Expressive Multi-Speaker Storybook TTS Skill

Use this skill to synthesize dramatized narration for every page in `./workspace/data/storybook.json` using `gemini-3.1-flash-tts-preview`.

## Usage

```bash
python3 /.agents/skills/tts-generation/scripts/generate_page_audio.py \
  --storybook ./workspace/data/storybook.json \
  --out-dir ./workspace/audio
```

## How It Works

- For each page in `storybook.json`, the script inspects `dialogueLines[]` (or falls back to `narrativeText` with `"Charon"`).
- When a page has 1 speaker, it uses `VoiceConfig` with the speaker's assigned Gemini TTS voice (`Charon`, `Kore`, `Puck`, `Fenrir`, `Aoede`, `Zephyr`, `Leda`, `Orus`).
- When a page has 2 speakers, it uses native `MultiSpeakerVoiceConfig`.
- When a page has 3+ speakers, it synthesizes each line with its character's voice and stitches them seamlessly with a natural 280ms theatrical pause via `pydub`, outputting `./workspace/audio/page_1.mp3`, `./workspace/audio/page_2.mp3`, etc.
