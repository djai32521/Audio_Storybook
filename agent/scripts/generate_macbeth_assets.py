#!/usr/bin/env python3
"""Generate and verify all anonymous, text-derived illustrations and 2K high-resolution
Victorian Toy Theatre cutouts for 07_macbeth:
  - illustrations/07_macbeth_char_sheet.jpg
  - illustrations/popup/07_macbeth_spread_1_bg.jpg
  - illustrations/popup/07_macbeth_standee_s1_left.png            (2K 1792x2400 solo lossless PNG)
  - illustrations/popup/07_macbeth_standee_s1_center.png          (2K 1792x2400 solo lossless PNG)
  - illustrations/popup/07_macbeth_standee_s1_right.png           (2K 1792x2400 solo lossless PNG)
  - illustrations/popup/07_macbeth_spread_1_cutouts.png           (2K 2752x1536 lossless composite)
  - illustrations/popup/07_macbeth_spread_1_cutouts.jpg           (1376x768 normalized 3-col sheet)
  - illustrations/popup/07_macbeth_spread_2_bg.jpg
  - illustrations/popup/07_macbeth_standee_s2_left.png            (2K 1792x2400 solo lossless PNG)
  - illustrations/popup/07_macbeth_standee_s2_center.png          (2K 1792x2400 solo lossless PNG)
  - illustrations/popup/07_macbeth_standee_s2_right.png           (2K 1792x2400 solo lossless PNG)
  - illustrations/popup/07_macbeth_standee_s2_ross.png            (2K 1792x2400 solo lossless PNG)
  - illustrations/popup/07_macbeth_spread_2_cutouts.png           (2K 2752x1536 lossless composite)
  - illustrations/popup/07_macbeth_spread_2_cutouts.jpg           (1376x768 normalized 3-col sheet)
  - illustrations/popup/07_macbeth_spread_3_bg.jpg
  - illustrations/popup/07_macbeth_standee_s3_lady.png            (2K 1792x2400 solo lossless PNG)
  - illustrations/popup/07_macbeth_spread_4_bg.jpg
  - illustrations/popup/07_macbeth_standee_s4_dagger.png          (2K 1792x2400 solo lossless PNG)
  - illustrations/popup/07_macbeth_standee_s4_macbeth_daggers.png (2K 1792x2400 solo lossless PNG)

Enforces:
1. ZERO character names, play titles, place names, or author/printer names in any prompt.
2. Authentic 19th-century Victorian paper toy theatre copperplate etching and moody
   watercolour wash aesthetic at native 2K resolution.
3. Explicit three-quarter profile stage-blocking and gaze directions for every character:
   - Scene 1: Left sister gazes RIGHT (->), Center sister gazes LEFT (<-) toward Left sister,
     Right sister gazes LEFT (<-) toward Center & Left sisters.
   - Scene 2a: Dark-haired commander (Left) gazes RIGHT (->) toward the three sisters on
     Stage Right; Auburn-bearded general (Center) gazes RIGHT (->) toward the three sisters
     on Stage Right; Three sisters cluster (Right) all gaze and point LEFT (<-) toward the
     two men on Stage Left.
   - Scene 2b: Royal herald thane enters on Stage Right gazing LEFT (<-) toward the two
     commanders on Stage Left.
   - Scene 3: Castle noblewoman with the letter stands on Stage Right gazing LEFT (<-) toward
     her husband entering from Stage Left.
   - Scene 4a: Floating spectral dagger hovers at Stage Center with its hilt pointing
     downward-LEFT (<-) toward the commander on Stage Left and its blade pointing upward-RIGHT (->).
   - Scene 4b: Commander returning with two crimson-stained daggers on Stage Right gazes
     LEFT (<-) toward his wife on Stage Left.
"""

import argparse
import base64
import io
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage

from generate_illustrations import get_api_key
from generate_popup_assets import (
    BG_FULLBLEED_RULES,
    CUTOUT_LAYOUT_RULES,
    normalize_cutout_sheet_columns,
)

ROOT = Path(__file__).resolve().parent.parent
ILLUST_DIR = ROOT / "illustrations"
POPUP_DIR = ILLUST_DIR / "popup"

TARGET_W = 1376
TARGET_H = 768
TARGET_2K_W = 2752
TARGET_2K_H = 1536

FORBIDDEN_WORDS = (
    "macbeth",
    "lady macbeth",
    "banquo",
    "ross",
    "duncan",
    "shakespeare",
    "weird sisters",
    "three witches",
    "glamis",
    "cawdor",
    "forres",
    "inverness",
    "pollock",
)

STYLE_HEADER = (
    "19th-century Victorian paper toy theatre illustration in ultra-crisp hand-tinted "
    "copperplate etching and rich moody watercolour wash — fine engraved cross-hatching, "
    "razor-sharp black ink linework, dramatic chiaroscuro candlelight and storm-cloud "
    "palette of slate-blue, peat-umber, heather-ochre, tarn-green, and deep crimson. "
    "Strictly NO text, NO captions, NO words, NO letters, NO numbers, and NO signatures anywhere."
)

# Strictly anonymous, text-derived physical and sartorial descriptions
DESC_THREE_SISTERS = (
    "three gaunt, wind-weathered elderly crone sisters — so wither'd and so wild in their "
    "attire — standing close together in tattered peat-brown, charcoal, and moss-green "
    "woollen shawls and draped cloth hoods over their heads, with wild windblown grey hair "
    "and bony pointing hands with choppy fingers upon skinny lips (eerie, ancient, grounded "
    "folklore look — strictly NO pointy hats, NO conical hats, NO broomsticks, NO cauldrons, "
    "and NO green skin)"
)

DESC_COMMANDER_DARK = (
    "a tall, broad-shouldered 11th-century Scottish highland commander in his late thirties "
    "with dark wavy shoulder-length hair, a short dark beard, and haunted piercing grey eyes, "
    "wearing bronze-studded dark brown leather brigandine armor over a deep crimson-and-charcoal "
    "tartan plaid cloak pinned at the shoulder with a circular bronze brooch, a broadsword at "
    "his belt, and dark leather highland boots (bareheaded, no helmet)"
)

DESC_GENERAL_AUBURN = (
    "a steadfast 11th-century Scottish highland general in his thirties with auburn-brown "
    "hair and a neat full auburn beard, wearing a finely linked steel chainmail hauberk under "
    "a forest-green and ochre tartan plaid cloak pinned at the shoulder with a circular silver "
    "brooch, carrying a round bronze-bossed leather targe shield, with tall leather highland "
    "boots (bareheaded, no helmet)"
)

