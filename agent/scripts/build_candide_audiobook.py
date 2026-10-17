#!/usr/bin/env python3
"""Build the complete, unabridged multi-voice audiobook for the first ~50 pages
(Chapters I-XII, pp. 1-53) of Voltaire's Candide in English:
1. Parses texts/06_candide_ch01_12.txt into Chapters I..XII and assigns every
   paragraph to its exact character voice (voltaire_narrator, candide, pangloss,
   cunegonde, old_woman, james_anabaptist).
2. Splits any paragraph > 135 words at sentence boundaries so every turn is crisp
   for TTS and fits generously on its right-hand literary folio page.
3. Synthesizes all turns via gemini-3.8-flash-tts using the custom voices in
   voices/voices_manifest.json.
4. Generates 4 period-appropriate 18th-century Baroque/Rococo chamber scores via
   Lyria 3.5 (lyria-3.5) and mixes them at the reduced -27.5 dBFS / -39.2 dBFS
   level with raised-cosine fade-ins and fade-outs at structural scene transitions.
"""

import base64
import concurrent.futures
import json
import math
import os
import re
import time
import urllib.request
import wave
from pathlib import Path
import numpy as np

from generate_and_mix_music import (
    decode_audio_to_stereo_float,
    fit_music_length_equal_power,
    generate_lyria_track,
    raised_cosine_window,
)

ROOT = Path(__file__).resolve().parent.parent
TEXT_PATH = ROOT / "texts" / "06_candide_ch01_12.txt"
VOICES_MANIFEST_PATH = ROOT / "voices" / "voices_manifest.json"
AUDIO_DIR = ROOT / "audio"
TURNS_DIR = AUDIO_DIR / "candide_turns"
MUSIC_DIR = ROOT / "music"
CANDIDE_TIMELINE_PATH = AUDIO_DIR / "candide_timeline_manifest.json"
SAMPLE_RATE = 24000

CANDIDE_VOICES = {
    "voltaire_narrator": {
        "voice_id": "Orus",
        "persona_style": (
            "Cultured, urbane British male literary narrator in his late 40s, crisp velvet"
            " Received Pronunciation baritone, dry Enlightenment deadpan wit and effortless"
            " narrative clarity"
        ),
    },
    "candide": {
        "voice_id": "Puck",
        "persona_style": (
            "Earnest, gentle-hearted, sincere young British man in his early 20s, clear warm"
            " Received Pronunciation tenor, polite and open-hearted full-voiced diction"
        ),
    },
    "pangloss": {
        "voice_id": "Charon",
        "persona_style": (
            "Older, pedantic, unshakably cheerful 18th-century British academic philosopher"
            " in his 60s, resonant theatrical Received Pronunciation baritone, pompous"
            " scholarly relish"
        ),
    },
    "cunegonde": {
        "voice_id": "Kore",
        "persona_style": (
            "Spirited, poised young aristocratic noblewoman, clear expressive British"
            " Received Pronunciation voice, vivid dramatic candour"
        ),
    },
    "old_woman": {
        "voice_id": "Callirrhoe",
        "persona_style": (
            "Seasoned, resilient older European woman in her 60s, warm low contralto voice,"
            " unsentimental wisdom and noble dignity"
        ),
    },
    "james_anabaptist": {
        "voice_id": "Fenrir",
        "persona_style": (
            "Grounded, resonant mature British baritone in his 40s, clear full-voiced"
            " diction and strong dramatic presence"
        ),
    },
}

