---
name: illustration-generation
description: Generate the storybook cover art and page illustrations using the official Gemini API CLI (`gemini-api image`) and `gemini-3.1-flash-lite-image`.
---

# Illustration Generation Skill (`gemini-api image`)

Use this skill to generate the front cover (`./workspace/images/cover.png`) and every page spread illustration (`./workspace/images/page_1.png`, `./workspace/images/page_2.png`, ...) using the **Gemini API CLI** (`https://github.com/google-gemini/gemini-api-cli`) and `gemini-3.1-flash-lite-image` (Nano Banana 2).

## Direct CLI Usage

```bash
export PATH="$HOME/.local/bin:$PATH"

# 1. Generate the book cover (3:4 vertical portrait)
gemini-api image "<coverImagePrompt>" \
  --model gemini-3.1-flash-lite-image \
  --aspect-ratio 3:4 \
  --out ./workspace/images/cover.png

# 2. Generate each storybook page illustration (4:3 classic book plate)
gemini-api image "<page illustrationPrompt>" \
  --model gemini-3.1-flash-lite-image \
  --aspect-ratio 4:3 \
  --out ./workspace/images/page_1.png
```

## Batch Parallel Generation Script

To generate the cover and all page illustrations concurrently from `./workspace/data/storybook.json` using `gemini-api image`:

```bash
python3 /.agents/skills/illustration-generation/scripts/generate_illustrations.py \
  --storybook ./workspace/data/storybook.json \
  --out-dir ./workspace/images
```
