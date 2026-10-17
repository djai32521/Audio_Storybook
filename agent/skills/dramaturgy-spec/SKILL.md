---
name: dramaturgy-spec
description: Adapts a user fairytale, story prompt, or literary chapter into the exact classic-audiobooks BOOKS_SPEC & timeline_manifest.json schema with fine-press editorial palette tokens, anonymous character descriptions, 3 folios (FOLIO I.1..I.3), and multi-voice dialogue turns.
---

# Dramaturgy & Fine-Press Folio Specification (`books_spec.py`)

When the user commissions a storybook or audiobook, first structure the work into the exact `BOOKS_SPEC` / `timeline_manifest.json` schema used by `classic-audiobooks`:

## 1. Fine-Press Editorial Palette Tokens
Every book defines a light-themed archival paper palette modeled on Jane Austen's *Pride and Prejudice* (`01_pride_and_prejudice`):
- `paper`: `"#F6F2EA"` (warm cream archival laid paper)
- `card`: `"#EFE9DC"` (matted illustration frame fill)
- `ink`: `"#1E1B18"` (primary active paragraph dark sepia/charcoal ink)
- `muted`: `"#7A7267"` (running headers, footers, and secondary metadata)
- `accent`: `"#4A6B53"` (Regency sage green, or period-specific accent for `PLATE I OF III`, speaker rubrics, and the 2px footer progress bar)
- `rule`: `"#D5CBB8"` (1px hairline border and spine rules)

## 2. Anonymous Character & Style Reference Sheet Prompt (`FORBIDDEN_WORDS` Rule)
To prevent image models from reproducing generic film, cartoon, or adaptation tropes:
- **NEVER** include proper character names, book titles, author names, or famous place names in `char_sheet_prompt` or `scenes[].prompt`.
- Describe characters purely by age, historical period attire, fabric texture, hair, posture, and three-quarter profile gaze direction (`LEFT` figure facing `RIGHT ->`, `RIGHT` figure facing `LEFT <-`) on `#F6F2EA` archival paper.

## 3. Three-Folio Right-Page Structure (`FOLIO I.1`, `FOLIO I.2`, `FOLIO I.3`)
- Divide the chapter's turns across **3 Folios** (`folio_idx: 0, 1, 2`) so each right-hand page sits comfortably in `EB Garamond` (18px–27px) without scrolling or clipping.
- Separate narrator attribution clauses (e.g., `said his lady to him one day,`) into their own `is_dialogue: false` narrator turns between spoken character lines (`is_dialogue: true`) so the voice switches cleanly between the narrator (`Kore` / `Fenrir`) and each character (`Aoede`, `Charon`, `Orus`, `Leda`, `Puck`, `Iapetus`).
