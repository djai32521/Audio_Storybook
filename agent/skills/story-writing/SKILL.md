---
name: story-writing
description: Research classic literature (Project Gutenberg) or original prompts and author a structured multi-page illustrated storybook & dramatized multi-voice audiobook script using the Gemini API CLI (`gemini-api generate`).
---

# Story Writing & Classic Literature Adaptation Skill

Use this skill to author `./workspace/data/storybook.json` — the master blueprint for the illustrated storybook and multi-voice dramatized audiobook.

## 1. Using the Gemini API CLI (`gemini-api`) for Story Research & Adaptation

Ensure `$HOME/.local/bin` is on your `PATH`:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

You can invoke `gemini-api generate` with `gemini-3.1-pro-preview` or `gemini-3.8-flash` to draft character analyses, literary adaptations, or structured JSON scripts:

```bash
gemini-api generate "Adapt Chapter 1 of Alice's Adventures in Wonderland into a 4-page illustrated storybook script with character dialogue for The Storyteller (Charon), Alice (Kore), and The White Rabbit (Puck)." \
  --model gemini-3.8-flash
```

If the user references a classic public-domain book, you can also query the Project Gutenberg API (`https://gutendex.com/books?search=<query>`) via `curl` or Python to ground your adaptation in authentic prose and character details.

## 2. Character Voice Casting (`gemini-3.1-flash-tts-preview` Voices)

Assign every character (plus `"The Storyteller"` narrator) a distinct prebuilt Gemini TTS voice:

| Voice Name | Vocal Quality & Ideal Casting |
| :--- | :--- |
| `Charon` | Warm, resonant, authoritative classic storyteller / wise elder |
| `Kore` | Bright, expressive, curious heroine / young protagonist |
| `Puck` | Lively, nimble, eccentric or whimsical character / trickster |
| `Fenrir` | Deep, dramatic, gravelly antagonist / sea captain / monster |
| `Aoede` | Lyrical, melodic, gentle narrator / fairy queen / poet |
| `Zephyr` | Airy, youthful, energetic adventurer |
| `Leda` | Refined, poised, aristocratic or classical figure |
| `Orus` | Steady, heroic, earnest companion |

## 3. Visual Consistency Rule

Choose a single unmistakable artistic medium for `visualStyle` (for example: *"Golden-Age Arthur Rackham ink and watercolor book plate on warm deckle-edge parchment"* or *"Studio Ghibli hand-painted gouache background with warm lantern light"*).

Every single `illustrationPrompt` in `pages[]` and `coverImagePrompt` **must** begin with the `visualStyle` prefix and explicitly repeat the physical appearance of any character in the scene (e.g., *"young Alice in a sky-blue Victorian pinafore with a black ribbon"*), because each `gemini-api image` call is stateless.

## 4. Output Location

Write the completed JSON to `./workspace/data/storybook.json` and validate it with:
```bash
python3 -m json.tool ./workspace/data/storybook.json > /dev/null && echo "storybook.json is valid JSON"
```