# Explicit paragraph speaker map: (RomanChapter, para_idx) -> (speaker_key, display_label, style_cue)
PARA_SPEAKER_MAP = {
    # Chapter I
    ("I", 4): ("pangloss", "DOCTOR PANGLOSS", "pedantic, cheerful 18th-century philosophical certainty"),
    # Chapter II
    ("II", 1): ("james_anabaptist", "BULGARIAN RECRUITER", "boisterous, calculating military recruiter"),
    ("II", 3): ("candide", "CANDIDE", "modest, polite, earnest young gentleman"),
    ("II", 4): ("james_anabaptist", "BULGARIAN RECRUITER", "flattering, hearty tavern conviviality"),
    ("II", 5): ("candide", "CANDIDE", "polite, innocent sincerity"),
    ("II", 6): ("james_anabaptist", "BULGARIAN RECRUITER", "warm, persuasive tavern camaraderie"),
    ("II", 7): ("candide", "CANDIDE", "grateful, wide-eyed optimism"),
    ("II", 9): ("james_anabaptist", "BULGARIAN RECRUITER", "demanding, theatrical warmth"),
    ("II", 10): ("candide", "CANDIDE", "tender, innocent romantic devotion"),
    ("II", 11): ("james_anabaptist", "BULGARIAN RECRUITER", "blunt military insistence"),
    ("II", 12): ("candide", "CANDIDE", "honest, simple candour"),
    ("II", 13): ("james_anabaptist", "BULGARIAN RECRUITER", "boisterous toast"),
    ("II", 14): ("candide", "CANDIDE", "obliging, cheerful politeness"),
    ("II", 15): ("james_anabaptist", "BULGARIAN RECRUITER", "triumphant, ironic military proclamation"),
    # Chapter III
    ("III", 5): ("james_anabaptist", "DUTCH ORATOR", "stern, self-righteous inquisitorial gravity"),
    ("III", 6): ("candide", "CANDIDE", "modest, earnest philosophical humility"),
    ("III", 7): ("james_anabaptist", "DUTCH ORATOR", "harsh, dogmatic zeal"),
    ("III", 8): ("candide", "CANDIDE", "weary, honest simplicity"),
    ("III", 9): ("james_anabaptist", "DUTCH ORATOR", "furious, indignant dismissal"),
    ("III", 12): ("candide", "CANDIDE", "touched, grateful optimism"),
    # Chapter IV
    ("IV", 1): ("pangloss", "DOCTOR PANGLOSS", "sorrowful, pathetic yet dramatic recognition"),
    ("IV", 2): ("candide", "CANDIDE", "shocked, compassionate dismay"),
    ("IV", 3): ("pangloss", "DOCTOR PANGLOSS", "weary, solemn, sorrowful confession"),
    ("IV", 5): ("candide", "CANDIDE", "anxious, urgent inquiry"),
    ("IV", 6): ("pangloss", "DOCTOR PANGLOSS", "solemn, tragic finality"),
    ("IV", 8): ("candide", "CANDIDE", "heartbroken, sorrowful grief"),
    ("IV", 9): ("pangloss", "DOCTOR PANGLOSS", "matter-of-fact tragic recitation"),
    ("IV", 11): ("pangloss", "DOCTOR PANGLOSS", "lyrical, philosophical reflection"),
    ("IV", 12): ("candide", "CANDIDE", "wistful, bewildered innocence"),
    ("IV", 13): ("pangloss", "DOCTOR PANGLOSS", "pedantic, clinical genealogical lecture"),
    ("IV", 14): ("candide", "CANDIDE", "astonished exclamation"),
    ("IV", 15): ("pangloss", "DOCTOR PANGLOSS", "triumphant, unshakable philosophical optimism"),
    ("IV", 16): ("candide", "CANDIDE", "earnest, practical concern"),
    ("IV", 17): ("pangloss", "DOCTOR PANGLOSS", "melancholy, penniless resignation"),
    ("IV", 19): ("james_anabaptist", "JAMES THE ANABAPTIST", "calm, humane, sober moral wisdom"),
    ("IV", 20): ("pangloss", "DOCTOR PANGLOSS", "confident, dogmatic rebuttal"),
    # Chapter V
    ("V", 2): ("pangloss", "DOCTOR PANGLOSS", "curious, academic detachment amid catastrophe"),
    ("V", 3): ("candide", "CANDIDE", "alarmed exclamation"),
    ("V", 5): ("pangloss", "DOCTOR PANGLOSS", "polite, pedantic scolding"),
    ("V", 6): ("james_anabaptist", "BATAVIAN SAILOR", "bold, defiant maritime brusqueness"),
    ("V", 8): ("candide", "CANDIDE", "urgent, pleading anguish"),
    ("V", 9): ("pangloss", "DOCTOR PANGLOSS", "enthusiastic geological lecturing, ignoring the plea"),
    ("V", 10): ("candide", "CANDIDE", "desperate, polite pleading"),
    ("V", 11): ("pangloss", "DOCTOR PANGLOSS", "indignant academic insistence"),
    ("V", 13): ("pangloss", "DOCTOR PANGLOSS", "serene, consoling philosophical lecture"),
    ("V", 15): ("james_anabaptist", "FAMILIAR OF THE INQUISITION", "smooth, polite, trap-setting inquisitorial courtesy"),
    ("V", 16): ("pangloss", "DOCTOR PANGLOSS", "elaborately polite, oblivious academic explanation"),
    ("V", 17): ("james_anabaptist", "FAMILIAR OF THE INQUISITION", "measured, pointed interrogation"),
    ("V", 18): ("pangloss", "DOCTOR PANGLOSS", "eager metaphysical pedantry"),
    # Chapter VI
    ("VI", 3): ("candide", "CANDIDE", "bewildered, anguished inner reflection"),
    ("VI", 5): ("old_woman", "THE OLD WOMAN", "low, gentle, mysterious reassurance"),
    # Chapter VII
    ("VII", 1): ("old_woman", "THE OLD WOMAN", "warm, practical, maternal kindness"),
    ("VII", 3): ("old_woman", "THE OLD WOMAN", "unsentimental, brisk reassurance"),
    ("VII", 5): ("candide", "CANDIDE", "amazed, grateful wonder"),
    ("VII", 7): ("old_woman", "THE OLD WOMAN", "low, urgent, confidential gravity"),
    ("VII", 10): ("old_woman", "THE OLD WOMAN", "measured, dramatic invitation"),
    ("VII", 12): ("candide", "CANDIDE", "overwhelmed joy and astonished disbelief"),
    ("VII", 13): ("cunegonde", "LADY CUNÉGONDE", "poised, matter-of-fact aristocratic candour"),
    ("VII", 14): ("candide", "CANDIDE", "gentle, anxious question"),
    ("VII", 15): ("cunegonde", "LADY CUNÉGONDE", "sorrowful, poignant reflection"),
    ("VII", 16): ("candide", "CANDIDE", "gentle, sympathetic question"),
    ("VII", 17): ("cunegonde", "LADY CUNÉGONDE", "solemn, mournful confirmation"),
    ("VII", 18): ("candide", "CANDIDE", "eager, rapid curiosity"),
    ("VII", 19): ("cunegonde", "LADY CUNÉGONDE", "warm, affectionate invitation"),
    # Chapter VIII
    ("VIII", 0): ("cunegonde", "LADY CUNÉGONDE", "vivid, dramatic, composed first-person storytelling"),
    ("VIII", 1): ("candide", "CANDIDE", "earnest, innocent interjection"),
    ("VIII", 2): ("cunegonde", "LADY CUNÉGONDE", "gentle, amused poise"),
    ("VIII", 3): ("candide", "CANDIDE", "eager, attentive reply"),
    ("VIII", 5): ("cunegonde", "LADY CUNÉGONDE", "expressive, candid aristocratic narrative"),
    ("VIII", 6): ("cunegonde", "LADY CUNÉGONDE", "wry, poised worldly storytelling"),
    ("VIII", 7): ("cunegonde", "LADY CUNÉGONDE", "dramatic, suspenseful recollection"),
    ("VIII", 8): ("cunegonde", "LADY CUNÉGONDE", "tender, emotional culmination"),
    # Chapter IX
    ("IX", 1): ("james_anabaptist", "DON ISSACHAR", "furious, jealous outburst"),
    ("IX", 3): ("cunegonde", "LADY CUNÉGONDE", "alarmed, urgent distress"),
    ("IX", 4): ("candide", "CANDIDE", "earnest, bewildered calm"),
    ("IX", 7): ("candide", "CANDIDE", "rapid, earnest logical deduction"),
    ("IX", 8): ("cunegonde", "LADY CUNÉGONDE", "astonished, theatrical exclamation"),
    ("IX", 9): ("candide", "CANDIDE", "gentle, bewildered apology"),
    ("IX", 11): ("old_woman", "THE OLD WOMAN", "brisk, commanding, practical urgency"),
    # Chapter X
    ("X", 0): ("cunegonde", "LADY CUNÉGONDE", "sorrowful, distressed lament"),
    ("X", 1): ("old_woman", "THE OLD WOMAN", "shrewd, observant worldly suspicion"),
    ("X", 2): ("candide", "CANDIDE", "earnest philosophical consolation"),
    ("X", 3): ("cunegonde", "LADY CUNÉGONDE", "blunt, despairing reply"),
    ("X", 4): ("candide", "CANDIDE", "helpless, earnest question"),
    ("X", 5): ("old_woman", "THE OLD WOMAN", "resolute, practical resourcefulness"),
    ("X", 8): ("candide", "CANDIDE", "hopeful, wide-eyed optimism"),
    ("X", 9): ("cunegonde", "LADY CUNÉGONDE", "tender yet shaken honesty"),
    ("X", 10): ("candide", "CANDIDE", "reassuring, gentle conviction"),
    ("X", 11): ("cunegonde", "LADY CUNÉGONDE", "weary, guarded reflection"),
    ("X", 12): ("old_woman", "THE OLD WOMAN", "dry, authoritative, world-weary gravity"),
    ("X", 14): ("cunegonde", "LADY CUNÉGONDE", "incredulous, spirited challenge"),
    ("X", 15): ("old_woman", "THE OLD WOMAN", "calm, dignified, enigmatic authority"),
    # Chapter XI
    ("XI", 0): ("old_woman", "THE OLD WOMAN", "noble, nostalgic, unhurried reminiscence"),
    ("XI", 1): ("old_woman", "THE OLD WOMAN", "poignant, tragic dramatic recollection"),
    ("XI", 2): ("old_woman", "THE OLD WOMAN", "stark, unsentimental storytelling"),
    ("XI", 3): ("old_woman", "THE OLD WOMAN", "dry, composed irony"),
    ("XI", 4): ("old_woman", "THE OLD WOMAN", "grim, measured historical narrative"),
    ("XI", 5): ("old_woman", "THE OLD WOMAN", "intense, vivid, unsparing dramatic narration"),
    ("XI", 6): ("old_woman", "THE OLD WOMAN", "weary, solemn dignity"),
    # Chapter XII
    ("XII", 0): ("old_woman", "THE OLD WOMAN", "astonished, reflective storytelling"),
    ("XII", 1): ("james_anabaptist", "NEAPOLITAN CHAPELMASTER", "melancholy, expressive Italian courtier"),
    ("XII", 2): ("old_woman", "THE OLD WOMAN", "startled exclamation"),
    ("XII", 3): ("james_anabaptist", "NEAPOLITAN CHAPELMASTER", "sorrowful, tender recognition"),
    ("XII", 4): ("old_woman", "THE OLD WOMAN", "sorrowful, stark reply"),
    ("XII", 5): ("old_woman", "THE OLD WOMAN", "measured, unsentimental narrative"),
    ("XII", 6): ("james_anabaptist", "NEAPOLITAN CHAPELMASTER", "compassionate, solemn promise"),
    ("XII", 7): ("old_woman", "THE OLD WOMAN", "wry, fatalistic transition"),
    ("XII", 8): ("cunegonde", "LADY CUNÉGONDE", "earnest, wide-eyed reply"),
    ("XII", 9): ("old_woman", "THE OLD WOMAN", "grave, authoritative comparison"),
    ("XII", 10): ("old_woman", "THE OLD WOMAN", "unhurried, resilient chronicle"),
    ("XII", 11): ("old_woman", "THE OLD WOMAN", "stark, dramatic siege narrative"),
    ("XII", 12): ("old_woman", "THE OLD WOMAN", "dry, deadpan ironic setup"),
    ("XII", 13): ("james_anabaptist", "THE IMAN OF AZOV", "eloquent, solemn, absurdly persuasive sermon"),
    ("XII", 14): ("old_woman", "THE OLD WOMAN", "dry, matter-of-fact stoicism"),
    ("XII", 15): ("old_woman", "THE OLD WOMAN", "measured, worldly narrative"),
    ("XII", 16): ("old_woman", "THE OLD WOMAN", "resilient, unsentimental life chronicle"),
    ("XII", 17): ("old_woman", "THE OLD WOMAN", "profound, philosophical challenge and conclusion"),
}