CHAR_SHEET_PROMPT = (
    f"{STYLE_HEADER}\n\n"
    "Character reference sheet on a clean warm cream paper background (#F7F3EA) with "
    "generous open negative space and strictly ZERO text, ZERO labels, and ZERO borders. "
    "Show three distinct full-body character groups standing side by side from head to toe:\n"
    f"- LEFT: {DESC_THREE_SISTERS}.\n"
    f"- CENTER: {DESC_COMMANDER_DARK}.\n"
    f"- RIGHT: {DESC_GENERAL_AUBURN}.\n"
    "Every figure must be complete from head to boots with generous cream margin above "
    "the heads and below the feet. Strictly NO text, NO labels, NO borders."
)

SPREAD_1_BG_PROMPT = (
    f"{STYLE_HEADER}\n\n"
    "Full-bleed edge-to-edge 16:9 painted backdrop of a wild, stormy Scottish moorland heath "
    "under brooding slate-indigo and peat-umber storm clouds with a distant forked lightning "
    "flash high on the far horizon. Framed ONLY on the far left edge (outermost 10%) and far "
    "right edge (outermost 10%) by painted paper toy-theatre crag-and-heather wing flats. "
    "Across the entire center (from x = 15% to x = 85%) is a completely open, bare, flat "
    "stone-and-moss foreground stage floor ready for paper standees — strictly NO characters, "
    "NO people, NO standing stones in the center, NO foreground props, and NO outer paper "
    "margins or borders.\n\n"
    f"{BG_FULLBLEED_RULES}"
)

SPREAD_2_BG_PROMPT = (
    f"{STYLE_HEADER}\n\n"
    "Full-bleed 100% edge-to-edge 16:9 painted stage backdrop of a misty Scottish highland "
    "heath with ancient weathered Neolithic standing stones set far back in the distant "
    "background against brooding amber-ochre and slate-blue storm clouds on the horizon. "
    "Framed ONLY on the far left edge (outermost 10%) and far right edge (outermost 10%) by "
    "tall painted paper rock-outcrop wing flats that bleed directly off the top, bottom, "
    "left, and right edges of the canvas. Across the entire center (from x = 15% to x = 85%) "
    "is a completely open, bare, flat turf-and-stone foreground stage floor. CRITICAL: The "
    "painted artwork must bleed 100% to every pixel of all four edges of the image — strictly "
    "ZERO white or cream outer border, ZERO black frame line, ZERO paper margin around the "
    "outside of the image!\n\n"
    f"{BG_FULLBLEED_RULES}"
)

SPREAD_3_BG_PROMPT = (
    f"{STYLE_HEADER}\n\n"
    "Match the exact 19th-century Victorian paper toy theatre copperplate etching linework, "
    "engraved cross-hatching, and rich moody watercolour wash style of the attached reference "
    "backdrop, but depict a vaulted 11th-century Scottish stone castle great hall interior:\n"
    "Full-bleed 100% edge-to-edge 16:9 painted stage backdrop of a grand, vaulted 11th-century "
    "Scottish highland stone castle great hall with massive rough-hewn granite arches, ancient "
    "woven Celtic tapestries hanging high on the receding side walls, and flickering iron "
    "wall-sconce torches casting warm amber chiaroscuro light against deep slate-indigo stone "
    "shadows. Framed ONLY on the far left edge (outermost 10%) and far right edge (outermost 10%) "
    "by painted paper stone-pillar wing flats that bleed directly off the top, bottom, left, and "
    "right edges of the canvas. Across the entire center (from x = 15% to x = 85%) is a completely "
    "bare, empty, flat castle flagstone foreground stage floor ready for paper standees — strictly "
    "ZERO characters, ZERO people, ZERO furniture in the center, and ZERO outer borders or margins!\n\n"
    f"{BG_FULLBLEED_RULES}"
)

SPREAD_4_BG_PROMPT = (
    f"{STYLE_HEADER}\n\n"
    "Match the exact 19th-century Victorian paper toy theatre copperplate etching linework, "
    "engraved cross-hatching, and rich moody watercolour wash style of the attached reference "
    "backdrop, but depict a dark 11th-century Scottish castle midnight courtyard and chamber stair:\n"
    "Full-bleed 100% edge-to-edge 16:9 painted stage backdrop of a dark, foreboding 11th-century "
    "Scottish stone castle interior courtyard at midnight. On the far left is a high gothic stone "
    "archway admitting cold slate-blue moonlight; on the far right is a shadowy stone archway "
    "staircase leading up to a heavy iron-studded oak chamber door beside a single dying flickering "
    "wall-sconce torch casting dim amber highlights against deep midnight-indigo shadows. Across "
    "the entire center (from x = 15% to x = 85%) is a completely bare, open, flat castle flagstone "
    "foreground stage floor ready for paper standees — strictly ZERO characters, ZERO people, "
    "ZERO foreground objects in the center, and ZERO outer borders or margins!\n\n"
    f"{BG_FULLBLEED_RULES}"
)

SOLO_STANDEE_RULES = (
    "CRITICAL PAPER STANDEE CUTOUT RULES:\n"
    "1. Draw ONE single freestanding full-length paper toy-theatre standee figure centered "
    "on a 100% PURE SOLID WHITE (#FFFFFF) background with generous pure white margin (at least "
    "10% white space) above the head, below the base, and on both left and right sides.\n"
    "2. The figure stands on a small, flat, self-contained stone-and-heather paper standee base. "
    "Strictly NO vertical support wires, NO sticks, NO rods, NO cast drop shadows on the white "
    "background, NO background scenery, and NO outer frame or border.\n"
    "3. Render ultra-crisp, museum-grade copperplate engraving cross-hatching and fine black ink "
    "linework on the face, eyes, hands, drapery folds, and armor details."
)

