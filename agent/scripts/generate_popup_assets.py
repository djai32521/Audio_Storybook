#!/usr/bin/env python3
"""Generate multi-plane paper pop-up book assets (5 character reference sheets,
8 canonical empty stage backplates + shared-room copies, and 15 three-column die-cut
character/prop sheets on pure #FFFFFF) for Books 1-5 at native 2K resolution using
`gemini-3.1-flash-lite-image` ("imageSize": "2K") conditioned on each book's
character reference sheet.

Enforces:
1. Anonymous, Book-Derived Visual Descriptions (Zero Character/Book/Place Names):
   - All character sheets, stage backplates, and die-cut cutout prompts use strictly
     anonymous, period-authentic visual descriptions derived from the book text, with
     ZERO character names, ZERO book titles, ZERO author/illustrator names, and ZERO
     famous place names so the model never reproduces film/animation/adaptation tropes.
2. Explicit Three-Quarter Stage Blocking & Gaze Direction:
   - Every character in a cutout sheet has an explicit three-quarter profile facing and
     gaze direction (`LEFT` column facing RIGHT `->` toward stage center/right; `RIGHT`
     column facing LEFT `<-` toward stage center/left; `CENTER` character facing the
     scene's dramatic partner).
3. Room / Location Continuity Across Spreads:
   - Consecutive spreads in the same room or location share the exact same `_bg.jpg`
     backplate file (`same_bg_as`).
4. Strict Foreground/Background Separation & Full-Bleed Backplates:
   - Architectural features belong ONLY in `_bg.jpg` on the back wall/distance, with a
     completely open, bare, uncluttered center and foreground floor/ground and zero outer
     paper border (`strip_outer_border_if_any`).
   - `_cutouts.jpg` contains ONLY 3 compact, self-contained, freestanding foreground
     characters or compact freestanding props that NEVER duplicate anything in `_bg.jpg`.
5. Strict Anti-Cropping & Column Normalization:
   - `_cutouts.jpg` arranges 3 compact, full-length freestanding items side by side on a
     uniform pure solid `#FFFFFF` background, and deterministically normalizes the 3 columns
     into `[13.5%, 32.5%]`, `[39.5%, 60.5%]`, and `[67.5%, 86.5%]` with `split1 == 0`,
     `split2 == 0`, and `>= 13%` pure `#FFFFFF` margins on all four sides.
"""

import argparse
import base64
import concurrent.futures
import io
import json
import re
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

from generate_illustrations import call_nano_banana_lite, get_api_key

ROOT = Path(__file__).resolve().parent.parent
ILLUST_DIR = ROOT / "illustrations"
POPUP_DIR = ILLUST_DIR / "popup"

TARGET_W = 1376
TARGET_H = 768

FORBIDDEN_WORDS = (
    # Book 1
    "bennet",
    "bingley",
    "darcy",
    "netherfield",
    "longbourn",
    "meryton",
    "austen",
    "pride and prejudice",
    # Book 2
    "holmes",
    "sherlock",
    "watson",
    "mortimer",
    "baskerville",
    "baskervilles",
    "baker street",
    "dartmoor",
    "london",
    "conan doyle",
    "paget",
    # Book 3
    "alice",
    "dinah",
    "wonderland",
    "lewis carroll",
    "carroll",
    "tenniel",
    "disney",
    # Book 4
    "time traveller",
    "time machine",
    "filby",
    "weena",
    "eloi",
    "morlock",
    "h. g. wells",
    # Book 5
    "tom sawyer",
    "sawyer",
    "aunt polly",
    "polly",
    "huck",
    "huckleberry",
    "becky",
    "mark twain",
    "twain",
    "st. petersburg",
    "missouri",
    "mississippi",
)

BG_FULLBLEED_RULES = (
    "CRITICAL COMPOSITION RULES FOR STAGE BACKDROP:\n"
    "1. FULL-BLEED 16:9 ARTWORK: Paint a flat 2D illustration that fills 100% of the 16:9 "
    "canvas completely from edge to edge and corner to corner. Strictly NO outer paper border, "
    "NO unpainted cream margins, NO decorative frame, NO arch vignette, and NO 3D pop-up book "
    "or cardboard theatre mockup.\n"
    "2. COMPLETELY EMPTY FOREGROUND STAGE FLOOR: Keep all architectural or landscape details "
    "on the distant back wall or far horizon. The entire center and foreground floor or ground "
    "must be completely open, bare, and empty like an uncluttered stage floor — strictly NO "
    "foreground objects, NO people, NO characters, and NO animals anywhere."
)

CUTOUT_LAYOUT_RULES = (
    "CRITICAL LAYOUT & ANTI-CROPPING RULES:\n"
    "1. UNIFORM PURE SOLID WHITE (#FFFFFF) BACKGROUND ONLY: The entire canvas background from "
    "edge to edge must be one seamless, flat, untextured pure white (#FFFFFF) field. Do NOT "
    "draw any grey shading, column rectangles, vertical divider stripes, paper cutout outlines, "
    "sticker borders, airbrush glow halos, floor lines, cast shadows, frames, or background scenery.\n"
    "2. THREE WIDELY SPACED ITEMS (LEFT, CENTER, RIGHT): Place the three freestanding subjects "
    "side by side in three clearly separated columns (left at ~22%, center at ~50%, right at ~78%) "
    "with wide empty pure-white (#FFFFFF) space separating them so they never touch or overlap.\n"
    "3. COMPACT FULL-LENGTH FIGURES WITH GENEROUS WHITE MARGINS: Draw every figure and prop "
    "compactly (each occupying roughly 55% to 65% of the canvas height) with at least 15% "
    "empty pure white (#FFFFFF) margin above the highest head/top, below the lowest "
    "shoe/chair-leg/base, and outside the left and right edges so nothing is ever cropped.\n"
    "4. ZERO TEXT OR NUMBERS: Strictly NO text, NO letters, NO captions, NO numbers, and NO "
    "labels anywhere on the image."
)

# Anonymous, book-text-derived character descriptions (ZERO character or book names)
B1_GENTLEMAN = (
    "a dry, observant fifty-year-old 1810s English country gentleman with lean features, "
    "greying sideburns, a high white linen cravat, buff waistcoat, and tailored dark "
    "olive-brown wool cutaway coat and breeches"
)
B1_LADY = (
    "an animated forty-five-year-old 1810s English country gentlewoman with soft curls "
    "under a lace morning cap, wearing a high-waisted sage-and-cream sprigged muslin "
    "Empire-waist gown with a light shawl"
)

B2_INVESTIGATOR = (
    "a tall, spare late-Victorian gentleman in his early forties with sharp grey eyes, "
    "straight dark hair brushed back, clean-shaven angular face, wearing a dark claret-brown "
    "velveteen indoor smoking jacket over a white wing collar, dark waistcoat and trousers "
    "(no hat, no cape)"
)
B2_PHYSICIAN = (
    "a sturdy, warm-faced late-Victorian gentleman in his forties with neatly parted "
    "sandy-brown hair and a trim moustache, wearing a brown three-piece tweed morning suit"
)