PARTS_SPEC = [
    {
        "id": "06_candide_part1_ch01_03",
        "roman": "VI · PART I",
        "title": "Candide: Part I (Chapters I–III)",
        "author": "Voltaire",
        "year": "1759",
        "genre": "Enlightenment Philosophical Satire",
        "chapter_title": "Chapters I–III (Pages 1–12)",
        "setting": "Westphalia, Bulgaria & Holland",
        "chapters": ["I", "II", "III"],
        "char_sheet_image": "illustrations/06_candide_char_sheet.jpg",
        "palette": {
            "paper": "#F6F1E6",
            "card": "#EFE7D6",
            "ink": "#231E1A",
            "muted": "#6E6254",
            "accent": "#7A2E2E",
            "rule": "#CBBFA8",
        },
        "scenes": [
            {
                "scene_idx": 0,
                "image_file": "illustrations/06_candide_p1_scene_1.jpg",
                "caption": "Chapter I · Doctor Pangloss & The Best of Possible Worlds",
            },
            {
                "scene_idx": 1,
                "image_file": "illustrations/06_candide_p1_scene_2.jpg",
                "caption": "Chapter I · Behind the Folding Screen at Thunder-ten-Tronckh",
            },
            {
                "scene_idx": 2,
                "image_file": "illustrations/06_candide_p1_scene_3.jpg",
                "caption": "Chapter II · Candide Among the Bulgarian Recruiters",
            },
            {
                "scene_idx": 3,
                "image_file": "illustrations/06_candide_p1_scene_4.jpg",
                "caption": "Chapter III · Escape to Holland & James the Anabaptist",
            },
        ],
        "lyria_prompt": (
            "Subtle, restrained 18th-century French Baroque and Rococo chamber underscore"
            " for an Enlightenment literary audiobook. Delicate solo harpsichord, warm"
            " baroque wooden transverse flute, and muted chamber cello in D major. Light,"
            " dry, witty 1759 salon elegance, sparse and minimal, purely instrumental,"
            " no vocals, no percussion."
        ),
    },
    {
        "id": "06_candide_part2_ch04_06",
        "roman": "VI · PART II",
        "title": "Candide: Part II (Chapters IV–VI)",
        "author": "Voltaire",
        "year": "1759",
        "genre": "Enlightenment Philosophical Satire",
        "chapter_title": "Chapters IV–VI (Pages 13–25)",
        "setting": "Holland & The Lisbon Earthquake",
        "chapters": ["IV", "V", "VI"],
        "char_sheet_image": "illustrations/06_candide_char_sheet.jpg",
        "palette": {
            "paper": "#F5EFE4",
            "card": "#EDE4D3",
            "ink": "#221D1A",
            "muted": "#6C6052",
            "accent": "#7A2E2E",
            "rule": "#C8BCA6",
        },
        "scenes": [
            {
                "scene_idx": 0,
                "image_file": "illustrations/06_candide_p2_scene_1.jpg",
                "caption": "Chapter IV · Reunion with Doctor Pangloss in Holland",
            },
            {
                "scene_idx": 1,
                "image_file": "illustrations/06_candide_p2_scene_2.jpg",
                "caption": "Chapter V · The Tempest & Shipwreck off Lisbon",
            },
            {
                "scene_idx": 2,
                "image_file": "illustrations/06_candide_p2_scene_3.jpg",
                "caption": "Chapter V · Sufficient Reason Amid the Lisbon Ruins",
            },
            {
                "scene_idx": 3,
                "image_file": "illustrations/06_candide_p2_scene_4.jpg",
                "caption": "Chapter VI · The Lisbon Auto-da-fé & The Old Woman",
            },
        ],
        "lyria_prompt": (
            "Subtle, contemplative 18th-century Baroque chamber underscore in D minor for"
            " Voltaire's Candide in Lisbon. Warm solo viola da gamba, Plucked baroque"
            " theorbo lute, and sparse muted harpsichord chords. Restrained, solemn,"
            " philosophical intimacy, purely instrumental, no vocals, no percussion."
        ),
    },
    {
        "id": "06_candide_part3_ch07_10",
        "roman": "VI · PART III",
        "title": "Candide: Part III (Chapters VII–X)",
        "author": "Voltaire",
        "year": "1759",
        "genre": "Enlightenment Philosophical Satire",
        "chapter_title": "Chapters VII–X (Pages 26–41)",
        "setting": "Lisbon, Avacena & Cadiz",
        "chapters": ["VII", "VIII", "IX", "X"],
        "char_sheet_image": "illustrations/06_candide_char_sheet.jpg",
        "palette": {
            "paper": "#F6F1E6",
            "card": "#EFE7D6",
            "ink": "#231E1A",
            "muted": "#6E6254",
            "accent": "#7A2E2E",
            "rule": "#CBBFA8",
        },
        "scenes": [
            {
                "scene_idx": 0,
                "image_file": "illustrations/06_candide_p3_scene_1.jpg",
                "caption": "Chapter VII · The Unveiling of Lady Cunégonde",
            },
            {
                "scene_idx": 1,
                "image_file": "illustrations/06_candide_p3_scene_2.jpg",
                "caption": "Chapter VIII · The History of Cunégonde",
            },
            {
                "scene_idx": 2,
                "image_file": "illustrations/06_candide_p3_scene_3.jpg",
                "caption": "Chapter IX · Night Flight from Lisbon on Andalusian Horses",
            },
            {
                "scene_idx": 3,
                "image_file": "illustrations/06_candide_p3_scene_4.jpg",
                "caption": "Chapter X · Across the Mountains to Cadiz",
            },
        ],
        "lyria_prompt": (
            "Subtle, graceful 18th-century Iberian Baroque chamber underscore in G minor"
            " for an Enlightenment literary audiobook. Delicate baroque guitar, sparse"
            " harpsichord, and warm muted solo cello. Restrained nocturnal romantic"
            " elegance, purely instrumental, no vocals, no drums."
        ),
    },
    {
        "id": "06_candide_part4_ch11_12",
        "roman": "VI · PART IV",
        "title": "Candide: Part IV (Chapters XI–XII)",
        "author": "Voltaire",
        "year": "1759",
        "genre": "Enlightenment Philosophical Satire",
        "chapter_title": "Chapters XI–XII (Pages 42–53)",
        "setting": "The Atlantic Voyage & Mediterranean Memories",
        "chapters": ["XI", "XII"],
        "char_sheet_image": "illustrations/06_candide_char_sheet.jpg",
        "palette": {
            "paper": "#F6F1E6",
            "card": "#EFE7D6",
            "ink": "#231E1A",
            "muted": "#6E6254",
            "accent": "#7A2E2E",
            "rule": "#CBBFA8",
        },
        "scenes": [
            {
                "scene_idx": 0,
                "image_file": "illustrations/06_candide_p4_scene_1.jpg",
                "caption": "Chapter XI · The Old Woman's Tale Aboard Ship",
            },
            {
                "scene_idx": 1,
                "image_file": "illustrations/06_candide_p4_scene_2.jpg",
                "caption": "Chapter XI · The Galley off the Coast of Gaeta",
            },
            {
                "scene_idx": 2,
                "image_file": "illustrations/06_candide_p4_scene_3.jpg",
                "caption": "Chapter XII · Beneath the Mediterranean Orange Grove",
            },
            {
                "scene_idx": 3,
                "image_file": "illustrations/06_candide_p4_scene_4.jpg",
                "caption": "Chapter XII · Philosophical Reflections on the Atlantic",
            },
        ],
        "lyria_prompt": (
            "Subtle, nostalgic 18th-century Italian Baroque chamber underscore in A minor"
            " for an Enlightenment literary audiobook. Delicate archlute, warm solo cello,"
            " and soft harpsichord arpeggios evoking a calm ocean voyage and distant"
            " memories. Sparse, purely instrumental, no vocals, no percussion."
        ),
    },
]