# --- Scene 1 Solo 2K Standee Prompts (Act I, Scene 1: Three Sisters in Coven Conversation) ---
STANDEE_S1_LEFT_PROMPT = (
    f"{STYLE_HEADER}\n\n"
    "Match the copperplate etching style and weathered woollen shawl texture of the attached "
    "reference image. Draw ONE single gaunt, wind-weathered elder crone sister standing full-length "
    "on a small flat flagstone-and-moss standee base on a PURE SOLID WHITE (#FFFFFF) background.\n"
    "MANDATORY STAGE DIRECTION & GAZE (FACING RIGHT ->): She stands on Stage Left and MUST be "
    "turned in a clear THREE-QUARTER PROFILE VIEW FACING AND GAZING RIGHTWARD (her nose, piercing "
    "sunken eyes, hooded head, and posture all directed toward the RIGHT side of the image, "
    "looking across at her sisters to the right). She wears a tattered peat-brown woollen hooded "
    "shawl over wild grey hair, leans her left hand on a gnarled twisted hawthorn staff, and "
    "raises her right bony index finger pointing UPWARD AND TO THE RIGHT. Strictly ONE woman, "
    "no pointy hat.\n\n"
    f"{SOLO_STANDEE_RULES}"
)

STANDEE_S1_CENTER_PROMPT = (
    f"{STYLE_HEADER}\n\n"
    "Match the copperplate etching style and weathered woollen shawl texture of the attached "
    "reference image. Draw ONE single gaunt, wind-weathered elder crone sister standing full-length "
    "in a slightly crouched posture behind a low mossy moorland hearth-stone with subtle wisps of "
    "mist on a compact flat standee base on a PURE SOLID WHITE (#FFFFFF) background.\n"
    "MANDATORY STAGE DIRECTION & GAZE (FACING LEFT <-): Her head, sharp nose, and eerie sunken "
    "eyes are turned in a clear THREE-QUARTER PROFILE VIEW FACING AND GAZING LEFTWARD (looking "
    "toward the LEFT side of the image to converse with her sister on Stage Left), with both "
    "gnarled bony hands raised and hovering over the mossy stone. She wears tattered moss-green "
    "and charcoal woollen rags and a draped cloth hood over wild windblown grey hair. Strictly "
    "ONE woman, no pointy hat.\n\n"
    f"{SOLO_STANDEE_RULES}"
)

STANDEE_S1_RIGHT_PROMPT = (
    f"{STYLE_HEADER}\n\n"
    "Match the copperplate etching style and weathered woollen shawl texture of the attached "
    "reference image. Draw ONE single gaunt, wind-weathered elder crone sister standing full-length "
    "on a small, organic, ink-outlined flat flagstone-and-heather standee base (hand-drawn rock "
    "slabs and heather tufts with crisp black ink outlines — strictly NO rectangular grey block "
    "or box under her feet!) on a PURE SOLID WHITE (#FFFFFF) background.\n"
    "MANDATORY STAGE DIRECTION & GAZE (FACING LEFT <-): She stands on Stage Right and MUST be "
    "turned in a clear THREE-QUARTER PROFILE VIEW FACING AND GAZING LEFTWARD (her hooded head, "
    "sharp nose, piercing sunken eyes, and shoulders all angled unmistakably toward the LEFT "
    "side of the image, looking across the stage at her sisters to the left). She wears a "
    "tattered dark slate-blue and charcoal woollen hooded shawl over windblown grey hair and "
    "raises BOTH gnarled open hands forward toward the LEFT in prophetic incantation (do NOT "
    "put her finger on her lips). Strictly ONE woman, two hands only, no pointy hat.\n\n"
    f"{SOLO_STANDEE_RULES}"
)

# --- Scene 2 Solo 2K Standee Prompts (Act I, Scene 3: Commander & General Confronting Sisters) ---
STANDEE_S2_LEFT_PROMPT = (
    f"{STYLE_HEADER}\n\n"
    "Match the character face, dark wavy hair, short dark beard, bronze-studded dark leather "
    "brigandine armor, and deep crimson-and-charcoal tartan plaid cloak of the attached reference "
    f"image ({DESC_COMMANDER_DARK}).\n"
    "MANDATORY STAGE DIRECTION & GAZE (THREE-QUARTER VIEW FACING RIGHT ->): Do NOT draw him "
    "facing straight forward at the camera! He stands on Stage Left confronting supernatural "
    "figures across the stage to his right, so his head, nose, haunted piercing grey eyes, "
    "bearded jaw, and armored torso MUST be turned in a clear, dramatic THREE-QUARTER PROFILE "
    "VIEW FACING AND GAZING RIGHTWARD (looking intently toward the RIGHT edge of the image). "
    "His left hand is raised open at chest height toward the right in startled wonder, and his "
    "right hand grips the hilt of his broadsword at his belt. Keep his crimson tartan cloak "
    "draped cleanly behind his back with zero stray sticks or lines near his boots.\n\n"
    f"{SOLO_STANDEE_RULES}"
)

STANDEE_S2_CENTER_PROMPT = (
    f"{STYLE_HEADER}\n\n"
    "Match the character face, auburn-brown hair, neat full auburn beard, steel chainmail "
    "hauberk, forest-green and ochre tartan plaid cloak with silver shoulder brooch, and round "
    f"bronze-bossed leather targe shield of the attached reference image ({DESC_GENERAL_AUBURN}).\n"
    "MANDATORY STAGE DIRECTION & GAZE (THREE-QUARTER VIEW FACING RIGHT ->): He stands on Stage "
    "Center-Left looking across the heath at the strange figures on Stage Right. His head, nose, "
    "watchful eyes, auburn beard, and chainmail-clad torso MUST be turned in a clear, unmistakable "
    "THREE-QUARTER PROFILE VIEW FACING AND GAZING RIGHTWARD (eyes and face pointed directly "
    "toward the RIGHT side of the image — strictly NOT looking to the left and NOT staring "
    "straight at the viewer!). His round bronze-bossed targe shield is strapped on his left arm, "
    "and his right hand is slightly raised toward the right in questioning astonishment.\n\n"
    f"{SOLO_STANDEE_RULES}"
)

STANDEE_S2_RIGHT_PROMPT = (
    f"{STYLE_HEADER}\n\n"
    "Faithfully render the exact three gaunt, wind-weathered elder crone sisters from the "
    "attached reference image standing tightly together side by side as ONE unified compact "
    "group on a single low hand-drawn flagstone-and-heather standee base on a PURE SOLID WHITE "
    "(#FFFFFF) background, preserving their exact poses, gazes, and two-handed anatomy from "
    "the reference image:\n"
    "- ALL THREE ELDERLY SISTERS face and gaze intently to the LEFT (<-) in three-quarter profile.\n"
    "- The sister on the right (in tattered peat-brown hooded shawl) points her left index "
    "finger to the LEFT (<-) while her other hand rests just below it.\n"
    "- The middle sister (in dark charcoal hooded shawl) and left sister (in moss-green hooded "
    "shawl) each press one bony index finger to their skinny lips while their other hand rests "
    "at their elbow.\n"
    "Keep their exact two-armed anatomy from the reference image with ultra-crisp 2K copperplate "
    "engraving linework and strictly NO extra arms, NO extra hands, and NO pointy hats.\n\n"
    f"{SOLO_STANDEE_RULES}"
)

