---
name: character-sheet-illustrator
description: Generates the 16:9 Character & Style Reference Sheet (_char_sheet.jpg) and reference-conditioned Scene Plates (_scene_1..3.jpg) and 3D Pop-Up Cutouts (_bg.jpg, _cutouts.jpg) using gemini-3.1-flash-lite-image and gemini-api-cli.
---

# Reference-Conditioned Fine-Press Illustration & Pop-Up Plates

Follow the exact visual pipeline in `scripts/generate_illustrations.py` and `scripts/generate_popup_assets.py`:

## Step 1: 16:9 Character & Style Reference Sheet (`<book_id>_char_sheet.jpg`)
Generate `<book_id>_char_sheet.jpg` first on warm cream archival paper (`#F6F2EA`) using delicate pen-and-ink linework and muted period watercolour wash:

```bash
gemini-api interactions create \
  --model gemini-3.1-flash-lite-image \
  --input-text "$(jq -r '.char_sheet_prompt' book_spec.json)" \
  --response-format '{"type":"image","aspect_ratio":"16:9"}' \
  --output illustrations/${BOOK_ID}_char_sheet.jpg
```

## Step 2: Reference-Conditioned Scene Plates (`<book_id>_scene_1..3.jpg`)
Pass `illustrations/${BOOK_ID}_char_sheet.jpg` as the first input block (`type: "image"`) on every scene plate call so character faces, silhouettes, and linework remain 100% consistent across all plates:

```bash
python3 scripts/generate_illustrations.py --book "${BOOK_ID}"
```

## Step 3: Multi-Plane Paper Pop-Up Stage (`_bg.jpg` + `_cutouts.jpg`)
When generating 3D multi-plane pop-up spreads via `scripts/generate_popup_assets.py`:
- `_bg.jpg`: Full-bleed 16:9 distant architectural/landscape backdrop with a bare, uncluttered foreground stage floor.
- `_cutouts.jpg`: 3 freestanding full-length subjects isolated in 3 columns (`left` ~22%, `center` ~50%, `right` ~78%) on pure `#FFFFFF` background, segmented into die-cut cardstock standees by `extract_three_diecut_standees` in `scripts/render_audiobook_video.py`.