def get_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key.startswith("AQ."):
        return key
    profile = Path.home() / ".profile"
    if profile.exists():
        for line in profile.read_text().splitlines():
            if line.strip().startswith("export GEMINI_API_KEY="):
                return line.strip().split("=", 1)[1].strip()
    if key:
        return key
    raise RuntimeError("GEMINI_API_KEY not found")


def split_long_paragraph(text: str, max_words: int = 120) -> list[str]:
    """Split any paragraph exceeding `max_words` at sentence boundaries so each
    turn fits comfortably on a right-hand literary folio page.
    """
    words = text.split()
    if len(words) <= max_words:
        return [text]

    # Split into sentences keeping punctuation attached
    sents = re.split(r'(?<=[.!?])\s+(?=[A-Z"\'“‘])', text)
    if len(sents) <= 1:
        mid = len(words) // 2
        return [" ".join(words[:mid]), " ".join(words[mid:])]

    chunks = []
    cur = []
    cur_w = 0
    for s in sents:
        sw = len(s.split())
        if cur and cur_w + sw > max_words:
            chunks.append(" ".join(cur))
            cur = [s]
            cur_w = sw
        else:
            cur.append(s)
            cur_w += sw
    if cur:
        chunks.append(" ".join(cur))
    return chunks


def assign_scene_idx(part_id: str, rom: str, para_idx: int) -> int:
    """Map (part_id, chapter_roman, para_idx) to one of the 4 scenes (0..3) in that Part."""
    if part_id == "06_candide_part1_ch01_03":
        if rom == "I":
            return 0 if para_idx <= 4 else 1
        elif rom == "II":
            return 2
        else:
            return 3
    elif part_id == "06_candide_part2_ch04_06":
        if rom == "IV":
            return 0
        elif rom == "V":
            return 1 if para_idx <= 1 else 2
        else:
            return 3
    elif part_id == "06_candide_part3_ch07_10":
        if rom == "VII":
            return 0
        elif rom == "VIII":
            return 1
        elif rom == "IX":
            return 2
        else:
            return 3
    elif part_id == "06_candide_part4_ch11_12":
        if rom == "XI":
            return 0 if para_idx <= 1 else 1
        else:
            return 2 if para_idx <= 7 else 3
    return 0