# --- Scene 2b Solo 2K Standee Prompt (Act I, Scene 3: Royal Herald Thane Entering on Stage Right) ---
STANDEE_S2_ROSS_PROMPT = (
    f"{STYLE_HEADER}\n\n"
    "Match the exact 19th-century Victorian paper toy theatre copperplate etching linework weight, "
    "fine cross-hatching, rich watercolour wash palette, leftward three-quarter profile gaze, and "
    "flat ink-outlined stone-and-heather standee base of the attached reference image, but draw a "
    "distinct noble 11th-century Scottish highland king's messenger and thane in his forties:\n"
    "He has neatly trimmed dark-auburn hair and a neatly trimmed dark-auburn beard, wearing a "
    "polished bronze-and-leather breastplate over a deep royal-blue and gold tartan plaid cloak "
    "pinned at the shoulder with an ornate circular gold Celtic brooch, belted tunic, and tall "
    "leather highland boots on a small ink-outlined stone-and-heather base (bareheaded, no helmet, "
    "no shield).\n"
    "MANDATORY STAGE DIRECTION & GAZE (THREE-QUARTER VIEW FACING LEFT <-): He enters on Stage "
    "Right to greet two commanders on Stage Left, so his head, nose, eyes, bearded jaw, and "
    "breastplate-clad torso MUST be turned in a clear, unmistakable THREE-QUARTER PROFILE VIEW "
    "FACING AND GAZING LEFTWARD (looking directly toward the LEFT side of the image). He holds a "
    "rolled parchment royal decree with a hanging crimson wax seal in his extended right hand "
    "while gesturing leftward in solemn royal salutation.\n\n"
    f"{SOLO_STANDEE_RULES}"
)

# --- Scene 3 Solo 2K Standee Prompt (Act I, Scene 5: The Castle Lady with the Letter) ---
STANDEE_S3_LADY_PROMPT = (
    f"{STYLE_HEADER}\n\n"
    "Match the exact 19th-century Victorian paper toy theatre copperplate etching linework weight, "
    "fine engraved cross-hatching, moody watercolour wash palette, and leftward three-quarter "
    "profile orientation of the attached reference image, but draw ONE SINGLE WOMAN (strictly "
    "NO man and NO beard):\n"
    "A fierce, regal 11th-century Scottish noblewoman in her thirties with piercing dark eyes, "
    "sculpted high cheekbones, and long dark braided hair worn beneath a hammered-gold Celtic "
    "circlet. She wears a rich deep-emerald and dark-crimson wool-and-velvet medieval gown with "
    "long trailing sleeves and a knotted gold girdle at her waist, standing full-length on a "
    "small, flat, ink-outlined castle flagstone standee base on a PURE SOLID WHITE (#FFFFFF) "
    "background.\n"
    "MANDATORY STAGE DIRECTION & GAZE (THREE-QUARTER VIEW FACING LEFT <-): She stands on Stage "
    "Right and MUST be turned in a clear, dramatic THREE-QUARTER PROFILE VIEW FACING AND GAZING "
    "LEFTWARD (her face, nose, piercing dark eyes, and posture all directed toward the LEFT side "
    "of the image). She holds an open parchment letter with a hanging red wax seal in one hand "
    "and raises her other hand toward the LEFT in an intense, commanding gesture of dark resolve.\n\n"
    f"{SOLO_STANDEE_RULES}"
)

# --- Scene 4a Solo 2K Cutout Prompt (Act II, Scene 1: The Floating Spectral Dagger) ---
STANDEE_S4_DAGGER_PROMPT = (
    f"{STYLE_HEADER}\n\n"
    "Match the exact 19th-century Victorian paper toy theatre copperplate etching linework weight, "
    "fine engraved steel cross-hatching, and moody watercolour wash style of the attached reference "
    "image. Draw ONLY ONE single floating object centered in mid-air on a 100% PURE SOLID WHITE "
    "(#FFFFFF) background (strictly NO person, NO hand holding it, and NO standee base at the bottom):\n"
    "An ornate 11th-century Scottish highland dirk / dagger hovering diagonally in mid-air.\n"
    "MANDATORY ORIENTATION (HILT POINTING DOWNWARD-LEFT <-, BLADE POINTING UPWARD-RIGHT ->): "
    "Its carved dark bog-oak and bronze Celtic knotwork hilt and pommel MUST point DOWNWARD AND "
    "TO THE LEFT (toward the lower-left of the canvas, angled toward a hand on Stage Left), and "
    "its gleaming double-edged steel blade MUST point UPWARD AND TO THE RIGHT (toward the "
    "upper-right of the canvas), with several vivid crimson droplets clinging to the steel blade "
    "and falling from its tip. Surround the dagger closely with a compact, delicate wisp of pale "
    "golden-amber spectral mist rendered with fine copperplate stippling and soft amber watercolour "
    "wash, leaving generous pure solid white (#FFFFFF) margin on all four sides. Strictly NO base "
    "stand at the bottom, NO background scenery, NO people, and NO text."
)

# --- Scene 4b Solo 2K Standee Prompt (Act II, Scene 2: Commander Returning with Two Bloody Daggers) ---
STANDEE_S4_MACBETH_DAGGERS_PROMPT = (
    f"{STYLE_HEADER}\n\n"
    "Faithfully preserve the EXACT same character likeness, face, dark wavy shoulder-length hair, "
    "short dark beard, bronze-studded dark leather brigandine, and deep crimson-and-charcoal tartan "
    "plaid cloak of the attached reference image, rendered in the exact same 19th-century Victorian "
    "paper toy theatre copperplate etching and watercolour wash style on a PURE SOLID WHITE (#FFFFFF) "
    "background.\n"
    "MANDATORY STAGE DIRECTION & GAZE (THREE-QUARTER VIEW FACING LEFT <-): He stands on Stage Right "
    "on a small, flat, ink-outlined castle flagstone standee base and MUST be turned in a clear, "
    "dramatic THREE-QUARTER PROFILE VIEW FACING AND GAZING LEFTWARD (his head, nose, wide haunted "
    "eyes, and torso angled unmistakably toward the LEFT side of the image, matching the leftward "
    "orientation of the reference image).\n"
    "He is now pale and wide-eyed with horror and remorse, wearing an unfastened white linen "
    "night-shirt visible at his open collar and forearms beneath his loosened dark leather "
    "brigandine and crimson-and-charcoal tartan cloak. In his TWO trembling, crimson-stained hands "
    "he holds TWO crimson-stained 11th-century Scottish daggers (one blood-stained dagger gripped in "
    "his left hand, and a second blood-stained dagger gripped in his right hand) held out in front "
    "of him toward the LEFT as he stares leftward in terror at his crimson-stained hands. Strictly "
    "ONE man, two hands, two daggers (one in each hand), and NO broadsword.\n\n"
    f"{SOLO_STANDEE_RULES}"
)


