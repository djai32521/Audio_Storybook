---
name: lyria-chamber-score
description: Generates bespoke period-authentic acoustic chamber scores using Google Lyria 3.5 (lyria-3.5 via POST /v1beta/interactions) and mixes beneath the multi-voice reading with spectral unmasking and sidechain ducking.
---

# Bespoke Instrumental Chamber Score & Audiobook Mix (`generate_and_mix_music.py`)

Follow `scripts/generate_and_mix_music.py` to score and mix the completed audiobook chapter:

## 1. Period-Authentic Chamber Score Generation (`lyria-3.5`)
Request a purely instrumental acoustic chamber recording tailored to the book's period and key signature via `POST /v1beta/interactions` (or `gemini-api interactions create --model lyria-3.5`):
- **Regency Social Satire (*Pride and Prejudice*)**: *"Warm Regency chamber string quartet and pianoforte in D major — resonant cello and contrabass arco and pizzicato foundation, warm viola and mellow violin, rich fortepiano lower-midrange chords, close ribbon microphones in a warm wooden concert hall salon, lush 80 to 400 Hz acoustic body. Purely instrumental, no vocals, no percussion."*
- **Victorian Mystery / Sci-Fi / Fantasy / Fairytale**: Specify warm low strings (cello, double bass, viola), woodwinds (bassoon, low clarinet), or harp/lute/fortepiano with rich `80–400 Hz` body and zero vocals or percussion.

## 2. Spectral Unmasking & Sidechain Ducking Mix
Mix the chamber score underneath the mastered narration track:
- Scan `18s..50s` of the generated Lyria track (`select_warm_ensemble_section`) so the score enters with full low-string warmth.
- Carve a vocal presence pocket (`250 Hz – 3.8 kHz`) during active speech turns while keeping continuous chapter-level bed warmth across page turns (fading in during the `2.6s` Title Card and fading out over the final `2.4s` chapter outro).