def parse_chapters_into_parts() -> list[dict]:
    clean = TEXT_PATH.read_text()
    ch_splits = re.split(r"(?m)^(?=(?:I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII)\s*$)", clean)
    chapters_map = {}
    for ch in ch_splits:
        if not ch.strip():
            continue
        paras = [
            re.sub(r"\s+", " ", p.strip()).replace("_", "")
            for p in re.split(r"\n\s*\n", ch.strip())
            if p.strip()
        ]
        rom = paras[0]
        ch_title = paras[1]
        body_paras = paras[2:]
        chapters_map[rom] = (ch_title, body_paras)

    parts_out = []
    global_turn_counter = 0

    for p_spec in PARTS_SPEC:
        part_id = p_spec["id"]
        raw_items = []
        for rom in p_spec["chapters"]:
            ch_title, body_paras = chapters_map[rom]
            for idx, p_text in enumerate(body_paras):
                spk_key, spk_label, style_cue = PARA_SPEAKER_MAP.get(
                    (rom, idx),
                    ("voltaire_narrator", "NARRATOR", "dry, urbane 18th-century Enlightenment wit and clear literary pacing"),
                )
                is_dialogue = spk_key != "voltaire_narrator"
                s_idx = assign_scene_idx(part_id, rom, idx)
                sub_texts = split_long_paragraph(p_text, max_words=115)
                for st in sub_texts:
                    raw_items.append({
                        "chapter_roman": rom,
                        "chapter_heading": f"CHAPTER {rom}",
                        "scene_idx": s_idx,
                        "speaker_key": spk_key,
                        "speaker_label": spk_label,
                        "is_dialogue": is_dialogue,
                        "style_cue": style_cue,
                        "display_text": st,
                    })

        # Merge consecutive very short narrative turns (< 45 words) within the same scene & chapter
        merged_turns = []
        for item in raw_items:
            if (
                merged_turns
                and not item["is_dialogue"]
                and not merged_turns[-1]["is_dialogue"]
                and merged_turns[-1]["scene_idx"] == item["scene_idx"]
                and merged_turns[-1]["chapter_roman"] == item["chapter_roman"]
                and len(merged_turns[-1]["display_text"].split()) + len(item["display_text"].split()) <= 105
            ):
                merged_turns[-1]["display_text"] += " " + item["display_text"]
            else:
                merged_turns.append(item)

        # Assign folio pages (`page_idx`) within each scene so each right-hand page
        # holds at most ~135 words and at most 4 turns (guaranteed generous typography!)
        page_idx = 0
        page_words = 0
        page_turns = 0
        prev_scene = None
        prev_chap = None

        part_turns = []
        for local_idx, trn in enumerate(merged_turns):
            w_cnt = len(trn["display_text"].split())
            if (
                prev_scene is not None
                and (
                    trn["scene_idx"] != prev_scene
                    or trn["chapter_roman"] != prev_chap
                    or page_words + w_cnt > 135
                    or page_turns >= 4
                )
            ):
                page_idx += 1
                page_words = 0
                page_turns = 0

            trn["turn_idx"] = local_idx
            trn["global_turn_idx"] = global_turn_counter
            trn["page_idx"] = page_idx
            trn["tts_text"] = trn["display_text"]
            part_turns.append(trn)

            page_words += w_cnt
            page_turns += 1
            prev_scene = trn["scene_idx"]
            prev_chap = trn["chapter_roman"]
            global_turn_counter += 1

        p_copy = dict(p_spec)
        p_copy["turns"] = part_turns
        parts_out.append(p_copy)
        print(
            f"[PARSED] {part_id}: {len(part_turns)} turns across {page_idx + 1} folio pages"
        )

    return parts_out