def assert_no_forbidden_words(prompt: str, name: str) -> None:
    import re
    low = prompt.lower()
    for word in FORBIDDEN_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", low):
            raise ValueError(f"Forbidden term {word!r} found in prompt for {name}")


def call_gemini_image(
    prompt: str,
    output_path: Path,
    api_key: str,
    ref_image_path: Path | None = None,
    aspect_ratio: str = "16:9",
    model: str = "gemini-3.1-flash-lite-image",
    retries: int = 6,
) -> Path:
    """Call Gemini image generation (`gemini-3.1-flash-lite-image` at 2K `16:9` via
    `generateContent`, with fallback to `interactions`) and save a 1376x768 (16:9) JPEG.
    """
    assert_no_forbidden_words(prompt, output_path.name)

    parts = []
    if ref_image_path and ref_image_path.exists():
        im_ref = Image.open(ref_image_path).convert("RGB")
        buf = io.BytesIO()
        im_ref.save(buf, format="JPEG", quality=95)
        b64_ref = base64.b64encode(buf.getvalue()).decode("utf-8")
        parts.append({
            "inlineData": {
                "mimeType": "image/jpeg",
                "data": b64_ref,
            }
        })
    parts.append({"text": prompt})

    last_err = None
    for attempt in range(1, retries + 1):
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={api_key}"
        )
        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
                "imageConfig": {
                    "aspectRatio": aspect_ratio,
                    "imageSize": "2K",
                },
            },
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=150) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            for cand in data.get("candidates", []):
                for part in cand.get("content", {}).get("parts", []):
                    if "inlineData" in part and part["inlineData"].get("data"):
                        raw = base64.b64decode(part["inlineData"]["data"])
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        im = Image.open(io.BytesIO(raw)).convert("RGB")
                        if im.size != (TARGET_W, TARGET_H):
                            im = im.resize((TARGET_W, TARGET_H), Image.Resampling.LANCZOS)
                        im.save(output_path, format="JPEG", quality=95)
                        return output_path
            raise RuntimeError(f"No inlineData image in response: {json.dumps(data)[:300]}")
        except Exception as e:
            last_err = e
            print(f"[RETRY {attempt}/{retries}] {output_path.name} ({model}): {e}")
            time.sleep(2 * attempt)
    raise RuntimeError(f"Failed to generate {output_path}: {last_err}")


def call_gemini_image_2k(
    prompt: str,
    output_path: Path,
    api_key: str,
    ref_image: Image.Image | None = None,
    aspect_ratio: str = "3:4",
    image_size: str = "2K",
    model: str = "gemini-3.1-flash-lite-image",
    retries: int = 6,
) -> Path:
    """Call Gemini 2K image generation via generateContent (`1792x2400` for `3:4`,
    `2752x1536` for `16:9`) and save as a lossless PNG.
    """
    assert_no_forbidden_words(prompt, output_path.name)

    parts = []
    if ref_image is not None:
        buf = io.BytesIO()
        ref_image.convert("RGB").save(buf, format="JPEG", quality=95)
        b64_ref = base64.b64encode(buf.getvalue()).decode("utf-8")
        parts.append({
            "inlineData": {
                "mimeType": "image/jpeg",
                "data": b64_ref,
            }
        })
    parts.append({"text": prompt})

    last_err = None
    for attempt in range(1, retries + 1):
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={api_key}"
        )
        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
                "imageConfig": {
                    "aspectRatio": aspect_ratio,
                    "imageSize": image_size,
                },
            },
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=150) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            for cand in data.get("candidates", []):
                for part in cand.get("content", {}).get("parts", []):
                    if "inlineData" in part and part["inlineData"].get("data"):
                        raw = base64.b64decode(part["inlineData"]["data"])
                        im = Image.open(io.BytesIO(raw)).convert("RGB")
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        im.save(output_path, format="PNG", compress_level=3)
                        return output_path
            raise RuntimeError(f"No inlineData image in response: {json.dumps(data)[:300]}")
        except Exception as e:
            last_err = e
            print(f"[RETRY {attempt}/{retries}] {output_path.name} ({model} 2K): {e}")
            time.sleep(2 * attempt)
    raise RuntimeError(f"Failed to generate 2K image {output_path}: {last_err}")