B3_GIRL = (
    "a curious seven-year-old 1860s Victorian English girl with wavy shoulder-length dark "
    "chestnut-brown hair (no headband), wearing a simple 1860s summer dress in warm "
    "terracotta-ochre linen with short puffed sleeves, cream stockings, and buttoned ankle "
    "boots (NOT blonde, NOT wearing a blue dress or white apron)"
)
B3_SISTER = (
    "a sixteen-year-old 1860s Victorian girl with braided brown hair wearing a soft "
    "olive-and-cream summer dress, holding a small clothbound book"
)
B3_RABBIT = (
    "a naturalistically proportioned white English country rabbit with pink eyes, wearing "
    "a small buttoned russet-tweed waistcoat and holding a round brass pocket-watch on a chain"
)

B4_INVENTOR = (
    "a lean, pale-faced late-Victorian natural philosopher in his late thirties with tousled "
    "dark brown hair, bright grey eyes, and a short trim beard, wearing an unbuttoned dark "
    "charcoal waistcoat over a white linen shirt and dark trousers"
)
B4_DEBATER = (
    "an argumentative Victorian gentleman in his thirties with thick wavy auburn-red hair "
    "and a neat red moustache, wearing a warm brown wool frock coat and high collar"
)
B4_PHYSICIAN_GUEST = (
    "a composed fifty-year-old Victorian gentleman with silver-streaked hair and spectacles, "
    "wearing a dark evening coat"
)

B5_AUNT = (
    "a tall, kindly sixty-year-old 1840s American frontier woman with grey hair pulled into "
    "a neat bun, small square brass spectacles pushed high up on her forehead, wearing a "
    "plain indigo-dyed homespun cotton ankle-length dress, a clean white linen apron, and "
    "black leather ankle shoes on her feet (wearing shoes, NOT barefoot)"
)
B5_BOY = (
    "a wiry ten-year-old 1840s country boy with messy sun-bleached brown hair "
    "(no hat), wearing a short buttoned tan wool roundabout jacket over a terracotta homespun "
    "shirt and rolled-up patched trousers with bare feet, his empty hands at his sides with "
    "dark berry-jam smudges on his cheeks and hands"
)


