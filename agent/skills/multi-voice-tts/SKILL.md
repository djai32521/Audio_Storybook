---
name: multi-voice-tts
description: Creates character voices and synthesizes turn-by-turn 24kHz WAV narration using gemini-3.8-flash-tts / gemini-3.1-flash-tts-preview, applies zero-phase voice_mastering.py leveling, and outputs audio/timeline_manifest.json.
---

# Multi-Voice Narration & Studio Mastering (`create_voices.py` + `generate_audiobook_tts.py`)

Follow the exact multi-voice synthesis and mastering pipeline in `scripts/create_voices.py`, `scripts/generate_audiobook_tts.py`, and `scripts/voice_mastering.py`:

## 1. Voice Casting (`voices/voices_manifest.json`)
Assign distinct studio voices to the narrator and each character:
- `Kore` — Poised literary narrator (e.g., Jane Austen Regency Narrator, Wonderland Narrator)
- `Aoede` — Animated, expressive female character (e.g., Mrs. Bennet, Aunt Polly)
- `Charon` — Dry, deadpan baritone gentleman (e.g., Mr. Bennet, The Psychologist, Mark Twain Narrator)
- `Fenrir` — Warm, observant Victorian narrator (e.g., Dr. John Watson, Hillyer Narrator)
- `Orus` — Crisp, incisive intellectual lead (e.g., Sherlock Holmes, The Time Traveller)
- `Leda` — Young, curious storybook heroine (e.g., Alice)
- `Puck` — Brisk, lively character voice (e.g., The White Rabbit, Tom Sawyer)
- `Iapetus` — Skeptical, resonant debater (e.g., Filby)

## 2. Turn-by-Turn Synthesis with `speech_metadata` Style Annotations
Synthesize each turn at `24000` Hz mono WAV using `scripts/generate_audiobook_tts.py` (or `gemini-api interactions create`):
- Combine `persona_style` and turn-specific `style` into `annotations: [{"type": "speech_metadata", "style": full_style}]`.
- Trim excessive leading/trailing digital silence (> 80ms, preserving a 50ms natural breath pad) and apply a 15ms linear fade-in/fade-out.

## 3. Studio Voice Mastering (`scripts/voice_mastering.py`)
Run `warm_master_voice_turn(samples, sr=24000)`:
- 2nd-order Butterworth zero-phase high-pass filter at `60 Hz` (`scipy.signal.sosfiltfilt`) to remove sub-bass rumble.
- Active-speech RMS leveling (`target_rms = 3450 / 32768`, gain clamped to `[0.70, 1.35]`) with a linear true-peak ceiling at `-1.5 dBFS` (`0.84`).
- Assemble the chapter timeline with a `2.6s` Title Card hold (`TITLE_CARD_HOLD_SEC = 2.6`) and exact `start_sec` / `end_sec` timestamps per turn and per folio in `audio/timeline_manifest.json`.