def extract_foreground_mask_and_crop(
    im: Image.Image,
    is_floating_prop: bool = False,
) -> tuple[np.ndarray, np.ndarray]:
    """Extract the primary connected character + standee base `(rgb_crop, mask_crop)` from a
    white-background standee plate, stripping any disconnected stray islands, border noise,
    or enclosed cream/white paper gaps between boots/legs.
    """
    arr = np.array(im.convert("RGB"), dtype=np.float32)
    h, w, _ = arr.shape

    top = np.median(arr[:16, :, :], axis=0)
    bot = np.median(arr[-16:, :, :], axis=0)
    v = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None, None]
    bg_field = top[None, :, :] * (1.0 - v) + bot[None, :, :] * v
    dist = np.linalg.norm(arr - bg_field, axis=2)

    gray = arr.mean(axis=2)
    grad = np.hypot(ndimage.sobel(gray, axis=1), ndimage.sobel(gray, axis=0))

    if is_floating_prop:
        # Preserve delicate pale golden-amber spectral mist around the floating dagger
        is_paper_bg = (gray > 245.0) & (grad < 10.0) & ((arr.max(axis=2) - arr.min(axis=2)) < 14.0)
        core = ((dist > 11.0) | (grad > 12.0)) & (~is_paper_bg)
    else:
        # Any bright, low-gradient paper/cream region (e.g. #F7F3EA between boots) is background
        is_paper_bg = (gray > 218.0) & (grad < 16.0) & ((arr.max(axis=2) - arr.min(axis=2)) < 42.0)
        core = ((dist > 22.0) | (grad > 18.0)) & (~is_paper_bg)

    core[:4, :] = False
    core[-4:, :] = False
    core[:, :4] = False
    core[:, -4:] = False

    struct = ndimage.generate_binary_structure(2, 2)
    fg = ndimage.binary_closing(core, structure=struct, iterations=2)

    # Fill only small interior holes (e.g. eye whites, small highlights < 2500 px), NOT large
    # background openings between boots/cloaks!
    holes = ndimage.binary_fill_holes(fg) & (~fg)
    lbl_h, n_h = ndimage.label(holes)
    if n_h > 0:
        h_sizes = ndimage.sum(holes, lbl_h, range(1, n_h + 1))
        for idx_h, sz_h in enumerate(h_sizes, 1):
            if sz_h < (8000 if is_floating_prop else 2500):
                fg |= lbl_h == idx_h

    if not is_floating_prop:
        fg = ndimage.binary_erosion(fg, structure=struct, iterations=1)
        fg &= ~is_paper_bg

    lbl, n_cc = ndimage.label(fg)
    if n_cc > 0:
        sizes = ndimage.sum(fg, lbl, range(1, n_cc + 1))
        max_sz = max(sizes) if len(sizes) > 0 else 0
        keep = np.zeros_like(fg)
        min_keep = max(250.0, max_sz * 0.04) if is_floating_prop else max(800.0, max_sz * 0.12)
        for idx_c, sz in enumerate(sizes, 1):
            if sz >= min_keep:
                keep |= lbl == idx_c
        fg = keep

    ys, xs = np.where(fg)
    if len(ys) == 0:
        return arr, np.ones((h, w), dtype=bool)

    pad = 12 if is_floating_prop else 10
    y0 = max(0, int(ys.min()) - pad)
    y1 = min(h, int(ys.max()) + pad + 1)
    x0 = max(0, int(xs.min()) - pad)
    x1 = min(w, int(xs.max()) + pad + 1)
    return arr[y0:y1, x0:x1].copy(), fg[y0:y1, x0:x1].copy()


def clean_solo_standee_png(png_path: Path, is_floating_prop: bool = False) -> dict:
    """Clean a 2K (1792x2400) solo standee PNG so the background outside the character is pure
    #FFFFFF and the character stands ~1850-1960 px tall (or compact centered floating prop for
    the spectral dagger) with clean margins.
    """
    im = Image.open(png_path).convert("RGB")
    w, h = im.size
    rgb_crop, mask_crop = extract_foreground_mask_and_crop(im, is_floating_prop=is_floating_prop)

    dist_out = ndimage.distance_transform_edt(~mask_crop)
    feather = 4.5 if is_floating_prop else 2.4
    alpha = np.clip((feather - dist_out) / feather, 0.0, 1.0)[:, :, None]
    clean_rgb = np.clip(rgb_crop * alpha + 255.0 * (1.0 - alpha), 0, 255).astype(np.uint8)
    crop_im = Image.fromarray(clean_rgb, mode="RGB")

    cw, ch = crop_im.size
    if is_floating_prop:
        # Compact floating prop in mid-air (~960-1150 px tall)
        target_h = 1080
        max_w = int(round(w * 0.62))
        if ch < 920 or ch > 1220 or cw > max_w:
            scale = min(max_w / float(max(1, cw)), target_h / float(max(1, ch)))
            cw = max(1, int(round(cw * scale)))
            ch = max(1, int(round(ch * scale)))
            crop_im = crop_im.resize((cw, ch), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (w, h), (255, 255, 255))
        px = (w - cw) // 2
        py = (h - ch) // 2
        canvas.paste(crop_im, (px, py))
    else:
        # Normalize full-body character standees to ~1850-1960 px height
        min_h = 1865
        max_h = 1955
        target_h = 1925
        max_w = int(round(w * 0.82))
        if ch < min_h or ch > max_h or cw > max_w:
            scale = min(max_w / float(max(1, cw)), target_h / float(max(1, ch)))
            cw = max(1, int(round(cw * scale)))
            ch = max(1, int(round(ch * scale)))
            crop_im = crop_im.resize((cw, ch), Image.Resampling.LANCZOS)

        canvas = Image.new("RGB", (w, h), (255, 255, 255))
        px = (w - cw) // 2
        py = int(round(h * 0.90)) - ch
        py = max(int(round(h * 0.08)), min(int(round(h * 0.92)) - ch, py))
        canvas.paste(crop_im, (px, py))

    canvas.save(png_path, format="PNG", compress_level=3)
    return {"canvas_size": (w, h), "figure_size": (cw, ch)}


def assemble_cutout_sheet_from_solo_standees(
    solo_paths: list[Path],
    out_png_2k: Path,
    out_jpg_1k: Path,
) -> dict:
    """Compose 3 solo 2K standee PNGs (`left`, `center`, `right`) onto a 2K (2752x1536)
    lossless PNG sheet (`out_png_2k`) and a 1376x768 normalized JPEG sheet (`out_jpg_1k`)
    with guaranteed `split1 = 0, split2 = 0` and margins `>= 14.2%`.
    """
    w, h = TARGET_2K_W, TARGET_2K_H
    canvas_2k = Image.new("RGB", (w, h), (255, 255, 255))

    col_bounds = [
        (int(round(w * 0.142)), int(round(w * 0.342))),
        (int(round(w * 0.395)), int(round(w * 0.605))),
        (int(round(w * 0.658)), int(round(w * 0.858))),
    ]
    target_col_h = int(round(h * 0.68))
    baseline_y = int(round(h * 0.84))

    for idx_col, spath in enumerate(solo_paths):
        im_solo = Image.open(spath).convert("RGB")
        rgb_crop, mask_crop = extract_foreground_mask_and_crop(im_solo)
        dist_out = ndimage.distance_transform_edt(~mask_crop)
        alpha = np.clip((2.2 - dist_out) / 2.2, 0.0, 1.0)[:, :, None]
        clean_rgb = np.clip(rgb_crop * alpha + 255.0 * (1.0 - alpha), 0, 255).astype(np.uint8)
        crop_im = Image.fromarray(clean_rgb, mode="RGB")

        cw, ch = crop_im.size
        bx0, bx1 = col_bounds[idx_col]
        max_col_w = bx1 - bx0
        scale = min(max_col_w / float(max(1, cw)), target_col_h / float(max(1, ch)))
        cw = max(1, int(round(cw * scale)))
        ch = max(1, int(round(ch * scale)))
        crop_im = crop_im.resize((cw, ch), Image.Resampling.LANCZOS)

        paste_x = (bx0 + bx1 - cw) // 2
        paste_x = max(bx0, min(bx1 - cw, paste_x))
        paste_y = baseline_y - ch
        paste_y = max(int(round(h * 0.15)), min(int(round(h * 0.85)) - ch, paste_y))
        canvas_2k.paste(crop_im, (paste_x, paste_y))

    out_png_2k.parent.mkdir(parents=True, exist_ok=True)
    canvas_2k.save(out_png_2k, format="PNG", compress_level=3)

    canvas_1k = canvas_2k.resize((TARGET_W, TARGET_H), Image.Resampling.LANCZOS)
    canvas_1k.save(out_jpg_1k, quality=95)
    return measure_cutout_metrics(out_jpg_1k)