POPUP_SPREADS = {
    "01_pride_and_prejudice": {
        "char_sheet": "illustrations/01_pride_and_prejudice_char_sheet.jpg",
        "char_sheet_prompt": (
            "Minimalist editorial book illustration character reference sheet on clean "
            "warm cream archival paper (#F6F2EA). Delicate 1810s Regency pen-and-ink "
            "line drawing with sparse, subtle muted sage-green (#4A6B53) and warm "
            "sepia watercolor wash. Show two distinct full-length 1810s characters "
            "standing side by side with generous negative space, turned toward each other "
            f"in three-quarter profile: on the left, {B1_GENTLEMAN}, turned in three-quarter "
            "profile facing RIGHT (->) toward the center while holding a small leather-bound "
            f"book; on the right, {B1_LADY}, turned in three-quarter profile facing LEFT (<-) "
            "toward the gentleman. Clean fine-press ink linework, minimalist restraint, no text, "
            "no labels, no borders."
        ),
        "style": (
            "1810s Regency fine dip-pen sepia ink line drawing with delicate muted watercolour "
            "wash (sage green, warm ochre, dusty rose, pale blue, and sepia ink). "
            "Strictly NO text, NO captions, NO words, NO letters, NO signatures anywhere."
        ),
        "spreads": [
            {
                "idx": 1,
                "caption": "Morning Room",
                "bg_prompt": (
                    "1810s Regency country-house morning room back-wall backdrop. "
                    "Along the distant back wall are tall sunlit Georgian sash windows with pale sage-green "
                    "drapes, cream wainscot wall panelling, and small framed landscape prints hung high on "
                    "the wall. In front of the back wall is a wide, completely bare, empty polished wood "
                    "floor and flat woven rug with no furniture.\n"
                    f"{BG_FULLBLEED_RULES}"
                ),
                "cutouts_prompt": (
                    "Three separate, compact, freestanding full-length subjects isolated side by side on a "
                    "seamless PURE SOLID WHITE (#FFFFFF) background, matching the character designs of the "
                    "attached reference sheet:\n"
                    f"- LEFT: Compact full-length standing figure of {B1_LADY}, turned in a clear "
                    "three-quarter profile FACING AND GAZING RIGHT (->) toward the center and right of the "
                    "stage, stepping forward and holding a small folded letter close to her chest (entire "
                    "cap to slippers visible).\n"
                    "- CENTER: A compact freestanding narrow round 1810s mahogany pedestal tea table set "
                    "with a porcelain teapot and two teacups (entire tabletop and tripod base visible).\n"
                    f"- RIGHT: Compact full-length figure of {B1_GENTLEMAN}, seated calmly in a compact "
                    "wooden library armchair angled in a clear three-quarter profile FACING AND GAZING LEFT "
                    "(<-) toward the lady on Stage Left, holding a small open leather-bound book in his lap "
                    "(entire head and all chair legs visible).\n"
                    f"{CUTOUT_LAYOUT_RULES}"
                ),
            },
            {
                "idx": 2,
                "caption": "The Country Park News",
                "same_bg_as": 1,
                "bg_prompt": (
                    "Same 1810s Regency morning room backdrop as Spread 1.\n"
                    f"{BG_FULLBLEED_RULES}"
                ),
                "cutouts_prompt": (
                    "Three separate, compact, freestanding full-length subjects isolated side by side on a "
                    "seamless PURE SOLID WHITE (#FFFFFF) background, matching the character designs of the "
                    "attached reference sheet:\n"
                    f"- LEFT: Compact full-length figure of {B1_GENTLEMAN}, seated in a compact green "
                    "upholstered library armchair angled in a clear three-quarter profile FACING AND GAZING "
                    "RIGHT (->) toward the lady on Stage Right, looking up dryly over the top of a small "
                    "leather-bound book held in his lap (entire head and all chair legs visible).\n"
                    "- CENTER: A compact freestanding 1810s terrestrial globe mounted in a brass meridian "
                    "arc on a carved three-legged mahogany stand.\n"
                    f"- RIGHT: Compact full-length upright standing figure of {B1_LADY}, turned in a clear "
                    "three-quarter profile FACING AND GAZING LEFT (<-) toward the gentleman on Stage Left, "
                    "clasping both hands eagerly in front of her waist (entire cap to slippers visible).\n"
                    f"{CUTOUT_LAYOUT_RULES}"
                ),
            },
            {
                "idx": 3,
                "caption": "A Man of Large Fortune",
                "same_bg_as": 1,
                "bg_prompt": (
                    "Same 1810s Regency morning room backdrop as Spread 1.\n"
                    f"{BG_FULLBLEED_RULES}"
                ),
                "cutouts_prompt": (
                    "Three separate, compact, freestanding full-length subjects isolated side by side on a "
                    "seamless PURE SOLID WHITE (#FFFFFF) background, matching the character designs of the "
                    "attached reference sheet:\n"
                    f"- LEFT: Compact full-length upright standing figure of {B1_LADY}, turned in a clear "
                    "three-quarter profile FACING AND GAZING RIGHT (->) toward the gentleman on Stage Right, "
                    "raising both hands near her shoulders in joyful delight (arms kept narrow within her "
                    "silhouette, entire cap to hem visible).\n"
                    "- CENTER: A compact freestanding 1810s gilt-wood classical harp standing upright beside "
                    "a small narrow pedestal stand holding a porcelain vase of pink roses.\n"
                    f"- RIGHT: Compact full-length upright standing figure of {B1_GENTLEMAN}, standing alone "
                    "on his own feet in a clear three-quarter profile FACING AND GAZING LEFT (<-) toward the "
                    "lady on Stage Left, with his hands clasped calmly behind his cutaway coat (entire head "
                    "to shoes visible).\n"
                    f"{CUTOUT_LAYOUT_RULES}"
                ),
            },
        ],
    },
    "02_hound_of_the_baskervilles": {
        "char_sheet": "illustrations/02_hound_of_the_baskervilles_char_sheet.jpg",
        "char_sheet_prompt": (
            "Minimalist 1900 late-Victorian woodblock and scratchboard engraving "
            "character reference sheet on aged ivory archival paper (#F2EDE2). Crisp "
            "charcoal-black ink linework (#181A1B) with a single restrained warm "
            "amber-ochre accent (#9E6B2E) and wide negative space. Show two distinct "
            "full-length characters standing side by side turned toward each other in "
            f"three-quarter profile: on the left, {B2_INVESTIGATOR}, turned in three-quarter "
            f"profile facing RIGHT (->) toward the center; on the right, {B2_PHYSICIAN}, "
            "turned in three-quarter profile facing LEFT (<-) toward the investigator and "
            "holding a thick bulbous-headed wooden walking-stick with a broad silver-gold "
            "band below the handle. Minimalist fine-press printmaking style, no text, "
            "no labels, no borders."
        ),
        "style": (
            "1900 late-Victorian periodical charcoal, graphite, and India-ink crosshatched wash drawing "
            "with warm sepia-grey tones and subtle amber highlights. "
            "Strictly NO text, NO captions, NO words, NO letters, NO newspaper headlines anywhere."
        ),
        "spreads": [
            {
                "idx": 1,
                "caption": "The Upstairs Sitting-Room",
                "same_bg_as": 2,
                "bg_prompt": (
                    "Same 1900 late-Victorian study backdrop as Spread 2.\n"
                    f"{BG_FULLBLEED_RULES}"
                ),
                "cutouts_prompt": (
                    "Three separate, compact, freestanding full-length subjects isolated side by side on a "
                    "seamless PURE SOLID WHITE (#FFFFFF) background, matching the character designs of the "
                    "attached reference sheet:\n"
                    f"- LEFT: Compact full-length figure of {B2_INVESTIGATOR}, seated in a compact wooden "
                    "armchair angled in a clear three-quarter profile FACING AND GAZING RIGHT (->) toward "
                    "the standing physician on Stage Right, leaning back with fingertips steepled under his "
                    "chin (entire head, feet, and chair legs visible).\n"
                    "- CENTER: A compact, narrow round Victorian breakfast table draped in a white cloth set "
                    "with a silver coffee pot, porcelain teacup, and toast rack (entire table base visible).\n"
                    f"- RIGHT: Compact full-length upright standing figure of {B2_PHYSICIAN}, standing "
                    "straight in a clear three-quarter profile FACING AND GAZING LEFT (<-) toward the seated "
                    "investigator on Stage Left, holding a single bulbous-headed wooden walking stick "
                    "vertically right beside his leg (entire head to shoes visible).\n"
                    f"{CUTOUT_LAYOUT_RULES}"
                ),
            },
            {
                "idx": 2,
                "caption": "The Silver-Banded Walking Stick",
                "bg_prompt": (
                    "1900 late-Victorian gentleman's study back-wall backdrop. "
                    "Built flat into the center of the distant back wall is a dark carved Victorian fireplace "
                    "hearth with a glowing amber coal grate and mantel clock, flanked by recessed floor-to-ceiling "
                    "wall bookshelves filled with leather scrapbooks. In front of the back wall is a completely "
                    "bare, open, empty Persian rug on dark floorboards.\n"
                    f"{BG_FULLBLEED_RULES}"
                ),
                "cutouts_prompt": (
                    "Three separate, compact, freestanding full-length subjects isolated side by side on a "
                    "seamless PURE SOLID WHITE (#FFFFFF) background, matching the character designs of the "
                    "attached reference sheet:\n"
                    f"- LEFT: Compact full-length upright standing figure of {B2_PHYSICIAN}, turned in a "
                    "clear three-quarter profile FACING AND GAZING RIGHT (->) toward the center and right of "
                    "the stage, holding the silver-banded wooden walking stick steeply angled in front of "
                    "his chest with both hands to inspect the silver band closely (entire head to shoes visible).\n"
                    "- CENTER: A compact freestanding narrow Victorian mahogany pedestal stand holding a "
                    "brass microscope, two glass chemical flasks, and a wooden violin with bow.\n"
                    f"- RIGHT: Compact full-length figure of {B2_INVESTIGATOR}, seated in a compact tufted "
                    "leather wingchair angled in a clear three-quarter profile FACING AND GAZING LEFT (<-) "
                    "toward the physician on Stage Left, holding a small briar pipe in one hand (entire head "
                    "and all chair legs visible).\n"
                    f"{CUTOUT_LAYOUT_RULES}"
                ),
            },
            {
                "idx": 3,
                "caption": "Examining the Stick",
                "same_bg_as": 2,
                "bg_prompt": (
                    "Same 1900 late-Victorian study backdrop as Spread 2.\n"
                    f"{BG_FULLBLEED_RULES}"
                ),
                "cutouts_prompt": (
                    "Three separate, compact, freestanding full-length subjects isolated side by side on a "
                    "seamless PURE SOLID WHITE (#FFFFFF) background, matching the character designs of the "
                    "attached reference sheet:\n"
                    f"- LEFT: Compact full-length upright standing figure of {B2_PHYSICIAN}, turned in a "
                    "clear three-quarter profile FACING AND GAZING RIGHT (->) toward the investigator on "
                    "Stage Right, holding the wooden walking stick vertically in his right hand close to his "
                    "side while gesturing calmly with his left hand (strictly ONE walking stick in the image, "
                    "entire head to shoes visible).\n"
                    "- CENTER: A compact, narrow freestanding octagonal Victorian mahogany side-table holding "
                    "a brass magnifying glass, a ceramic tobacco jar, and three stacked leather books.\n"
                    f"- RIGHT: Compact full-length upright standing figure of {B2_INVESTIGATOR}, standing "
                    "straight in a clear three-quarter profile FACING AND GAZING LEFT (<-) toward the "
                    "physician on Stage Left, with one hand in his jacket pocket and the other holding a "
                    "small curved briar pipe near his chin (strictly NO walking stick or cane in his hands, "
                    "entire head to shoes visible).\n"
                    f"{CUTOUT_LAYOUT_RULES}"
                ),
            },
        ],
    },
    "03_alice_in_wonderland": {
        "char_sheet": "illustrations/03_alice_in_wonderland_char_sheet.jpg",
        "char_sheet_prompt": (
            "Minimalist editorial book illustration character reference sheet on "
            "warm ivory paper (#F8F5EE). Delicate 1860s Victorian wood-engraving "
            "crosshatched black pen-and-ink linework with warm terracotta-ochre, "
            "soft olive-green, and russet-red watercolor accents. Show two distinct "
            "full-length characters standing side by side with generous empty paper space, "
            f"turned toward each other in three-quarter profile: on the left, {B3_GIRL}, "
            "turned in three-quarter profile facing RIGHT (->) toward the center; on the "
            f"right, {B3_RABBIT}, standing upright on its hind legs in three-quarter profile "
            "facing LEFT (<-) toward the girl. Minimalist, no text, no labels, no borders."
        ),
        "style": (
            "1860s Victorian wood-engraving crosshatching with delicate antique hand-tinted "
            "watercolour wash (warm terracotta-ochre, meadow green, soft olive, and russet accent). "
            "Strictly NO text, NO captions, NO words, NO letters, NO labels anywhere."
        ),
        "spreads": [
            {
                "idx": 1,
                "caption": "On the Sunny Riverbank",
                "bg_prompt": (
                    "2D 1860s Victorian English summer riverbank landscape backdrop. "
                    "In the distance is a gentle winding river reflecting cumulus clouds, distant willow trees "
                    "on the far bank, and sunlit rolling hills under a painted blue sky. Across the center and "
                    "foreground is a wide, smooth, completely open grassy meadow bank.\n"
                    f"{BG_FULLBLEED_RULES}"
                ),
                "cutouts_prompt": (
                    "Three separate, compact, freestanding full-length subjects isolated side by side on a "
                    "seamless PURE SOLID WHITE (#FFFFFF) background (use the attached reference sheet ONLY for "
                    "the young girl on the RIGHT; strictly DO NOT draw the white rabbit anywhere in this image!):\n"
                    f"- LEFT: Compact full-length figure of {B3_SISTER}, seated on a solid low mossy wooden log "
                    "and grassy mound (with the entire mossy log reaching the ground beneath her skirt so she "
                    "is completely grounded and not floating in mid-air), angled in a clear three-quarter "
                    "profile FACING AND GAZING RIGHT (->) toward her younger sister on Stage Right while reading "
                    "a small clothbound book in her lap (entire head, dress hem, and mossy log base visible).\n"
                    "- CENTER: A compact, low rounded mossy wooden tree stump surrounded by a tidy cluster "
                    "of blooming white meadow daisies and yellow buttercups (compact rounded top with generous "
                    "pure white space above it).\n"
                    f"- RIGHT: Compact full-length figure of {B3_GIRL} (strictly the young human girl in the "
                    "terracotta-ochre dress, NOT a rabbit), seated cross-legged on a small grassy tuft angled "
                    "in a clear three-quarter profile FACING AND GAZING LEFT (<-) toward her older sister on "
                    "Stage Left while weaving a chain of white daisies in her hands (entire head to buttoned "
                    "ankle boots visible).\n"
                    f"{CUTOUT_LAYOUT_RULES}"
                ),
            },
            {
                "idx": 2,
                "caption": "The Pocket-Watch",
                "same_bg_as": 1,
                "bg_prompt": (
                    "Same sunny riverbank landscape backdrop as Spread 1.\n"
                    f"{BG_FULLBLEED_RULES}"
                ),
                "cutouts_prompt": (
                    "Three separate, compact, freestanding full-length subjects isolated side by side on a "
                    "seamless PURE SOLID WHITE (#FFFFFF) background, matching the character designs of the "
                    "attached reference sheet:\n"
                    f"- LEFT: Compact full-length upright standing figure of {B3_GIRL}, turned in a clear "
                    "three-quarter profile FACING AND GAZING RIGHT (->) toward the white rabbit on Stage "
                    "Right, springing to her feet in startled wonder with hands raised near her cheeks "
                    "(entire head to buttoned ankle boots visible).\n"
                    "- CENTER: A compact, organic, self-contained rounded hollow tree-root burrow entrance "
                    "arch framed by curved mossy roots, small ferns, and three upright foxglove stems "
                    "(natural rounded silhouette surrounded on all four sides by generous pure white space).\n"
                    f"- RIGHT: Compact full-length upright standing figure of {B3_RABBIT}, standing on its "
                    "hind legs in a clear three-quarter profile FACING AND GAZING LEFT (<-) toward the center "
                    "and left of the stage while looking down at the round brass pocket-watch held in its "
                    "paw (entire ears to hind paws visible).\n"
                    f"{CUTOUT_LAYOUT_RULES}"
                ),
            },
            {
                "idx": 3,
                "caption": "Down the Deep Well",
                "bg_prompt": (
                    "2D subterranean brick well-shaft interior backdrop. "
                    "Curved antique dark-red brick and stone masonry walls stretching edge-to-edge across the "
                    "entire 16:9 canvas, with empty recessed brick arches and empty stone niches set into the "
                    "brickwork. Strictly NO cupboards, NO globes, NO clocks, NO jars, NO books, NO floating "
                    "objects, and NO people anywhere in the background.\n"
                    f"{BG_FULLBLEED_RULES}"
                ),
                "cutouts_prompt": (
                    "Three separate, compact, freestanding subjects isolated side by side on a seamless PURE "
                    "SOLID WHITE (#FFFFFF) background, matching the character designs of the attached "
                    "reference sheet:\n"
                    "- LEFT: A compact floating antique wooden wall-bracket shelf holding a porcelain teapot, "
                    "teacup, and unlabelled stoneware marmalade jar.\n"
                    f"- CENTER: Compact full-length figure of {B3_GIRL}, floating gracefully downward in "
                    "mid-air in a clear three-quarter profile FACING AND GAZING SLIGHTLY DOWNWARD AND RIGHT "
                    "(->), with her warm terracotta-ochre linen summer dress billowing compactly around her "
                    "knees and her arms and hands kept compact near her shoulders within her silhouette "
                    "(entire head to buttoned ankle boots visible).\n"
                    "- RIGHT: A compact floating Victorian brass terrestrial globe and an antique brass "
                    "pendulum wall clock drifting together in a tight vertical cluster.\n"
                    f"{CUTOUT_LAYOUT_RULES}"
                ),
            },
        ],
    },
    "04_the_time_machine": {
        "char_sheet": "illustrations/04_the_time_machine_char_sheet.jpg",
        "char_sheet_prompt": (
            "Minimalist architectural line and woodcut book illustration character "
            "reference sheet on pale slate-ivory paper (#F0F2F4). Clean Prussian-blue "
            "(#18222C) ink linework with warm burnished brass-gold (#B38628) accents "
            "and generous negative space. Show two distinct full-length 1895 "
            "Victorian gentlemen standing side by side turned toward each other in "
            f"three-quarter profile: on the left, {B4_INVENTOR}, turned in three-quarter "
            "profile facing RIGHT (->) toward the center and raising one lean forefinger "
            f"in explanation; on the right, {B4_DEBATER}, turned in three-quarter profile "
            "facing LEFT (<-) toward the natural philosopher with arms folded in sceptical "
            "debate. Minimalist fine-press illustration, no text, no labels, no borders."
        ),
        "style": (
            "1895 fin-de-siecle woodcut engraving and crosshatched ink illustration with warm amber firelight "
            "highlights against deep Prussian blue and charcoal-sepia shadows. "
            "Strictly NO text, NO captions, NO words, NO letters, NO labels anywhere."
        ),
        "spreads": [
            {
                "idx": 1,
                "caption": "The Firelit Smoking-Room",
                "bg_prompt": (
                    "Late-Victorian smoking-room back-wall backdrop. "
                    "Built flat into the center of the distant back wall is a carved stone Victorian fireplace "
                    "with a blazing amber hearth fire, flanked along the back wall by dark carved oak wainscot "
                    "panelling and heavy Prussian-blue velvet curtains. In front of the back wall, the entire "
                    "center and foreground wooden floor is completely bare, open, and empty with warm amber "
                    "firelight reflections.\n"
                    f"{BG_FULLBLEED_RULES}"
                ),
                "cutouts_prompt": (
                    "Three separate, compact, freestanding full-length subjects isolated side by side on a "
                    "seamless PURE SOLID WHITE (#FFFFFF) background, matching the character designs of the "
                    "attached reference sheet:\n"
                    f"- LEFT: Compact full-length upright standing figure of {B4_INVENTOR}, turned in a "
                    "clear three-quarter profile FACING AND GAZING RIGHT (->) toward his guest on Stage "
                    "Right, gesturing earnestly with one raised index finger kept close to his chest (entire "
                    "head to shoes visible).\n"
                    "- CENTER: A compact freestanding narrow round Victorian mahogany pedestal table holding "
                    "a crystal spirit decanter and two small glasses.\n"
                    f"- RIGHT: Compact full-length figure of {B4_PHYSICIAN_GUEST}, seated in a compact "
                    "quilted leather armchair angled in a clear three-quarter profile FACING AND GAZING LEFT "
                    "(<-) toward the natural philosopher on Stage Left, holding a small glass in his hand "
                    "(entire head and all chair legs visible).\n"
                    f"{CUTOUT_LAYOUT_RULES}"
                ),
            },
            {
                "idx": 2,
                "caption": "The Geometry Debate",
                "same_bg_as": 1,
                "bg_prompt": (
                    "Same late-Victorian firelit smoking-room backdrop as Spread 1.\n"
                    f"{BG_FULLBLEED_RULES}"
                ),
                "cutouts_prompt": (
                    "Three separate, compact, freestanding full-length subjects isolated side by side on a "
                    "seamless, flat, uniform PURE SOLID WHITE (#FFFFFF) background (with NO airbrush light "
                    "halo and NO grey background tint), matching the character designs of the attached reference sheet:\n"
                    f"- LEFT: Compact full-length figure of {B4_INVENTOR}, seated in a compact wooden "
                    "library chair angled in a clear three-quarter profile FACING AND GAZING RIGHT (->) "
                    "toward the auburn-haired gentleman on Stage Right, leaning slightly forward with hands "
                    "open close to his lap (entire head, feet, and chair legs visible).\n"
                    "- CENTER: A compact freestanding narrow octagonal mahogany pedestal table holding an "
                    "antique brass-and-amber-glass parlour oil lamp with a crisp ink outline and NO outer "
                    "glow halo on the white background (entire lamp chimney and table base visible).\n"
                    f"- RIGHT: Compact full-length figure of {B4_DEBATER}, seated in a compact upholstered "
                    "armchair angled in a clear three-quarter profile FACING AND GAZING LEFT (<-) toward the "
                    "natural philosopher on Stage Left, raising one hand in sceptical debate (entire head, "
                    "feet, and chair legs visible).\n"
                    f"{CUTOUT_LAYOUT_RULES}"
                ),
            },
            {
                "idx": 3,
                "caption": "The Fourth Dimension",
                "same_bg_as": 1,
                "bg_prompt": (
                    "Same late-Victorian firelit smoking-room backdrop as Spread 1.\n"
                    f"{BG_FULLBLEED_RULES}"
                ),
                "cutouts_prompt": (
                    "Three separate, compact, freestanding full-length subjects isolated side by side on one "
                    "seamless, flat, uniform PURE SOLID WHITE (#FFFFFF) background (strictly NO grey column "
                    "boxes or background panels), matching the character designs of the attached reference sheet:\n"
                    f"- LEFT: Compact full-length upright standing figure of {B4_INVENTOR}, turned in a "
                    "clear three-quarter profile FACING AND GAZING RIGHT (->) toward the miniature clockwork "
                    "mechanism at Stage Center, pointing one hand slightly downward in quiet triumph (entire "
                    "head to shoes visible).\n"
                    "- CENTER: A compact, narrow velvet-draped round pedestal table supporting a glittering "
                    "miniature clockwork horological mechanism made of brass rods, ivory bars, and quartz "
                    "crystal (entire mechanism and pedestal base visible).\n"
                    f"- RIGHT: Compact full-length upright standing figure of {B4_DEBATER}, standing straight "
                    "in a clear three-quarter profile FACING AND GAZING LEFT (<-) toward the miniature "
                    "clockwork mechanism at Stage Center, with his hands resting on his coat lapel and his "
                    "head tilted slightly down to inspect the mechanism (strictly upright vertical posture, "
                    "entire head to shoes visible).\n"
                    f"{CUTOUT_LAYOUT_RULES}"
                ),
            },
        ],
    },
    "05_tom_sawyer": {
        "char_sheet": "illustrations/05_tom_sawyer_char_sheet.jpg",
        "char_sheet_prompt": (
            "Minimalist 19th-century American woodcut and dip-pen book illustration "
            "character reference sheet on warm cotton-rag paper (#F6EFE4). Crisp "
            "walnut-brown ink linework (#261E19) with warm indigo-blue and "
            "sun-baked terracotta (#B85733) accents and wide negative space. Show "
            "two distinct full-length 1840s American frontier characters standing side by "
            f"side turned toward each other in three-quarter profile: on the left, {B5_AUNT}, "
            "turned in three-quarter profile facing RIGHT (->) toward the center; on the "
            f"right, {B5_BOY}, turned in three-quarter profile facing LEFT (<-) toward the "
            "older woman. Minimalist printmaking style, no text, no labels, no borders."
        ),
        "style": (
            "1870s 19th-century American frontier book illustration: expressive "
            "sepia dip-pen crosshatching with warm sunlit watercolour wash (golden ochre, sage green, "
            "indigo blue, and russet brown). "
            "Strictly NO text, NO captions, NO words, NO letters, NO labels anywhere."
        ),
        "spreads": [
            {
                "idx": 1,
                "caption": "At the Cottage Door",
                "same_bg_as": 2,
                "bg_prompt": (
                    "Same 1840s American frontier cottage room interior backdrop as Spread 2.\n"
                    f"{BG_FULLBLEED_RULES}"
                ),
                "cutouts_prompt": (
                    "Three separate, compact, freestanding full-length subjects isolated side by side on a "
                    "seamless PURE SOLID WHITE (#FFFFFF) background (use the attached reference sheet ONLY for "
                    "the older woman on the LEFT; strictly DO NOT draw the boy or any other person in the "
                    "CENTER or RIGHT columns — CENTER and RIGHT must be wooden furniture props only!):\n"
                    f"- LEFT: Compact full-length upright standing figure of {B5_AUNT}, turned in a clear "
                    "three-quarter profile FACING AND GAZING RIGHT (->) across the room toward the center "
                    "and right of the stage, holding a corn-husk broom vertically right beside her skirt "
                    "(entire head to shoes visible).\n"
                    "- CENTER: A compact freestanding empty 1840s wooden spindle rocking chair with a folded "
                    "patchwork quilt draped neatly over the seat (strictly an empty chair with NO person, "
                    "entire chair back and curved rockers visible).\n"
                    "- RIGHT: A compact freestanding small rustic wooden parlour table holding a woven wicker "
                    "sewing basket, spools of thread, and a red pincushion (strictly a table prop with NO "
                    "person, entire tabletop and four table legs visible).\n"
                    f"{CUTOUT_LAYOUT_RULES}"
                ),
            },
            {
                "idx": 2,
                "caption": "Caught by the Roundabout",
                "bg_prompt": (
                    "1840s American frontier cottage kitchen back-wall interior backdrop. "
                    "Along the distant back wall are warm horizontal timber boards and a sunlit paned window "
                    "looking out at blue sky. Across the center and foreground are wide pine floorboards that "
                    "are completely bare, open, and empty from corner to corner.\n"
                    f"{BG_FULLBLEED_RULES}"
                ),
                "cutouts_prompt": (
                    "Three separate, compact, freestanding full-length subjects isolated side by side on a "
                    "seamless PURE SOLID WHITE (#FFFFFF) background, matching the character designs of the "
                    "attached reference sheet:\n"
                    "- LEFT: A compact freestanding 1840s pine kitchen jam-cupboard standing on four short "
                    "wooden legs with its small door ajar, showing stoneware crocks and an unlabelled glass "
                    "jar of red berry jam inside (complete flat cornice top and all four bottom legs visible).\n"
                    f"- CENTER: Compact full-length upright standing figure of {B5_AUNT}, standing at Stage "
                    "Center turned in a clear three-quarter profile FACING AND GAZING RIGHT (->) toward the "
                    "boy on Stage Right, with her small square brass spectacles pulled down onto her nose and "
                    "holding a thin birch switch vertically near her shoulder (entire head to shoes visible).\n"
                    f"- RIGHT: ONE single compact full-length upright standing figure of {B5_BOY} (strictly ONE "
                    "boy in the right column — do NOT draw two boys or duplicate poses!), standing on Stage "
                    "Right turned in a clear three-quarter profile FACING AND GAZING LEFT (<-) toward the "
                    "older woman at Stage Center, looking sheepishly with dark berry-jam smudges on his "
                    "cheeks and hands (entire tousled hair to bare feet visible).\n"
                    f"{CUTOUT_LAYOUT_RULES}"
                ),
            },
            {
                "idx": 3,
                "caption": "Over the High Board-Fence",
                "bg_prompt": (
                    "2D 1840s American frontier summer backyard landscape backdrop. "
                    "Running horizontally across the back of the yard is a tall weathered whitewashed "
                    "vertical-plank wooden board fence, with green oak trees and distant river bluffs rising "
                    "behind the fence under a bright blue summer sky. In front of the whitewashed board fence "
                    "is a wide, completely empty, open sunlit green grass lawn stretching smoothly to the "
                    "bottom and side edges of the 16:9 frame, with nothing at all on the grass.\n"
                    f"{BG_FULLBLEED_RULES}"
                ),
                "cutouts_prompt": (
                    "Three separate, compact, freestanding full-length subjects isolated side by side on a "
                    "seamless PURE SOLID WHITE (#FFFFFF) background, matching the character designs of the "
                    "attached reference sheet:\n"
                    f"- LEFT: Compact full-length upright standing figure of {B5_AUNT}, turned in a clear "
                    "three-quarter profile FACING AND GAZING RIGHT (->) toward the boy on Stage Right, "
                    "holding a thin birch switch up in one hand while her face breaks into a surprised, "
                    "gentle laugh (entire head to shoes visible).\n"
                    "- CENTER: A compact freestanding weathered wooden apple barrel standing beside a woven "
                    "bushel basket of red apples and a tin watering can.\n"
                    f"- RIGHT: Compact full-length freestanding figure of {B5_BOY} in mid-leap on Stage "
                    "Right with his head turned in a clear three-quarter view FACING AND GAZING LEFT (<-) "
                    "back over his shoulder toward the older woman on Stage Left, grinning with his knees "
                    "tucked up (completely freestanding full-body pose, messy sun-bleached brown hair with "
                    "no hat, barefoot).\n"
                    f"{CUTOUT_LAYOUT_RULES}"
                ),
            },
        ],
    },
}