from voice_mastering import warm_master_voice_turn


def _call_tts_raw_wav(
    text: str, full_style: str, voice_id: str, api_key: str, retries: int = 6
) -> bytes:
    url = "https://generativelanguage.googleapis.com/v1beta/interactions"
    clean_style = re.sub(r"\s+in (?:his|her) (?:early |late )?\d+s,?", "", full_style)
    for attempt in range(1, retries + 1):
        if attempt == 1:
            annotation = {"type": "speech_metadata", "style": full_style}
        elif attempt == 2:
            annotation = {"type": "speech_metadata", "style": clean_style}
        else:
            annotation = {"type": "speech_metadata"}
        payload = {
            "model": "gemini-3.8-flash-tts",
            "input": [
                {
                    "type": "user_input",
                    "content": [
                        {
                            "type": "text",
                            "text": text,
                            "annotations": [annotation],
                        }
                    ],
                }
            ],
            "response_format": {
                "type": "audio",
                "mime_type": "audio/wav",
                "sample_rate": SAMPLE_RATE,
            },
            "generation_config": {
                "speech_config": [
                    {"voice": voice_id},
                ]
            },
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "x-goog-api-key": api_key,
                    "Content-Type": "application/json",
                    "Api-Revision": "2026-05-20",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            for step in data.get("steps", []):
                for block in step.get("content", []):
                    if block.get("type") == "audio" and block.get("data"):
                        return base64.b64decode(block["data"])
            raise RuntimeError(f"No audio block returned: {json.dumps(data)[:200]}")
        except Exception as e:
            if attempt == retries:
                raise
            time.sleep(1.5 * attempt)
    raise RuntimeError("Unreachable")


def _raw_wav_to_pcm16(raw_bytes: bytes) -> np.ndarray:
    if raw_bytes[:4] == b"RIFF":
        import io
        with wave.open(io.BytesIO(raw_bytes), "rb") as wf:
            return np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
    return np.frombuffer(raw_bytes, dtype=np.int16)


def synthesize_turn(
    turn: dict, api_key: str, retries: int = 6
) -> Path:
    TURNS_DIR.mkdir(parents=True, exist_ok=True)
    g_idx = turn["global_turn_idx"]
    spk = turn["speaker_key"]
    voice_cfg = CANDIDE_VOICES[spk]
    voice_id = voice_cfg["voice_id"]
    persona_style = voice_cfg["persona_style"]
    turn_style = turn.get("style_cue", "").strip()
    full_style = f"{persona_style}; {turn_style}" if turn_style else persona_style

    out_wav = TURNS_DIR / f"candide_turn_{g_idx:03d}_{spk}.wav"
    if out_wav.exists() and out_wav.stat().st_size > 4000:
        return out_wav

    try:
        raw = _call_tts_raw_wav(
            turn["tts_text"], full_style, voice_id, api_key, retries=retries
        )
        pcm16_in = _raw_wav_to_pcm16(raw)
    except Exception as e:
        print(f"[SENTENCE FALLBACK] turn {g_idx} ({e}); splitting into sentences...")
        sents = [s.strip() for s in re.split(r"(?<=[.!?;:])\s+", turn["tts_text"]) if s.strip()]
        pcm_parts = []
        pause = np.zeros(int(0.18 * SAMPLE_RATE), dtype=np.int16)
        clause_pause = np.zeros(int(0.11 * SAMPLE_RATE), dtype=np.int16)

        def _synth_clause(txt: str) -> list[np.ndarray]:
            try:
                raw_c = _call_tts_raw_wav(txt, full_style, voice_id, api_key, retries=3)
                return [_raw_wav_to_pcm16(raw_c)]
            except Exception:
                clauses = [c.strip() for c in txt.split(",") if c.strip()]
                if len(clauses) <= 1:
                    raise
                mid = max(1, len(clauses) // 2)
                c1 = ", ".join(clauses[:mid]) + ","
                c2 = ", ".join(clauses[mid:])
                out = []
                out.extend(_synth_clause(c1))
                out.append(clause_pause)
                out.extend(_synth_clause(c2))
                return out

        for s in sents:
            pcm_parts.extend(_synth_clause(s))
            pcm_parts.append(pause)
        pcm16_in = np.concatenate(pcm_parts[:-1]) if pcm_parts else np.zeros(2400, dtype=np.int16)

    samples = pcm16_in.astype(np.float32) / 32768.0
    samples = warm_master_voice_turn(samples, sr=24000)
    pcm16_out = (np.clip(samples, -0.98, 0.98) * 32767.0).astype(np.int16)

    out_wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm16_out.tobytes())
    return out_wav


synthesize_turn_wav = synthesize_turn


def load_and_clean_turn_pcm(wav_path: Path) -> np.ndarray:
    raw_bytes = wav_path.read_bytes()
    if raw_bytes[:4] == b"RIFF":
        with wave.open(str(wav_path), "rb") as wf:
            raw = wf.readframes(wf.getnframes())
            arr = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    else:
        arr = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0

    # Trim leading/trailing silence below -48 dBFS (0.004)
    idx = np.where(np.abs(arr) > 0.004)[0]
    if len(idx) > 0:
        pad = int(0.025 * SAMPLE_RATE)
        i0 = max(0, int(idx[0]) - pad)
        i1 = min(len(arr), int(idx[-1]) + pad)
        arr = arr[i0:i1]

    # Transparent studio voice mastering + RMS leveling
    arr = warm_master_voice_turn(arr, sr=24000)

    # 15ms cosine fade-in and 25ms cosine fade-out
    f_in = min(int(0.015 * SAMPLE_RATE), len(arr) // 4)
    f_out = min(int(0.025 * SAMPLE_RATE), len(arr) // 4)
    if f_in > 0:
        arr[:f_in] *= np.sin(np.linspace(0.0, np.pi / 2.0, f_in, dtype=np.float32))
    if f_out > 0:
        arr[-f_out:] *= np.cos(np.linspace(0.0, np.pi / 2.0, f_out, dtype=np.float32))

    return np.clip(arr, -0.95, 0.95)


def assemble_part_timeline_and_master(part: dict) -> dict:
    title_hold_sec = 2.6
    outro_hold_sec = 1.6

    chunks = [np.zeros(int(title_hold_sec * SAMPLE_RATE), dtype=np.float32)]
    cursor_sec = title_hold_sec

    turns = part["turns"]
    for i, trn in enumerate(turns):
        wav_path = TURNS_DIR / f"candide_turn_{trn['global_turn_idx']:03d}_{trn['speaker_key']}.wav"
        pcm = load_and_clean_turn_pcm(wav_path)
        dur = len(pcm) / float(SAMPLE_RATE)

        trn["start_sec"] = round(cursor_sec, 4)
        trn["duration_sec"] = round(dur, 4)
        trn["end_sec"] = round(cursor_sec + dur, 4)
        trn["wav_file"] = str(wav_path.relative_to(ROOT))

        chunks.append(pcm)
        cursor_sec += dur

        if i < len(turns) - 1:
            nxt = turns[i + 1]
            if nxt["scene_idx"] != trn["scene_idx"] or nxt["chapter_roman"] != trn["chapter_roman"]:
                pause_sec = 0.95
            elif nxt["speaker_key"] != trn["speaker_key"]:
                pause_sec = 0.48
            else:
                pause_sec = 0.35
            chunks.append(np.zeros(int(pause_sec * SAMPLE_RATE), dtype=np.float32))
            cursor_sec += pause_sec

    chunks.append(np.zeros(int(outro_hold_sec * SAMPLE_RATE), dtype=np.float32))
    total_dur = cursor_sec + outro_hold_sec

    # Compute scene time windows
    for sc in part["scenes"]:
        s_idx = sc["scene_idx"]
        s_turns = [t for t in turns if t["scene_idx"] == s_idx]
        if s_turns:
            sc["start_sec"] = round(s_turns[0]["start_sec"], 4)
            sc["end_sec"] = round(s_turns[-1]["end_sec"], 4)
            sc["duration_sec"] = round(sc["end_sec"] - sc["start_sec"], 4)
        else:
            sc["start_sec"] = 2.6
            sc["end_sec"] = round(total_dur, 4)
            sc["duration_sec"] = round(total_dur - 2.6, 4)

    full_mono = np.concatenate(chunks)
    pcm16 = (np.clip(full_mono, -0.98, 0.98) * 32767.0).astype(np.int16)
    master_wav = AUDIO_DIR / f"{part['id']}_master.wav"
    with wave.open(str(master_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm16.tobytes())

    part["title_card_end_sec"] = title_hold_sec
    part["total_duration_sec"] = round(len(full_mono) / float(SAMPLE_RATE), 4)
    part["voice_only_wav"] = str(master_wav.relative_to(ROOT))
    print(f"[MASTER WAV] {master_wav.name}: {part['total_duration_sec']:.1f}s ({len(turns)} turns)")
    return part


def main():
    api_key = get_api_key()
    parts = parse_chapters_into_parts()

    all_turns = [t for p in parts for t in p["turns"]]
    print(
        f"Synthesizing {len(all_turns)} turns across Chapters I-XII via gemini-3.8-flash-tts"
        " using studio prebuilt voices (Orus, Puck, Charon, Kore, Callirrhoe, Fenrir)..."
    )

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        futs = {
            ex.submit(
                synthesize_turn,
                t,
                api_key,
            ): t["global_turn_idx"]
            for t in all_turns
        }
        done_cnt = 0
        for f in concurrent.futures.as_completed(futs):
            f.result()
            done_cnt += 1
            if done_cnt % 20 == 0 or done_cnt == len(all_turns):
                print(f"  [TTS PROGRESS] {done_cnt}/{len(all_turns)} turns synthesized")

    # Assemble voice-only master WAVs and timelines
    for i in range(len(parts)):
        parts[i] = assemble_part_timeline_and_master(parts[i])

    # Generate 4 Lyria 3.5 scores and mix with structural fade-in/fade-out cues
    from generate_and_mix_music import mix_voice_and_music

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        futs = {
            ex.submit(generate_lyria_track, p["id"], p["lyria_prompt"], api_key): p["id"]
            for p in parts
        }
        mp3_map = {}
        for f in concurrent.futures.as_completed(futs):
            pid = futs[f]
            mp3_map[pid] = f.result()

    for p in parts:
        pid = p["id"]
        voice_wav = AUDIO_DIR / f"{pid}_master.wav"
        scored_wav = AUDIO_DIR / f"{pid}_master_scored.wav"
        mix_voice_and_music(p, voice_wav, mp3_map[pid], scored_wav, sr=48000)
        p["master_wav"] = str(scored_wav.relative_to(ROOT))
        p["music_mp3"] = str(mp3_map[pid].relative_to(ROOT))

    if CANDIDE_TIMELINE_PATH.exists():
        old_data = json.loads(CANDIDE_TIMELINE_PATH.read_text())
        old_by_id = {b["id"]: b for b in old_data.get("books", [])}
        for p in parts:
            old_b = old_by_id.get(p["id"], {})
            for k, v in old_b.items():
                if k not in p:
                    p[k] = v

    CANDIDE_TIMELINE_PATH.write_text(json.dumps({"books": parts}, indent=2))
    print(f"Saved complete Candide timeline to {CANDIDE_TIMELINE_PATH}")


if __name__ == "__main__":
    main()