def strip_outer_border_if_any(bg_path: Path) -> None:
    """Ensure `_bg.jpg` is 100% edge-to-edge full-bleed with zero cream/white outer paper
    margins or black border lines along any of the 4 edges.
    """
    im = Image.open(bg_path).convert("RGB")
    arr = np.array(im, dtype=np.float32)
    h, w, _ = arr.shape

    gray = arr.mean(axis=2)
    row_bright = (gray > 195).mean(axis=1)
    col_bright = (gray > 195).mean(axis=0)

    y0, y1 = 0, h
    x0, x1 = 0, w
    max_trim_y = int(h * 0.06)
    max_trim_x = int(w * 0.06)

    while y0 < max_trim_y and (row_bright[y0] > 0.35 or gray[y0, :].std() < 12.0):
        y0 += 1
    while y1 > h - max_trim_y and (row_bright[y1 - 1] > 0.35 or gray[y1 - 1, :].std() < 12.0):
        y1 -= 1
    while x0 < max_trim_x and (col_bright[x0] > 0.35 or gray[:, x0].std() < 12.0):
        x0 += 1
    while x1 > w - max_trim_x and (col_bright[x1 - 1] > 0.35 or gray[:, x1 - 1].std() < 12.0):
        x1 -= 1

    if y0 > 0 or y1 < h or x0 > 0 or x1 < w:
        pad_in = 6
        y0 = min(max_trim_y, y0 + pad_in)
        y1 = max(h - max_trim_y, y1 - pad_in)
        x0 = min(max_trim_x, x0 + pad_in)
        x1 = max(w - max_trim_x, x1 - pad_in)
        cropped = im.crop((x0, y0, x1, y1)).resize((TARGET_W, TARGET_H), Image.Resampling.LANCZOS)
        cropped.save(bg_path, quality=95)
        print(f"[TRIM-BORDER] {bg_path.name}: cropped ({x0},{y0})-({x1},{y1}) -> {TARGET_W}x{TARGET_H}")


def measure_cutout_metrics(cutouts_path: Path) -> dict:
    im = Image.open(cutouts_path).convert("RGB")
    arr = np.array(im, dtype=np.float32)
    h, w, _ = arr.shape
    top = np.median(arr[:14, :, :], axis=0)
    bot = np.median(arr[-14:, :, :], axis=0)
    v = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None, None]
    bg_field = top[None, :, :] * (1.0 - v) + bot[None, :, :] * v
    dist = np.linalg.norm(arr - bg_field, axis=2)
    gray = arr.mean(axis=2)
    grad = np.hypot(ndimage.sobel(gray, axis=1), ndimage.sobel(gray, axis=0))
    core = (dist > 24.0) | (grad > 20.0)
    struct = ndimage.generate_binary_structure(2, 2)
    fg = ndimage.binary_fill_holes(ndimage.binary_closing(core, structure=struct, iterations=2))
    fg = ndimage.binary_fill_holes(ndimage.binary_erosion(fg, structure=struct, iterations=1))

    col_fg = fg.sum(axis=0)
    s1 = int(col_fg[int(w * 0.24) : int(w * 0.44)].min())
    s2 = int(col_fg[int(w * 0.56) : int(w * 0.76)].min())
    ys, xs = np.where(fg)
    top_m = float(ys.min()) / h * 100.0
    bot_m = float(h - 1 - ys.max()) / h * 100.0
    left_m = float(xs.min()) / w * 100.0
    right_m = float(w - 1 - xs.max()) / w * 100.0
    return {
        "width": w,
        "height": h,
        "split1": s1,
        "split2": s2,
        "top_pct": round(top_m, 2),
        "bot_pct": round(bot_m, 2),
        "left_pct": round(left_m, 2),
        "right_pct": round(right_m, 2),
    }