def assert_no_forbidden_words(prompt: str, name: str) -> None:
    low = prompt.lower()
    for word in FORBIDDEN_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", low):
            raise ValueError(f"Forbidden term {word!r} found in prompt for {name}")


def call_nano_banana_2k(
    prompt: str,
    output_path: Path,
    api_key: str,
    ref_image_path: Path | None = None,
    aspect_ratio: str = "16:9",
    model: str = "gemini-3.1-flash-lite-image",
    retries: int = 6,
) -> Path:
    """Call `gemini-3.1-flash-lite-image` at native 2K (`2752x1536` for `16:9`) via
    `generateContent` and downsample with `Image.Resampling.LANCZOS` to `1376x768` (`quality=95`)
    so `render_audiobook_video.py`'s die-cut border and bevel parameters stay in exact proportion.
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
            print(f"[RETRY {attempt}/{retries}] {output_path.name} ({model} 2K): {e}")
            time.sleep(2 * attempt)

    print(f"[FALLBACK] {output_path.name}: falling back to call_nano_banana_lite after {retries} attempts: {last_err}")
    return call_nano_banana_lite(
        prompt=prompt,
        output_path=output_path,
        api_key=api_key,
        ref_image_path=ref_image_path,
        aspect_ratio=aspect_ratio,
        retries=4,
    )


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


def _compute_foreground_mask(arr: np.ndarray) -> np.ndarray:
    h, w, _ = arr.shape
    top = np.median(arr[:14, :, :], axis=0)
    bot = np.median(arr[-14:, :, :], axis=0)
    v = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None, None]
    bg_field = top[None, :, :] * (1.0 - v) + bot[None, :, :] * v
    dist = np.linalg.norm(arr - bg_field, axis=2)

    gray = arr.mean(axis=2)
    grad = np.hypot(ndimage.sobel(gray, axis=1), ndimage.sobel(gray, axis=0))

    core = (dist > 24.0) | (grad > 20.0)
    core[:4, :] = False
    core[-4:, :] = False
    core[:, :4] = False
    core[:, -4:] = False

    struct = ndimage.generate_binary_structure(2, 2)
    fg = ndimage.binary_fill_holes(ndimage.binary_closing(core, structure=struct, iterations=2))
    fg = ndimage.binary_fill_holes(ndimage.binary_erosion(fg, structure=struct, iterations=1))
    return fg


def measure_cutout_metrics(cutouts_path: Path) -> dict:
    im = Image.open(cutouts_path).convert("RGB")
    arr = np.array(im, dtype=np.float32)
    h, w, _ = arr.shape
    fg = _compute_foreground_mask(arr)

    col_fg = fg.sum(axis=0)
    s1 = int(col_fg[int(w * 0.24) : int(w * 0.44)].min())
    s2 = int(col_fg[int(w * 0.56) : int(w * 0.76)].min())
    ys, xs = np.where(fg)
    if len(ys) == 0:
        return {
            "width": w,
            "height": h,
            "split1": 999,
            "split2": 999,
            "top_pct": 0.0,
            "bot_pct": 0.0,
            "left_pct": 0.0,
            "right_pct": 0.0,
        }
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


def normalize_cutout_sheet_columns(cutouts_path: Path) -> bool:
    """Ensure the 3 freestanding items in `cutouts_path` sit cleanly centered in the
    3 columns (`[13.5%, 32.5%]`, `[39.5%, 60.5%]`, `[67.5%, 86.5%]`) on a pure `#FFFFFF`
    canvas with `>= 13%` top/bottom/left/right pure-white margins and `split1 == 0`,
    `split2 == 0`. Also removes any stray floating head sketches or smudges in each column.
    """
    raw_im = Image.open(cutouts_path).convert("RGB")
    arr = np.array(raw_im, dtype=np.float32)
    h, w, _ = arr.shape

    fg = _compute_foreground_mask(arr)
    col_fg = fg.sum(axis=0)

    # Locate the two column valleys between Left/Center and Center/Right
    s1_lo, s1_hi = int(w * 0.24), int(w * 0.44)
    s2_lo, s2_hi = int(w * 0.56), int(w * 0.76)
    s1 = s1_lo + int(np.argmin(col_fg[s1_lo:s1_hi]))
    s2 = s2_lo + int(np.argmin(col_fg[s2_lo:s2_hi]))

    lbl, n_cc = ndimage.label(fg)
    if n_cc < 3:
        return False

    comps = []
    for cid in range(1, n_cc + 1):
        mask_c = lbl == cid
        sz = int(mask_c.sum())
        if sz < 250:
            continue
        ys, xs = np.where(mask_c)
        cx = float(xs.mean())
        comps.append((cx, sz, int(ys.min()), int(ys.max()), mask_c))

    if len(comps) < 3:
        return False

    col_comp_lists: list[list[tuple[int, int, int, np.ndarray]]] = [[], [], []]
    if col_fg[s1] <= 4 and col_fg[s2] <= 4:
        for cx, sz, ymin_c, ymax_c, mask_c in comps:
            if cx < s1:
                col_comp_lists[0].append((sz, ymin_c, ymax_c, mask_c))
            elif cx < s2:
                col_comp_lists[1].append((sz, ymin_c, ymax_c, mask_c))
            else:
                col_comp_lists[2].append((sz, ymin_c, ymax_c, mask_c))
    else:
        anchors = [w * 0.20, w * 0.50, w * 0.80]
        for cx, sz, ymin_c, ymax_c, mask_c in comps:
            best_idx = int(np.argmin([abs(cx - a) for a in anchors]))
            col_comp_lists[best_idx].append((sz, ymin_c, ymax_c, mask_c))

    clusters = [np.zeros((h, w), dtype=bool) for _ in range(3)]
    for idx_col, c_list in enumerate(col_comp_lists):
        if not c_list:
            return False
        c_list.sort(key=lambda t: t[0], reverse=True)
        main_sz, main_ymin, main_ymax, main_mask = c_list[0]
        clusters[idx_col] |= main_mask
        main_h = max(1, main_ymax - main_ymin)
        for sz, ymin_c, ymax_c, mask_c in c_list[1:]:
            # Discard small stray smudges/sketches (< 12% of main component area)
            if sz < 0.12 * main_sz:
                continue
            # Discard disconnected floating head sketches perched above the main component
            if ymax_c < main_ymin + 0.35 * main_h:
                continue
            clusters[idx_col] |= mask_c

    if any(int(c.sum()) < 800 for c in clusters):
        return False

    canvas = Image.new("RGB", (w, h), (255, 255, 255))
    col_bounds = [
        (int(round(w * 0.135)), int(round(w * 0.325))),
        (int(round(w * 0.395)), int(round(w * 0.605))),
        (int(round(w * 0.675)), int(round(w * 0.865))),
    ]
    min_y = int(round(h * 0.135))
    max_y = int(round(h * 0.865))
    max_col_h = max_y - min_y
    struct = ndimage.generate_binary_structure(2, 2)

    for idx_col, mask_col in enumerate(clusters):
        # Softly feather 2.2px outside the component mask onto pure #FFFFFF
        dil = ndimage.binary_dilation(mask_col, structure=struct, iterations=3)
        ys, xs = np.where(dil)
        y0, y1 = max(0, int(ys.min()) - 2), min(h, int(ys.max()) + 3)
        x0, x1 = max(0, int(xs.min()) - 2), min(w, int(xs.max()) + 3)

        sub_rgb = arr[y0:y1, x0:x1].copy()
        sub_mask = mask_col[y0:y1, x0:x1]
        dist_out = ndimage.distance_transform_edt(~sub_mask)
        alpha = np.clip((2.2 - dist_out) / 2.2, 0.0, 1.0)[:, :, None]
        clean_rgb = np.clip(sub_rgb * alpha + 255.0 * (1.0 - alpha), 0, 255).astype(np.uint8)
        crop_im = Image.fromarray(clean_rgb, mode="RGB")

        cw, ch = crop_im.size
        bx0, bx1 = col_bounds[idx_col]
        max_col_w = bx1 - bx0
        scale = min(1.0, max_col_w / float(max(1, cw)), max_col_h / float(max(1, ch)))
        if scale < 0.999:
            cw = max(1, int(round(cw * scale)))
            ch = max(1, int(round(ch * scale)))
            crop_im = crop_im.resize((cw, ch), Image.Resampling.LANCZOS)

        paste_x = (bx0 + bx1 - cw) // 2
        paste_x = max(bx0, min(bx1 - cw, paste_x))

        orig_cy = (y0 + y1) // 2
        paste_y = orig_cy - ch // 2
        paste_y = max(min_y, min(max_y - ch, paste_y))

        canvas.paste(crop_im, (paste_x, paste_y))

    canvas.save(cutouts_path, quality=95)
    return True


def generate_one_image(
    api_key: str,
    prompt: str,
    out_path: Path,
    ref_img_path: Path | None = None,
    force: bool = False,
):
    is_cutouts = out_path.name.endswith("_cutouts.jpg")
    is_bg = out_path.name.endswith("_bg.jpg")
    if not force and out_path.exists() and out_path.stat().st_size > 20_000:
        if is_cutouts:
            normalize_cutout_sheet_columns(out_path)
        elif is_bg:
            strip_outer_border_if_any(out_path)
        print(f"[SKIP] {out_path.name} already exists")
        return out_path

    out_path.parent.mkdir(parents=True, exist_ok=True)
    max_attempts = 4 if is_cutouts else 1
    for attempt in range(1, max_attempts + 1):
        print(f"[GEN 2K] {out_path.name} (attempt {attempt}/{max_attempts}) ...")
        res = call_nano_banana_2k(
            prompt=prompt,
            output_path=out_path,
            api_key=api_key,
            ref_image_path=ref_img_path,
            aspect_ratio="16:9",
            retries=6,
        )
        if is_bg:
            strip_outer_border_if_any(out_path)
            break
        if is_cutouts:
            ok = normalize_cutout_sheet_columns(out_path)
            metrics = measure_cutout_metrics(out_path)
            print(f"[CHECK]  {out_path.name}: {metrics}")
            if (
                ok
                and metrics["split1"] == 0
                and metrics["split2"] == 0
                and metrics["top_pct"] >= 12.0
                and metrics["bot_pct"] >= 12.0
                and metrics["left_pct"] >= 12.0
                and metrics["right_pct"] >= 12.0
            ):
                break
            print(f"[REGEN]  {out_path.name} failed 3-column gate ({metrics}), regenerating...")
        else:
            break

    print(f"[DONE] {out_path.name} ({out_path.stat().st_size // 1024} KB)")
    return res


def sync_shared_room_backgrounds() -> None:
    """Copy canonical `_bg.jpg` files to spreads that share the same room (`same_bg_as`)."""
    for book_id, bspec in POPUP_SPREADS.items():
        for sp in bspec["spreads"]:
            src_idx = sp.get("same_bg_as")
            if src_idx is not None:
                src_bg = POPUP_DIR / f"{book_id}_spread_{src_idx}_bg.jpg"
                dst_bg = POPUP_DIR / f"{book_id}_spread_{sp['idx']}_bg.jpg"
                if src_bg.exists() and src_bg != dst_bg:
                    shutil.copy2(src_bg, dst_bg)
                    print(f"[SYNC-BG] {dst_bg.name} <- {src_bg.name}")


def main():
    parser = argparse.ArgumentParser(description="Generate 2K pop-up book stage backplates and die-cut sheets.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing images.")
    parser.add_argument(
        "--char-sheets",
        action="store_true",
        help="Regenerate the 5 anonymous book-derived character sheets before generating cutouts.",
    )
    parser.add_argument(
        "--cutouts-only",
        action="store_true",
        help="Only generate/update the 15 `_cutouts.jpg` files (preserving existing `_bg.jpg` files).",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        help="Optional filter(s) matching output filename substring, e.g. 04_the_time_machine_spread_1_cutouts",
    )
    args = parser.parse_args()

    # Validate all prompts up front against FORBIDDEN_WORDS
    for book_id, bspec in POPUP_SPREADS.items():
        assert_no_forbidden_words(bspec["char_sheet_prompt"], f"{book_id}_char_sheet")
        assert_no_forbidden_words(bspec["style"], f"{book_id}_style")
        for sp in bspec["spreads"]:
            assert_no_forbidden_words(sp["bg_prompt"], f"{book_id}_spread_{sp['idx']}_bg")
            assert_no_forbidden_words(sp["cutouts_prompt"], f"{book_id}_spread_{sp['idx']}_cutouts")

    api_key = get_api_key()
    POPUP_DIR.mkdir(parents=True, exist_ok=True)

    if args.char_sheets:
        print("Generating 5 anonymous book-derived 2K character reference sheets...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            cs_futs = []
            for book_id, bspec in POPUP_SPREADS.items():
                ref_path = ROOT / bspec["char_sheet"]
                if not args.only or any(tok in ref_path.name for tok in args.only):
                    cs_futs.append(
                        ex.submit(
                            generate_one_image,
                            api_key,
                            bspec["char_sheet_prompt"],
                            ref_path,
                            None,
                            args.force,
                        )
                    )
            for f in concurrent.futures.as_completed(cs_futs):
                f.result()

    jobs = []
    for book_id, bspec in POPUP_SPREADS.items():
        style = bspec["style"]
        ref_path = ROOT / bspec["char_sheet"]
        for sp in bspec["spreads"]:
            idx = sp["idx"]
            bg_out = POPUP_DIR / f"{book_id}_spread_{idx}_bg.jpg"
            cut_out = POPUP_DIR / f"{book_id}_spread_{idx}_cutouts.jpg"
            full_bg_prompt = f"{style}\n\n{sp['bg_prompt']}"
            full_cut_prompt = f"{style}\n\n{sp['cutouts_prompt']}"

            if not args.cutouts_only and sp.get("same_bg_as") is None:
                if not args.only or any(tok in bg_out.name for tok in args.only):
                    jobs.append((full_bg_prompt, bg_out, None, args.force))
            if not args.only or any(tok in cut_out.name for tok in args.only):
                jobs.append((full_cut_prompt, cut_out, ref_path, args.force))

    print(f"Generating {len(jobs)} 2K pop-up assets...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        futs = [ex.submit(generate_one_image, api_key, p, o, r, f) for (p, o, r, f) in jobs]
        for f in concurrent.futures.as_completed(futs):
            f.result()

    sync_shared_room_backgrounds()
    print(f"All {len(jobs)} requested 2K pop-up assets generated and shared room backplates synced!")


if __name__ == "__main__":
    main()