def build_char_sheet_reference_crops(char_sheet_path: Path) -> dict[str, Image.Image]:
    """Slice `07_macbeth_char_sheet.jpg` (and direction-matched solo standee plates when present)
    into character-specific reference crops, oriented to match each standee's target stage gaze
    direction so the reference prior never conflicts with the prompt's three-quarter profile gaze.
    """
    cs = Image.open(char_sheet_path).convert("RGB")
    w, h = cs.size
    crop_sisters = cs.crop((0, 0, int(w * 0.34), h))
    crop_commander = cs.crop((int(w * 0.34), 0, int(w * 0.68), h))
    crop_general = cs.crop((int(w * 0.68), 0, w, h))

    s2_left_path = POPUP_DIR / "07_macbeth_standee_s2_left.png"
    if s2_left_path.exists():
        s2_commander_right = Image.open(s2_left_path).convert("RGB")
        s2_commander_left = ImageOps.mirror(s2_commander_right)
    else:
        s2_commander_right = crop_commander
        s2_commander_left = ImageOps.mirror(crop_commander)

    s2_center_path = POPUP_DIR / "07_macbeth_standee_s2_center.png"
    if s2_center_path.exists():
        s2_general_left = ImageOps.mirror(Image.open(s2_center_path).convert("RGB"))
    else:
        s2_general_left = crop_general

    return {
        "sisters_facing_right": crop_sisters,
        "sisters_facing_left": ImageOps.mirror(crop_sisters),
        "commander_facing_right": crop_commander,
        "commander_facing_left": s2_commander_left,
        "general_facing_right": ImageOps.mirror(crop_general),
        "general_facing_left": s2_general_left,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate anonymous 2K 07_macbeth Toy Theatre assets.")
    parser.add_argument("--force", action="store_true", help="Regenerate existing files.")
    parser.add_argument("--only", nargs="*", help="Filter by filename substring.")
    args = parser.parse_args()

    api_key = get_api_key()
    ILLUST_DIR.mkdir(parents=True, exist_ok=True)
    POPUP_DIR.mkdir(parents=True, exist_ok=True)

    char_sheet_path = ILLUST_DIR / "07_macbeth_char_sheet.jpg"
    if not char_sheet_path.exists() or (
        args.force and (not args.only or any(tok in char_sheet_path.name for tok in args.only))
    ):
        print(f"[GEN] {char_sheet_path.name} ...")
        call_gemini_image(
            prompt=CHAR_SHEET_PROMPT,
            output_path=char_sheet_path,
            api_key=api_key,
            ref_image_path=None,
        )
        print(f"[OK]  {char_sheet_path.name} ({char_sheet_path.stat().st_size // 1024} KB)")

    spread_1_bg_ref = POPUP_DIR / "07_macbeth_spread_1_bg.jpg"
    bg_style_ref = spread_1_bg_ref if spread_1_bg_ref.exists() else char_sheet_path

    # Backdrops (16:9 full-bleed)
    bg_jobs = [
        ("07_macbeth_spread_1_bg.jpg", SPREAD_1_BG_PROMPT, None),
        ("07_macbeth_spread_2_bg.jpg", SPREAD_2_BG_PROMPT, None),
        ("07_macbeth_spread_3_bg.jpg", SPREAD_3_BG_PROMPT, bg_style_ref),
        ("07_macbeth_spread_4_bg.jpg", SPREAD_4_BG_PROMPT, bg_style_ref),
    ]
    for fname, prompt, ref_bg in bg_jobs:
        out_path = POPUP_DIR / fname
        if args.only and not any(tok in fname for tok in args.only):
            continue
        if args.force or not out_path.exists():
            print(f"[GEN] {fname} ...")
            call_gemini_image(
                prompt=prompt,
                output_path=out_path,
                api_key=api_key,
                ref_image_path=ref_bg,
            )
            strip_outer_border_if_any(out_path)
            print(f"[OK]  {fname} ({out_path.stat().st_size // 1024} KB)")

    # Solo 2K (1792x2400) lossless PNG standees with explicit three-quarter gaze directions
    ref_crops = build_char_sheet_reference_crops(char_sheet_path)
    standee_jobs = [
        ("07_macbeth_standee_s1_left.png", STANDEE_S1_LEFT_PROMPT, ref_crops["sisters_facing_right"], False),
        ("07_macbeth_standee_s1_center.png", STANDEE_S1_CENTER_PROMPT, ref_crops["sisters_facing_left"], False),
        ("07_macbeth_standee_s1_right.png", STANDEE_S1_RIGHT_PROMPT, ref_crops["sisters_facing_left"], False),
        ("07_macbeth_standee_s2_left.png", STANDEE_S2_LEFT_PROMPT, ref_crops["commander_facing_right"], False),
        ("07_macbeth_standee_s2_center.png", STANDEE_S2_CENTER_PROMPT, ref_crops["general_facing_right"], False),
        ("07_macbeth_standee_s2_right.png", STANDEE_S2_RIGHT_PROMPT, ref_crops["sisters_facing_left"], False),
        ("07_macbeth_standee_s2_ross.png", STANDEE_S2_ROSS_PROMPT, ref_crops["general_facing_left"], False),
        ("07_macbeth_standee_s3_lady.png", STANDEE_S3_LADY_PROMPT, ref_crops["commander_facing_left"], False),
        ("07_macbeth_standee_s4_dagger.png", STANDEE_S4_DAGGER_PROMPT, ref_crops["commander_facing_right"], True),
        ("07_macbeth_standee_s4_macbeth_daggers.png", STANDEE_S4_MACBETH_DAGGERS_PROMPT, ref_crops["commander_facing_left"], False),
    ]

    for fname, prompt, ref_im, is_prop in standee_jobs:
        out_path = POPUP_DIR / fname
        if args.only and not any(tok in fname for tok in args.only):
            continue
        if args.force or not out_path.exists():
            print(f"[GEN 2K] {fname} ...")
            call_gemini_image_2k(
                prompt=prompt,
                output_path=out_path,
                api_key=api_key,
                ref_image=ref_im,
                aspect_ratio="3:4",
                image_size="2K",
            )
            info = clean_solo_standee_png(out_path, is_floating_prop=is_prop)
            print(f"[OK 2K]  {fname}: {info} ({out_path.stat().st_size // 1024} KB)")

    # Assemble 2K PNG & 1K JPEG 3-column cutout sheets from the solo 2K standees only when requested
    s1_solos = [
        POPUP_DIR / "07_macbeth_standee_s1_left.png",
        POPUP_DIR / "07_macbeth_standee_s1_center.png",
        POPUP_DIR / "07_macbeth_standee_s1_right.png",
    ]
    s1_cut_png = POPUP_DIR / "07_macbeth_spread_1_cutouts.png"
    s1_cut_jpg = POPUP_DIR / "07_macbeth_spread_1_cutouts.jpg"
    if all(p.exists() for p in s1_solos) and (
        not s1_cut_png.exists()
        or not s1_cut_jpg.exists()
        or (args.force and (not args.only or any(tok in "07_macbeth_spread_1_cutouts" for tok in args.only)))
    ):
        m1 = assemble_cutout_sheet_from_solo_standees(s1_solos, s1_cut_png, s1_cut_jpg)
        print(f"[ASSEMBLE] 07_macbeth_spread_1_cutouts (.png 2K + .jpg 1K): {m1}")

    s2_solos = [
        POPUP_DIR / "07_macbeth_standee_s2_left.png",
        POPUP_DIR / "07_macbeth_standee_s2_center.png",
        POPUP_DIR / "07_macbeth_standee_s2_right.png",
    ]
    s2_cut_png = POPUP_DIR / "07_macbeth_spread_2_cutouts.png"
    s2_cut_jpg = POPUP_DIR / "07_macbeth_spread_2_cutouts.jpg"
    if all(p.exists() for p in s2_solos) and (
        not s2_cut_png.exists()
        or not s2_cut_jpg.exists()
        or (args.force and (not args.only or any(tok in "07_macbeth_spread_2_cutouts" for tok in args.only)))
    ):
        m2 = assemble_cutout_sheet_from_solo_standees(s2_solos, s2_cut_png, s2_cut_jpg)
        print(f"[ASSEMBLE] 07_macbeth_spread_2_cutouts (.png 2K + .jpg 1K): {m2}")


if __name__ == "__main__":
    main()
