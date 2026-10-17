#!/usr/bin/env python3
"""Build Part 1 of the Macbeth Victorian Toy Theatre Pop-Up Video:
1. Creates 6 distinct Shakespearean voices via Gemini 3.8 Flash TTS Voice Design
   (POST /v1beta/voices, model="gemini-3.8-flash-tts").
2. Synthesizes all 28 turns across Act I, Scene 1 and Act I, Scene 3
   (2 Visual Scenes across 4 Right-Hand Text Folios) into audio/turns/07_macbeth_turn_*.wav.
3. Assembles audio/07_macbeth_master.wav (24 kHz mono) with:
   - title_card_end_sec = 2.6s + TITLE_TURN_PAUSE_SEC = 2.8s (Turn 0 starts at 5.4s)
   - 1.45s stage-action pauses after Turn 0 (enter_witches_sc1), Turn 10 (exit_witches_sc1),
     Turn 13 (enter_macbeth_banquo), and Turn 25 (vanish_witches)
   - Subtle -26 dBFS brown-noise bandpass stage foley (distant thunder rumble on Turn 0 +
     eerie moorland wind whoosh on Turn 25) via scipy.signal
   - 2.8s 3D page-turn pause between Scene 0 (after Turn 10's 1.45s exit hold) and Scene 1 (Turn 11)
   - 0.85s text-folio crossfade pauses between Folio 1 -> Folio 2 and Folio 2 -> Folio 3
   - OUTRO_HOLD_SEC = 2.6s after Turn 27
4. Generates music/07_macbeth_lyria.mp3 via Lyria 3.5 (model="lyria-3.5" on Gemini API),
   applies select_warm_ensemble_section(), FlashSR 48 kHz neural super-resolution, and
   upsample_and_warm_master_music() to produce music/07_macbeth_lyria.wav and
   audio/07_macbeth_master_scored.wav with the strict intro/outro-only envelope.
5. Writes audio/macbeth_manifest.json.
"""

import argparse
import base64
import concurrent.futures
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path
import numpy as np
from scipy import signal

os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import site

# Load PyTorch from the local virtualenv site-packages if not present in the active environment
try:
    import torch
except ImportError:
    for _sp in sorted((Path.home() / "js-art-arena" / ".venv" / "lib").glob("python*/site-packages")):
        site.addsitedir(str(_sp))
    try:
        import torch
    except ImportError:
        torch = None

if torch is not None:
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)

ROOT = Path(__file__).resolve().parent.parent
VOICES_DIR = ROOT / "voices"
MACBETH_VOICES_MANIFEST = VOICES_DIR / "macbeth_voices_manifest.json"
AUDIO_DIR = ROOT / "audio"
TURNS_DIR = AUDIO_DIR / "turns"
MUSIC_DIR = ROOT / "music"
MODELS_DIR = MUSIC_DIR / "models"
FLASHSR_CKPT = MODELS_DIR / "flashsr_upsampler.pth"
MANIFEST_PATH = AUDIO_DIR / "macbeth_manifest.json"

if str(MODELS_DIR) not in sys.path:
    sys.path.insert(0, str(MODELS_DIR))

BOOK_ID = "07_macbeth"
SAMPLE_RATE = 24000
SCORED_SAMPLE_RATE = 48000

TITLE_CARD_HOLD_SEC = 2.6
TITLE_TURN_PAUSE_SEC = 2.8
STAGE_ACTION_PAUSE_SEC = 1.45
PAGE_TURN_PAUSE_SEC = 2.8
PRE_FOLIO_BREATH_SEC = 0.40
FOLIO_FADE_PAUSE_SEC = 0.45  # 0.40 + 0.45 = 0.85s text-folio crossfade pause
OUTRO_HOLD_SEC = 2.6
FOLEY_TARGET_DBFS = -26.0

MACBETH_LYRIA_PROMPT = (
    "Dark, atmospheric chamber music in D minor for a tragedy on the Scottish moors — "
    "deep resonant solo cello and contrabass drone foundation, mournful viola da gamba, "
    "low muted French horn and subtle deep timpani pulse, warm wooden concert hall acoustics, "
    "close ribbon microphones, rich 50-350 Hz body, solemn and cinematic, no vocals, no percussion loops"
)

MACBETH_VOICES_SPEC = {
    "stage_narrator": {
        "voice_id": "Fenrir",
        "display_name": "Classical Stage Narrator (Macbeth)",
        "gender": "male",
        "language_code": "en-GB",
        "persona_style": (
            "Calm, refined British classical stage narrator in his late 40s, "
            "warm Received Pronunciation baritone, intimate measured pace"
        ),
        "prompt": (
            "A calm, poised, refined British classical stage narrator in his late 40s with a "
            "warm, cultivated Received Pronunciation baritone, reading theatrical stage directions "
            "in a clear, measured, atmospheric tone without melodrama."
        ),
    },
    "first_witch": {
        "voice_id": "Callirrhoe",
        "display_name": "First Witch (Macbeth)",
        "gender": "female",
        "language_code": "en-GB",
        "persona_style": (
            "Eerie, weathered ancient Scottish crone contralto, dark prophetic cadence, "
            "clear full-voiced theatrical diction without whispering. Pronounce 'Glamis' as 'Glahmz'"
        ),
        "prompt": (
            "A measured, eerie, older Scottish woman with a low, clear, resonant contralto voice, "
            "delivering Shakespeare's verse with solemn prophetic gravity, uncanny calm, "
            "and crisp natural theatrical articulation."
        ),
    },
    "second_witch": {
        "voice_id": "Zephyr",
        "display_name": "Second Witch (Macbeth)",
        "gender": "female",
        "language_code": "en-GB",
        "persona_style": (
            "Sinister, uncanny Scottish witch mezzo-soprano, unsettling rhythmic incantation, "
            "crisp theatrical articulation without whispering. Pronounce 'Cawdor' as 'Kaw-dor'"
        ),
        "prompt": (
            "A sharp, incisive Scottish woman with a clear, focused mezzo-soprano voice, "
            "delivering Shakespeare's verse with uncanny rhythmic precision, dark knowing stillness, "
            "and crisp full-voiced theatrical articulation."
        ),
    },
    "third_witch": {
        "voice_id": "Aoede",
        "display_name": "Third Witch (Macbeth)",
        "gender": "female",
        "language_code": "en-GB",
        "persona_style": (
            "Deep, ominous, ancient Scottish prophetess contralto, "
            "solemn and haunting full-voiced theatrical delivery"
        ),
        "prompt": (
            "A solemn, prophetic Scottish woman with a warm, dark, clear alto voice, "
            "delivering Shakespeare's verse with unhurried fateful cadence, ominous authority, "
            "and natural full-voiced classical diction."
        ),
    },
    "macbeth": {
        "voice_id": "Iapetus",
        "display_name": "Macbeth, Thane of Glamis",
        "gender": "male",
        "language_code": "en-GB",
        "persona_style": (
            "Deep, commanding Scottish warrior-thane baritone, noble and intense "
            "Royal Shakespeare Company delivery with natural Scottish inflection. "
            "Pronounce 'Glamis' as 'Glahmz' and 'Sinel's' as 'Sinnel's'"
        ),
        "prompt": (
            "A commanding, resonant Scottish baritone in his early 40s — a noble warrior-thane "
            "whose voice is intense, articulate, and deeply thoughtful, delivering Shakespearean "
            "blank verse with natural RSC authority and inward psychological weight. "
            "Pronounce 'Glamis' as 'Glahmz' and 'Sinel's' as 'Sinnel's'."
        ),
    },
    "banquo": {
        "voice_id": "Orus",
        "display_name": "Banquo (Macbeth)",
        "gender": "male",
        "language_code": "en-GB",
        "persona_style": (
            "Grounded, watchful, noble Scottish soldier and lord, "
            "clear resonant tenor-baritone with natural Scottish inflection and steady courage"
        ),
        "prompt": (
            "A grounded, watchful, warm Scottish baritone-tenor in his late 30s — a clear, "
            "observant, skeptical soldier and nobleman speaking Shakespearean verse with steady "
            "courage, natural lucidity, and measured restraint."
        ),
    },
    "ross": {
        "voice_id": "Charon",
        "display_name": "Ross, Scottish Nobleman (Macbeth)",
        "gender": "male",
        "language_code": "en-GB",
        "persona_style": (
            "Noble, ceremonial Scottish highland lord and royal herald, "
            "deep resonant baritone with warm Scottish inflection. Pronounce 'Cawdor' as 'Kaw-dor'"
        ),
        "prompt": (
            "A noble, commanding Scottish highland lord and royal herald in his forties — "
            "clear, resonant baritone with warm Scottish inflection, dignified authority, "
            "and ceremonial gravitas."
        ),
    },
    "lady_macbeth": {
        "voice_id": "Kore",
        "display_name": "Lady Macbeth",
        "gender": "female",
        "language_code": "en-GB",
        "persona_style": (
            "Fierce, hypnotic, aristocratic Scottish noblewoman, rich dark velvet mezzo-contralto "
            "with steely resolve and commanding RSC poise. Pronounce 'Glamis' as 'Glahmz'"
        ),
        "prompt": (
            "A fierce, hypnotic, aristocratic Scottish noblewoman in her thirties — rich, "
            "dark velvet mezzo-contralto voice with steely resolve, commanding poise, and "
            "clear full-voiced theatrical power. Pronounce 'Glamis' as 'Glahmz'."
        ),
    },
}

VISUAL_SCENES_SPEC = [
    {
        "scene_idx": 0,
        "popup_spread_num": 1,
        "caption": "ACT I, SCENE I — A Desert Place",
        "folios": [0],
    },
    {
        "scene_idx": 1,
        "popup_spread_num": 2,
        "caption": "ACT I, SCENE III — A Heath near Forres",
        "folios": [1, 2, 3, 4],
    },
    {
        "scene_idx": 2,
        "popup_spread_num": 3,
        "caption": "ACT I, SCENE V — Inverness. Macbeth’s Castle",
        "folios": [5, 6],
    },
    {
        "scene_idx": 3,
        "popup_spread_num": 4,
        "caption": "ACT II, SCENES I & II — Midnight at Inverness",
        "folios": [7, 8, 9],
    },
]

FOLIO_TITLES = {
    0: "ACT I, SCENE I — A Desert Place",
    1: "ACT I, SCENE III — A Heath near Forres",
    2: "ACT I, SCENE III — The Prophecies on the Heath",
    3: "ACT I, SCENE III — Into the Air",
    4: "ACT I, SCENE III — Thane of Cawdor",
    5: "ACT I, SCENE V — Inverness. The Letter & Invocation",
    6: "ACT I, SCENE V — Look Like the Innocent Flower",
    7: "ACT II, SCENE I — The Dagger of the Mind",
    8: "ACT II, SCENE II — I Have Done the Deed",
    9: "ACT II, SCENE II — Knocking at the Gate",
}

MACBETH_TURNS_SPEC = [
    # =========================================================================
    # Visual Scene 0 (scene_idx = 0, popup_spread_num = 1):
    # "ACT I, SCENE I — A Desert Place" (Folio 0)
    # =========================================================================
    {
        "turn_idx": 0,
        "scene_idx": 0,
        "folio_idx": 0,
        "speaker": "stage_narrator",
        "label": "STAGE DIRECTION",
        "is_stage_direction": True,
        "is_dialogue": False,
        "stage_cue": "enter_witches_sc1",
        "display_text": "Thunder and lightning. Enter three Witches.",
        "tts_text": "Thunder and lightning. Enter three Witches.",
        "style": "calm, poised classical stage direction, clear measured pace",
        "pause_after_sec": STAGE_ACTION_PAUSE_SEC,
    },
    {
        "turn_idx": 1,
        "scene_idx": 0,
        "folio_idx": 0,
        "speaker": "first_witch",
        "label": "FIRST WITCH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "When shall we three meet again\nIn thunder, lightning, or in rain?",
        "tts_text": "When shall we three meet again, in thunder, lightning, or in rain?",
        "style": "low, eerie, solemn prophetic cadence, measured supernatural stillness and crisp full-voiced articulation",
        "pause_after_sec": 0.36,
    },
    {
        "turn_idx": 2,
        "scene_idx": 0,
        "folio_idx": 0,
        "speaker": "second_witch",
        "label": "SECOND WITCH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "When the hurlyburly’s done,\nWhen the battle’s lost and won.",
        "tts_text": "When the hurlyburly's done, when the battle's lost and won.",
        "style": "sharp, uncanny rhythmic cadence, dark knowing intensity and clear full-voiced articulation",
        "pause_after_sec": 0.36,
    },
    {
        "turn_idx": 3,
        "scene_idx": 0,
        "folio_idx": 0,
        "speaker": "third_witch",
        "label": "THIRD WITCH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "That will be ere the set of sun.",
        "tts_text": "That will be ere the set of sun.",
        "style": "dark, solemn prophetic gravity, unhurried fateful cadence and clear full-voiced articulation",
        "pause_after_sec": 0.38,
    },
    {
        "turn_idx": 4,
        "scene_idx": 0,
        "folio_idx": 0,
        "speaker": "first_witch",
        "label": "FIRST WITCH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "Where the place?",
        "tts_text": "Where the place?",
        "style": "low, eerie, measured question, solemn supernatural stillness and crisp full-voiced articulation",
        "pause_after_sec": 0.30,
    },
    {
        "turn_idx": 5,
        "scene_idx": 0,
        "folio_idx": 0,
        "speaker": "second_witch",
        "label": "SECOND WITCH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "Upon the heath.",
        "tts_text": "Upon the heath.",
        "style": "sharp, uncanny certainty, dark rhythmic precision and clear full-voiced articulation",
        "pause_after_sec": 0.32,
    },
    {
        "turn_idx": 6,
        "scene_idx": 0,
        "folio_idx": 0,
        "speaker": "third_witch",
        "label": "THIRD WITCH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "There to meet with Macbeth.",
        "tts_text": "There to meet with Macbeth.",
        "style": "solemn, ominous prophetic weight, fateful cadence and clear full-voiced articulation",
        "pause_after_sec": 0.40,
    },
    {
        "turn_idx": 7,
        "scene_idx": 0,
        "folio_idx": 0,
        "speaker": "first_witch",
        "label": "FIRST WITCH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "I come, Graymalkin!",
        "tts_text": "I come, Graymalkin!",
        "style": "eerie, alert call to her familiar, clear resonant contralto with supernatural poise",
        "pause_after_sec": 0.32,
    },
    {
        "turn_idx": 8,
        "scene_idx": 0,
        "folio_idx": 0,
        "speaker": "second_witch",
        "label": "SECOND WITCH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "Paddock calls.",
        "tts_text": "Paddock calls.",
        "style": "sharp, alert uncanny answer, clear focused mezzo-soprano",
        "pause_after_sec": 0.32,
    },
    {
        "turn_idx": 9,
        "scene_idx": 0,
        "folio_idx": 0,
        "speaker": "third_witch",
        "label": "THIRD WITCH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "Anon.\nFair is foul, and foul is fair:\nHover through the fog and filthy air.",
        "tts_text": "Anon. Fair is foul, and foul is fair: hover through the fog and filthy air.",
        "style": "solemn, rhythmic ritual chant, dark prophetic cadence and clear full-voiced articulation",
        "pause_after_sec": 0.42,
    },
    {
        "turn_idx": 10,
        "scene_idx": 0,
        "folio_idx": 0,
        "speaker": "stage_narrator",
        "label": "STAGE DIRECTION",
        "is_stage_direction": True,
        "is_dialogue": False,
        "stage_cue": "exit_witches_sc1",
        "display_text": "Exeunt.",
        "tts_text": "Exeunt.",
        "style": "calm, poised classical stage direction, pronounce Exeunt as EK-see-unt",
        # 1.45s stage-action exit hold (in Scene 0) + 2.8s 3D page turn to Scene 1 = 4.25s total
        "pause_after_sec": round(STAGE_ACTION_PAUSE_SEC + PAGE_TURN_PAUSE_SEC, 4),
        "stage_action_hold_sec": STAGE_ACTION_PAUSE_SEC,
        "page_turn_pause_sec": PAGE_TURN_PAUSE_SEC,
    },

    # =========================================================================
    # Visual Scene 1 (scene_idx = 1, popup_spread_num = 2):
    # "ACT I, SCENE III — A Heath near Forres" (Folio 1)
    # =========================================================================
    {
        "turn_idx": 11,
        "scene_idx": 1,
        "folio_idx": 1,
        "speaker": "third_witch",
        "label": "THIRD WITCH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "A drum, a drum!\nMacbeth doth come.",
        "tts_text": "A drum, a drum! Macbeth doth come.",
        "style": "alert, ominous prophetic anticipation, rhythmic pulse and clear full-voiced articulation",
        "pause_after_sec": 0.36,
    },
    {
        "turn_idx": 12,
        "scene_idx": 1,
        "folio_idx": 1,
        "speaker": "first_witch",
        "label": "THE WEIRD SISTERS",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "The weird sisters, hand in hand,\n"
            "Posters of the sea and land,\n"
            "Thus do go about, about:\n"
            "Peace! the charm’s wound up."
        ),
        "tts_text": (
            "The weird sisters, hand in hand, posters of the sea and land, "
            "thus do go about, about: Peace! the charm's wound up."
        ),
        "style": "solemn, rhythmic ritual chant with dark prophetic poise, ending with a sudden, quiet, commanding 'Peace! the charm's wound up'",
        "pause_after_sec": 0.42,
    },
    {
        "turn_idx": 13,
        "scene_idx": 1,
        "folio_idx": 1,
        "speaker": "stage_narrator",
        "label": "STAGE DIRECTION",
        "is_stage_direction": True,
        "is_dialogue": False,
        "stage_cue": "enter_macbeth_banquo",
        "display_text": "Enter Macbeth and Banquo.",
        "tts_text": "Enter Macbeth and Banquo.",
        "style": "calm, poised classical stage direction",
        "pause_after_sec": STAGE_ACTION_PAUSE_SEC,
    },
    {
        "turn_idx": 14,
        "scene_idx": 1,
        "folio_idx": 1,
        "speaker": "macbeth",
        "label": "MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "So foul and fair a day I have not seen.",
        "tts_text": "So foul and fair a day I have not seen.",
        "style": "commanding, weary yet resonant Scottish baritone, reflective warrior",
        "pause_after_sec": 0.40,
    },
    {
        "turn_idx": 15,
        "scene_idx": 1,
        "folio_idx": 1,
        "speaker": "banquo",
        "label": "BANQUO",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "How far is’t call’d to Forres? What are these,\n"
            "So wither’d, and so wild in their attire,\n"
            "That look not like the inhabitants o’ the earth,\n"
            "And yet are on’t?"
        ),
        "tts_text": (
            "How far is't called to Forres? What are these, "
            "so withered, and so wild in their attire, "
            "that look not like the inhabitants o' the earth, "
            "and yet are on't?"
        ),
        "style": "grounded Scottish baritone-tenor, sudden watchful astonishment as he spots the figures",
        # Same visual scene -> 0.85s text-folio crossfade pause (0.40s breath + 0.45s fade)
        "pause_after_sec": round(PRE_FOLIO_BREATH_SEC + FOLIO_FADE_PAUSE_SEC, 4),
    },

    # =========================================================================
    # Visual Scene 1 (scene_idx = 1, popup_spread_num = 2):
    # Folio 2 (Same visual scene — right-hand text crossfade only, no page turn!)
    # =========================================================================
    {
        "turn_idx": 16,
        "scene_idx": 1,
        "folio_idx": 2,
        "speaker": "macbeth",
        "label": "MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "Speak, if you can: what are you?",
        "tts_text": "Speak, if you can: what are you?",
        "style": "commanding, intense Scottish baritone, taut authority",
        "pause_after_sec": 0.38,
    },
    {
        "turn_idx": 17,
        "scene_idx": 1,
        "folio_idx": 2,
        "speaker": "first_witch",
        "label": "FIRST WITCH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "All hail, Macbeth! hail to thee, thane of Glamis!",
        "tts_text": "All hail, Macbeth! hail to thee, thane of Glahmz!",
        "style": "solemn, heraldic prophetic salutation, low resonant contralto, pronounce Glahmz clearly",
        "pause_after_sec": 0.36,
    },
    {
        "turn_idx": 18,
        "scene_idx": 1,
        "folio_idx": 2,
        "speaker": "second_witch",
        "label": "SECOND WITCH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "All hail, Macbeth! hail to thee, thane of Cawdor!",
        "tts_text": "All hail, Macbeth! hail to thee, thane of Cawdor!",
        "style": "sharp, heraldic prophetic salutation, clear focused mezzo-soprano, uncanny authority",
        "pause_after_sec": 0.36,
    },
    {
        "turn_idx": 19,
        "scene_idx": 1,
        "folio_idx": 2,
        "speaker": "third_witch",
        "label": "THIRD WITCH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "All hail, Macbeth, that shalt be king hereafter!",
        "tts_text": "All hail, Macbeth, that shalt be king hereafter!",
        "style": "grand, fateful prophetic proclamation, dark resonant alto with ominous triumph",
        "pause_after_sec": 0.44,
    },
    {
        "turn_idx": 20,
        "scene_idx": 1,
        "folio_idx": 2,
        "speaker": "banquo",
        "label": "BANQUO",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "Good sir, why do you start; and seem to fear\n"
            "Things that do sound so fair? I’ the name of truth,\n"
            "Are ye fantastical, or that indeed\n"
            "Which outwardly ye show?"
        ),
        "tts_text": (
            "Good sir, why do you start; and seem to fear "
            "things that do sound so fair? In the name of truth, "
            "are ye fantastical, or that indeed "
            "which outwardly ye show?"
        ),
        "style": "observant, concerned Scottish soldier addressing Macbeth, then challenging the Witches",
        "pause_after_sec": 0.38,
    },
    {
        "turn_idx": 21,
        "scene_idx": 1,
        "folio_idx": 2,
        "speaker": "first_witch",
        "label": "FIRST WITCH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "Lesser than Macbeth, and greater.",
        "tts_text": "Lesser than Macbeth, and greater.",
        "style": "measured, enigmatic prophetic riddle, low resonant contralto with quiet knowing gravity",
        "pause_after_sec": 0.34,
    },
    {
        "turn_idx": 22,
        "scene_idx": 1,
        "folio_idx": 2,
        "speaker": "second_witch",
        "label": "SECOND WITCH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "Not so happy, yet much happier.",
        "tts_text": "Not so happy, yet much happier.",
        "style": "sharp, paradoxical prophetic riddle, clear focused mezzo-soprano with uncanny poise",
        "pause_after_sec": 0.34,
    },
    {
        "turn_idx": 23,
        "scene_idx": 1,
        "folio_idx": 2,
        "speaker": "third_witch",
        "label": "THIRD WITCH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "Thou shalt get kings, though thou be none:\nSo all hail, Macbeth and Banquo!",
        "tts_text": "Thou shalt get kings, though thou be none: so all hail, Macbeth and Banquo!",
        "style": "solemn, triumphant prophetic proclamation, dark resonant alto with fateful clarity",
        # Same visual scene -> 0.85s text-folio crossfade pause (0.40s breath + 0.45s fade)
        "pause_after_sec": round(PRE_FOLIO_BREATH_SEC + FOLIO_FADE_PAUSE_SEC, 4),
    },

    # =========================================================================
    # Visual Scene 1 (scene_idx = 1, popup_spread_num = 2):
    # Folio 3 (Same visual scene — right-hand text crossfade only, no page turn!)
    # =========================================================================
    {
        "turn_idx": 24,
        "scene_idx": 1,
        "folio_idx": 3,
        "speaker": "macbeth",
        "label": "MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "Stay, you imperfect speakers, tell me more:\n"
            "By Sinel’s death I know I am thane of Glamis;\n"
            "But how of Cawdor? and to be king\n"
            "Stands not within the prospect of belief.\n"
            "Speak, I charge you."
        ),
        "tts_text": (
            "Stay, you imperfect speakers, tell me more: "
            "By Sinnel's death I know I am thane of Glahmz; "
            "but how of Cawdor? and to be king "
            "stands not within the prospect of belief. "
            "Speak, I charge you."
        ),
        "style": "urgent, commanding Scottish baritone, intense questioning, pronounce Sinnel's and Glahmz clearly",
        "pause_after_sec": 0.38,
    },
    {
        "turn_idx": 25,
        "scene_idx": 1,
        "folio_idx": 3,
        "speaker": "stage_narrator",
        "label": "STAGE DIRECTION",
        "is_stage_direction": True,
        "is_dialogue": False,
        "stage_cue": "vanish_witches",
        "display_text": "The Witches vanish.",
        "tts_text": "The Witches vanish.",
        "style": "calm, quiet, mysterious classical stage direction",
        "pause_after_sec": STAGE_ACTION_PAUSE_SEC,
    },
    {
        "turn_idx": 26,
        "scene_idx": 1,
        "folio_idx": 3,
        "speaker": "banquo",
        "label": "BANQUO",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "The earth hath bubbles, as the water has,\n"
            "And these are of them. Whither are they vanish’d?"
        ),
        "tts_text": (
            "The earth hath bubbles, as the water has, "
            "and these are of them. Whither are they vanished?"
        ),
        "style": "quiet, bewildered wonder, grounded Scottish baritone-tenor",
        "pause_after_sec": 0.38,
    },
    {
        "turn_idx": 27,
        "scene_idx": 1,
        "folio_idx": 3,
        "speaker": "macbeth",
        "label": "MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "Into the air; and what seem’d corporal melted\n"
            "As breath into the wind. Would they had stay’d!"
        ),
        "tts_text": (
            "Into the air; and what seemed corporal melted "
            "as breath into the wind. Would they had stayed!"
        ),
        "style": "reflective, inward, spellbound longing, resonant Scottish baritone",
        # Same visual scene -> 0.85s text-folio crossfade pause into Folio 4
        "pause_after_sec": round(PRE_FOLIO_BREATH_SEC + FOLIO_FADE_PAUSE_SEC, 4),
    },

    # =========================================================================
    # Continuation of Visual Scene 1 (scene_idx = 1, popup_spread_num = 2):
    # "ACT I, SCENE III — A Heath near Forres" (Folio 4)
    # =========================================================================
    {
        "turn_idx": 28,
        "scene_idx": 1,
        "folio_idx": 4,
        "speaker": "stage_narrator",
        "label": "STAGE DIRECTION",
        "is_stage_direction": True,
        "is_dialogue": False,
        "stage_cue": "enter_ross",
        "display_text": "Enter Ross.",
        "tts_text": "Enter Ross.",
        "style": "calm, poised classical stage direction",
        "pause_after_sec": STAGE_ACTION_PAUSE_SEC,
    },
    {
        "turn_idx": 29,
        "scene_idx": 1,
        "folio_idx": 4,
        "speaker": "ross",
        "label": "ROSS",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "The king hath happily received, Macbeth,\n"
            "The news of thy success: and, for an earnest\n"
            "Of a greater honour, he bade me, from him,\n"
            "Call thee thane of Cawdor: in which addition,\n"
            "Hail, most worthy thane! for it is thine."
        ),
        "tts_text": (
            "The king hath happily received, Macbeth, "
            "the news of thy success: and, for an earnest "
            "of a greater honour, he bade me, from him, "
            "call thee thane of Cawdor: in which addition, "
            "Hail, most worthy thane! for it is thine."
        ),
        "style": "noble, commanding Scottish highland lord and royal herald, warm resonant baritone with ceremonial gravitas",
        "pause_after_sec": 0.38,
    },
    {
        "turn_idx": 30,
        "scene_idx": 1,
        "folio_idx": 4,
        "speaker": "banquo",
        "label": "BANQUO",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "What, can the devil speak true?",
        "tts_text": "What, can the devil speak true?",
        "style": "stunned, quiet Scottish baritone-tenor aside, shocked disbelief",
        "pause_after_sec": 0.36,
    },
    {
        "turn_idx": 31,
        "scene_idx": 1,
        "folio_idx": 4,
        "speaker": "macbeth",
        "label": "MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "The thane of Cawdor lives: why do you dress me\n"
            "In borrow’d robes?"
        ),
        "tts_text": (
            "The thane of Cawdor lives: why do you dress me "
            "in borrowed robes?"
        ),
        "style": "commanding, startled Scottish baritone, urgent questioning",
        "pause_after_sec": 0.38,
    },
    {
        "turn_idx": 32,
        "scene_idx": 1,
        "folio_idx": 4,
        "speaker": "ross",
        "label": "ROSS",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "Who was the thane lives yet;\n"
            "But under heavy judgment bears that life\n"
            "Which he deserves to lose. Treasons capital,\n"
            "Confess’d and proved, have overthrown him."
        ),
        "tts_text": (
            "Who was the thane lives yet; "
            "but under heavy judgment bears that life "
            "which he deserves to lose. Treasons capital, "
            "confessed and proved, have overthrown him."
        ),
        "style": "solemn, dignified Scottish baritone, grave judicial authority",
        "pause_after_sec": 0.40,
    },
    {
        "turn_idx": 33,
        "scene_idx": 1,
        "folio_idx": 4,
        "speaker": "macbeth",
        "label": "MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "Glamis, and thane of Cawdor!\n"
            "The greatest is behind.\n"
            "Two truths are told,\n"
            "As happy prologues to the swelling act\n"
            "Of the imperial theme."
        ),
        "tts_text": (
            "Glahmz, and thane of Cawdor! "
            "The greatest is behind. "
            "Two truths are told, "
            "as happy prologues to the swelling act "
            "of the imperial theme."
        ),
        "style": "inward, spellbound soliloquy, resonant Scottish baritone rising with dark ambition, pronounce Glahmz clearly",
        "pause_after_sec": PAGE_TURN_PAUSE_SEC,
        "stage_action_hold_sec": 0.0,
        "page_turn_pause_sec": PAGE_TURN_PAUSE_SEC,
    },

    # =========================================================================
    # Visual Scene 2 (scene_idx = 2, popup_spread_num = 3):
    # "ACT I, SCENE V — Inverness. Macbeth’s Castle" (Folios 5 & 6)
    # =========================================================================
    {
        "turn_idx": 34,
        "scene_idx": 2,
        "folio_idx": 5,
        "speaker": "stage_narrator",
        "label": "STAGE DIRECTION",
        "is_stage_direction": True,
        "is_dialogue": False,
        "stage_cue": "enter_lady_macbeth_sc3",
        "display_text": "Inverness. Macbeth’s castle. Enter Lady Macbeth, reading a letter.",
        "tts_text": "Inverness. Macbeth's castle. Enter Lady Macbeth, reading a letter.",
        "style": "calm, poised, atmospheric classical stage direction",
        "pause_after_sec": STAGE_ACTION_PAUSE_SEC,
    },
    {
        "turn_idx": 35,
        "scene_idx": 2,
        "folio_idx": 5,
        "speaker": "lady_macbeth",
        "label": "LADY MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "‘They met me in the day of success; and I have learned by the perfectest report, "
            "they have more in them than mortal knowledge. When I burned in desire to question "
            "them further, they made themselves air, into which they vanished. Whilst I stood "
            "rapt in the wonder of it, came missives from the king, who all-hailed me Thane of "
            "Cawdor; by which title, before, these weird sisters saluted me, and referred me to "
            "the coming on of time, with Hail, king that shalt be!’"
        ),
        "tts_text": (
            "They met me in the day of success; and I have learned by the perfectest report, "
            "they have more in them than mortal knowledge. When I burned in desire to question "
            "them further, they made themselves air, into which they vanished. Whilst I stood "
            "rapt in the wonder of it, came missives from the king, who all-hailed me Thane of "
            "Cawdor; by which title, before, these weird sisters saluted me, and referred me to "
            "the coming on of time, with Hail, king that shalt be!"
        ),
        "style": "fierce, hypnotic aristocratic Scottish noblewoman, dark velvet mezzo-contralto reading Macbeth's letter with focused intensity and rising triumph",
        "pause_after_sec": 0.42,
    },
    {
        "turn_idx": 36,
        "scene_idx": 2,
        "folio_idx": 5,
        "speaker": "lady_macbeth",
        "label": "LADY MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "Glamis thou art, and Cawdor; and shalt be\n"
            "What thou art promised: yet do I fear thy nature;\n"
            "It is too full o’ the milk of human kindness\n"
            "To catch the nearest way. Hie thee hither,\n"
            "That I may pour my spirits in thine ear."
        ),
        "tts_text": (
            "Glahmz thou art, and Cawdor; and shalt be "
            "what thou art promised: yet do I fear thy nature; "
            "it is too full o' the milk of human kindness "
            "to catch the nearest way. Hie thee hither, "
            "that I may pour my spirits in thine ear."
        ),
        "style": "dark velvet mezzo-contralto, steely resolve and incisive intimacy, pronounce Glahmz clearly",
        "pause_after_sec": 0.44,
    },
    {
        "turn_idx": 37,
        "scene_idx": 2,
        "folio_idx": 5,
        "speaker": "lady_macbeth",
        "label": "LADY MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "Come, you spirits\n"
            "That tend on mortal thoughts, unsex me here,\n"
            "And fill me from the crown to the toe top-full\n"
            "Of direst cruelty! Come, thick night,\n"
            "And pall thee in the dunnest smoke of hell,\n"
            "That my keen knife see not the wound it makes,\n"
            "Nor heaven peep through the blanket of the dark,\n"
            "To cry ‘Hold, hold!’"
        ),
        "tts_text": (
            "Come, you spirits "
            "that tend on mortal thoughts, unsex me here, "
            "and fill me from the crown to the toe top-full "
            "of direst cruelty! Come, thick night, "
            "and pall thee in the dunnest smoke of hell, "
            "that my keen knife see not the wound it makes, "
            "nor heaven peep through the blanket of the dark, "
            "to cry 'Hold, hold!'"
        ),
        "style": "fierce, commanding dark mezzo-contralto invocation, solemn ritual intensity and dark theatrical power",
        "pause_after_sec": round(PRE_FOLIO_BREATH_SEC + FOLIO_FADE_PAUSE_SEC, 4),
    },
    {
        "turn_idx": 38,
        "scene_idx": 2,
        "folio_idx": 6,
        "speaker": "stage_narrator",
        "label": "STAGE DIRECTION",
        "is_stage_direction": True,
        "is_dialogue": False,
        "stage_cue": "enter_macbeth_sc3",
        "display_text": "Enter Macbeth.",
        "tts_text": "Enter Macbeth.",
        "style": "calm, poised classical stage direction",
        "pause_after_sec": STAGE_ACTION_PAUSE_SEC,
    },
    {
        "turn_idx": 39,
        "scene_idx": 2,
        "folio_idx": 6,
        "speaker": "lady_macbeth",
        "label": "LADY MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "Great Glamis! worthy Cawdor!\n"
            "Greater than both, by the all-hail hereafter!\n"
            "Thy letters have transported me beyond\n"
            "This ignorant present, and I feel now\n"
            "The future in the instant."
        ),
        "tts_text": (
            "Great Glahmz! worthy Cawdor! "
            "Greater than both, by the all-hail hereafter! "
            "Thy letters have transported me beyond "
            "this ignorant present, and I feel now "
            "the future in the instant."
        ),
        "style": "exultant, hypnotic dark mezzo-contralto greeting Macbeth with electric ambition, pronounce Glahmz clearly",
        "pause_after_sec": 0.38,
    },
    {
        "turn_idx": 40,
        "scene_idx": 2,
        "folio_idx": 6,
        "speaker": "macbeth",
        "label": "MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "My dearest love,\n"
            "Duncan comes here to-night."
        ),
        "tts_text": "My dearest love, Duncan comes here to-night.",
        "style": "low, weighted, intimate Scottish baritone",
        "pause_after_sec": 0.34,
    },
    {
        "turn_idx": 41,
        "scene_idx": 2,
        "folio_idx": 6,
        "speaker": "lady_macbeth",
        "label": "LADY MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "And when goes hence?",
        "tts_text": "And when goes hence?",
        "style": "low, pointed, conspiratorial mezzo-contralto, quiet deadly focus",
        "pause_after_sec": 0.34,
    },
    {
        "turn_idx": 42,
        "scene_idx": 2,
        "folio_idx": 6,
        "speaker": "macbeth",
        "label": "MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "To-morrow, as he purposes.",
        "tts_text": "To-morrow, as he purposes.",
        "style": "guarded, meaningful Scottish baritone",
        "pause_after_sec": 0.38,
    },
    {
        "turn_idx": 43,
        "scene_idx": 2,
        "folio_idx": 6,
        "speaker": "lady_macbeth",
        "label": "LADY MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "O, never\n"
            "Shall sun that morrow see!\n"
            "Your face, my thane, is as a book where men\n"
            "May read strange matters. Look like the innocent flower,\n"
            "But be the serpent under’t. He that’s coming\n"
            "Must be provided for: and you shall put\n"
            "This night’s great business into my dispatch."
        ),
        "tts_text": (
            "O, never shall sun that morrow see! "
            "Your face, my thane, is as a book where men "
            "may read strange matters. Look like the innocent flower, "
            "but be the serpent under't. He that's coming "
            "must be provided for: and you shall put "
            "this night's great business into my dispatch."
        ),
        "style": "commanding, steely, hypnotic dark mezzo-contralto, deadly authority",
        "pause_after_sec": PAGE_TURN_PAUSE_SEC,
        "stage_action_hold_sec": 0.0,
        "page_turn_pause_sec": PAGE_TURN_PAUSE_SEC,
    },

    # =========================================================================
    # Visual Scene 3 (scene_idx = 3, popup_spread_num = 4):
    # "ACT II, SCENES I & II — Midnight at Inverness" (Folios 7, 8 & 9)
    # =========================================================================
    {
        "turn_idx": 44,
        "scene_idx": 3,
        "folio_idx": 7,
        "speaker": "stage_narrator",
        "label": "STAGE DIRECTION",
        "is_stage_direction": True,
        "is_dialogue": False,
        "stage_cue": "dagger_appears",
        "display_text": "Midnight. The court of Macbeth’s castle.",
        "tts_text": "Midnight. The court of Macbeth's castle.",
        "style": "calm, solemn, midnight classical stage direction",
        "pause_after_sec": STAGE_ACTION_PAUSE_SEC,
    },
    {
        "turn_idx": 45,
        "scene_idx": 3,
        "folio_idx": 7,
        "speaker": "macbeth",
        "label": "MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "Is this a dagger which I see before me,\n"
            "The handle toward my hand? Come, let me clutch thee.\n"
            "I have thee not, and yet I see thee still.\n"
            "Art thou not, fatal vision, sensible\n"
            "To feeling as to sight? or art thou but\n"
            "A dagger of the mind, a false creation,\n"
            "Proceeding from the heat-oppressed brain?"
        ),
        "tts_text": (
            "Is this a dagger which I see before me, "
            "the handle toward my hand? Come, let me clutch thee. "
            "I have thee not, and yet I see thee still. "
            "Art thou not, fatal vision, sensible "
            "to feeling as to sight? or art thou but "
            "a dagger of the mind, a false creation, "
            "proceeding from the heat-oppressed brain?"
        ),
        "style": "mesmerized, inward psychological intensity, resonant Scottish baritone",
        "pause_after_sec": 0.42,
    },
    {
        "turn_idx": 46,
        "scene_idx": 3,
        "folio_idx": 7,
        "speaker": "macbeth",
        "label": "MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "Thou marshall’st me the way that I was going;\n"
            "And such an instrument I was to use.\n"
            "I see thee still,\n"
            "And on thy blade and dudgeon gouts of blood,\n"
            "Which was not so before. There’s no such thing:\n"
            "It is the bloody business which informs\n"
            "Thus to mine eyes."
        ),
        "tts_text": (
            "Thou marshall'st me the way that I was going; "
            "and such an instrument I was to use. "
            "I see thee still, "
            "and on thy blade and dudgeon gouts of blood, "
            "which was not so before. There's no such thing: "
            "it is the bloody business which informs "
            "thus to mine eyes."
        ),
        "style": "dark, gripped fascination resolving into grim determination, resonant Scottish baritone",
        "pause_after_sec": 0.40,
    },
    {
        "turn_idx": 47,
        "scene_idx": 3,
        "folio_idx": 7,
        "speaker": "stage_narrator",
        "label": "STAGE DIRECTION",
        "is_stage_direction": True,
        "is_dialogue": False,
        "stage_cue": "bell_rings_exit_macbeth",
        "display_text": "A bell rings.",
        "tts_text": "A bell rings.",
        "style": "calm, solemn classical stage direction",
        "pause_after_sec": STAGE_ACTION_PAUSE_SEC,
    },
    {
        "turn_idx": 48,
        "scene_idx": 3,
        "folio_idx": 7,
        "speaker": "macbeth",
        "label": "MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "stage_cue_after": "exit_macbeth_to_chamber",
        "display_text": (
            "I go, and it is done; the bell invites me.\n"
            "Hear it not, Duncan; for it is a knell\n"
            "That summons thee to heaven or to hell."
        ),
        "tts_text": (
            "I go, and it is done; the bell invites me. "
            "Hear it not, Duncan; for it is a knell "
            "that summons thee to heaven or to hell."
        ),
        "style": "solemn, fateful, quiet dread, resonant Scottish baritone",
        "pause_after_sec": 1.60,
        "stage_action_hold_sec": 1.60,
    },
    {
        "turn_idx": 49,
        "scene_idx": 3,
        "folio_idx": 8,
        "speaker": "stage_narrator",
        "label": "STAGE DIRECTION",
        "is_stage_direction": True,
        "is_dialogue": False,
        "stage_cue": "enter_lady_macbeth_sc4",
        "display_text": "Exit Macbeth. Enter Lady Macbeth.",
        "tts_text": "Exit Macbeth. Enter Lady Macbeth.",
        "style": "calm, poised classical stage direction",
        "pause_after_sec": STAGE_ACTION_PAUSE_SEC,
    },
    {
        "turn_idx": 50,
        "scene_idx": 3,
        "folio_idx": 8,
        "speaker": "lady_macbeth",
        "label": "LADY MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "That which hath made them drunk hath made me bold;\n"
            "What hath quench’d them hath given me fire.\n"
            "Hark! Peace!\n"
            "It was the owl that shriek’d, the fatal bellman,\n"
            "Which gives the stern’st good-night. He is about it:\n"
            "The doors are open."
        ),
        "tts_text": (
            "That which hath made them drunk hath made me bold; "
            "what hath quenched them hath given me fire. "
            "Hark! Peace! "
            "It was the owl that shrieked, the fatal bellman, "
            "which gives the stern'st good-night. He is about it: "
            "the doors are open."
        ),
        "style": "taut, alert midnight tension, dark velvet mezzo-contralto, clear low-voiced intensity",
        "pause_after_sec": 0.40,
    },
    {
        "turn_idx": 51,
        "scene_idx": 3,
        "folio_idx": 8,
        "speaker": "stage_narrator",
        "label": "STAGE DIRECTION",
        "is_stage_direction": True,
        "is_dialogue": False,
        "stage_cue": "reenter_macbeth_daggers",
        "display_text": "Re-enter Macbeth, with two bloody daggers.",
        "tts_text": "Re-enter Macbeth, with two bloody daggers.",
        "style": "calm, tense classical stage direction",
        "pause_after_sec": 1.55,
        "stage_action_hold_sec": 1.55,
    },
    {
        "turn_idx": 52,
        "scene_idx": 3,
        "folio_idx": 8,
        "speaker": "macbeth",
        "label": "MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "I have done the deed. Didst thou not hear a noise?",
        "tts_text": "I have done the deed. Didst thou not hear a noise?",
        "style": "shaken, urgent, low-voiced Scottish baritone, clear tense articulation",
        "pause_after_sec": 0.32,
    },
    {
        "turn_idx": 53,
        "scene_idx": 3,
        "folio_idx": 8,
        "speaker": "lady_macbeth",
        "label": "LADY MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "I heard the owl scream and the crickets cry.\n"
            "Did not you speak?"
        ),
        "tts_text": "I heard the owl scream and the crickets cry. Did not you speak?",
        "style": "urgent, low-voiced, watchful mezzo-contralto",
        "pause_after_sec": 0.28,
    },
    {
        "turn_idx": 54,
        "scene_idx": 3,
        "folio_idx": 8,
        "speaker": "macbeth",
        "label": "MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "When?",
        "tts_text": "When?",
        "style": "taut, startled, low-voiced Scottish baritone",
        "pause_after_sec": 0.26,
    },
    {
        "turn_idx": 55,
        "scene_idx": 3,
        "folio_idx": 8,
        "speaker": "lady_macbeth",
        "label": "LADY MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "Now.",
        "tts_text": "Now.",
        "style": "immediate, sharp, low-voiced mezzo-contralto",
        "pause_after_sec": 0.30,
    },
    {
        "turn_idx": 56,
        "scene_idx": 3,
        "folio_idx": 8,
        "speaker": "macbeth",
        "label": "MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "As I descended?\n"
            "Methought I heard a voice cry ‘Sleep no more!\n"
            "Macbeth does murder sleep’ — the innocent sleep,\n"
            "Sleep that knits up the ravell’d sleave of care,\n"
            "The death of each day’s life, sore labour’s bath,\n"
            "Balm of hurt minds, great nature’s second course,\n"
            "Chief nourisher in life’s feast—"
        ),
        "tts_text": (
            "As I descended? "
            "Methought I heard a voice cry 'Sleep no more! "
            "Macbeth does murder sleep' — the innocent sleep, "
            "sleep that knits up the ravelled sleave of care, "
            "the death of each day's life, sore labour's bath, "
            "balm of hurt minds, great nature's second course, "
            "chief nourisher in life's feast—"
        ),
        "style": "anguished, haunted, deep lyrical grief and horror, resonant Scottish baritone",
        "pause_after_sec": round(PRE_FOLIO_BREATH_SEC + FOLIO_FADE_PAUSE_SEC, 4),
    },
    {
        "turn_idx": 57,
        "scene_idx": 3,
        "folio_idx": 9,
        "speaker": "lady_macbeth",
        "label": "LADY MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": "What do you mean?",
        "tts_text": "What do you mean?",
        "style": "sharp, impatient, commanding mezzo-contralto",
        "pause_after_sec": 0.34,
    },
    {
        "turn_idx": 58,
        "scene_idx": 3,
        "folio_idx": 9,
        "speaker": "macbeth",
        "label": "MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "Still it cried ‘Sleep no more!’ to all the house:\n"
            "‘Glamis hath murder’d sleep, and therefore Cawdor\n"
            "Shall sleep no more; Macbeth shall sleep no more!’"
        ),
        "tts_text": (
            "Still it cried 'Sleep no more!' to all the house: "
            "'Glahmz hath murdered sleep, and therefore Cawdor "
            "shall sleep no more; Macbeth shall sleep no more!'"
        ),
        "style": "rising dread and haunted despair, resonant Scottish baritone, pronounce Glahmz clearly",
        "pause_after_sec": 0.38,
    },
    {
        "turn_idx": 59,
        "scene_idx": 3,
        "folio_idx": 9,
        "speaker": "lady_macbeth",
        "label": "LADY MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "Why did you bring these daggers from the place?\n"
            "They must lie there: go carry them; and smear\n"
            "The sleepy grooms with blood."
        ),
        "tts_text": (
            "Why did you bring these daggers from the place? "
            "They must lie there: go carry them; and smear "
            "the sleepy grooms with blood."
        ),
        "style": "fierce, urgent, steely reprimand, dark mezzo-contralto",
        "pause_after_sec": 0.36,
    },
    {
        "turn_idx": 60,
        "scene_idx": 3,
        "folio_idx": 9,
        "speaker": "macbeth",
        "label": "MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "I’ll go no more:\n"
            "I am afraid to think what I have done;\n"
            "Look on’t again I dare not."
        ),
        "tts_text": (
            "I'll go no more: "
            "I am afraid to think what I have done; "
            "look on't again I dare not."
        ),
        "style": "horrified, resolute refusal, deep shaken Scottish baritone",
        "pause_after_sec": 0.40,
    },
    {
        "turn_idx": 61,
        "scene_idx": 3,
        "folio_idx": 9,
        "speaker": "stage_narrator",
        "label": "STAGE DIRECTION",
        "is_stage_direction": True,
        "is_dialogue": False,
        "stage_cue": "knocking_within",
        "display_text": "Knocking within.",
        "tts_text": "Knocking within.",
        "style": "calm, ominous classical stage direction",
        "pause_after_sec": STAGE_ACTION_PAUSE_SEC,
    },
    {
        "turn_idx": 62,
        "scene_idx": 3,
        "folio_idx": 9,
        "speaker": "macbeth",
        "label": "MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "Whence is that knocking?\n"
            "How is’t with me, when every noise appals me?\n"
            "What hands are here? ha! they pluck out mine eyes.\n"
            "Will all great Neptune’s ocean wash this blood\n"
            "Clean from my hand? No, this my hand will rather\n"
            "The multitudinous seas incarnadine,\n"
            "Making the green one red."
        ),
        "tts_text": (
            "Whence is that knocking? "
            "How is't with me, when every noise appals me? "
            "What hands are here? ha! they pluck out mine eyes. "
            "Will all great Neptune's ocean wash this blood "
            "clean from my hand? No, this my hand will rather "
            "the multitudinous seas incarnadine, "
            "making the green one red."
        ),
        "style": "startled dread rising to tragic, monumental horror, resonant Scottish baritone",
        "pause_after_sec": 0.40,
    },
    {
        "turn_idx": 63,
        "scene_idx": 3,
        "folio_idx": 9,
        "speaker": "lady_macbeth",
        "label": "LADY MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "My hands are of your colour; but I shame\n"
            "To wear a heart so white. I hear a knocking\n"
            "At the south entry: retire we to our chamber:\n"
            "A little water clears us of this deed."
        ),
        "tts_text": (
            "My hands are of your colour; but I shame "
            "to wear a heart so white. I hear a knocking "
            "at the south entry: retire we to our chamber: "
            "a little water clears us of this deed."
        ),
        "style": "cold, urgent composure and commanding resolve, dark mezzo-contralto",
        "pause_after_sec": 0.42,
    },
    {
        "turn_idx": 64,
        "scene_idx": 3,
        "folio_idx": 9,
        "speaker": "macbeth",
        "label": "MACBETH",
        "is_stage_direction": False,
        "is_dialogue": True,
        "stage_cue": None,
        "display_text": (
            "To know my deed, ’twere best not know myself.\n"
            "Wake Duncan with thy knocking! I would thou couldst!"
        ),
        "tts_text": (
            "To know my deed, 'twere best not know myself. "
            "Wake Duncan with thy knocking! I would thou couldst!"
        ),
        "style": "deep tragic remorse rising to an agonized final cry, resonant Scottish baritone",
        "pause_after_sec": OUTRO_HOLD_SEC,
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


def ensure_macbeth_voices(api_key: str, force: bool = False) -> dict[str, dict]:
    VOICES_DIR.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict] = {}
    if not force and MACBETH_VOICES_MANIFEST.exists():
        manifest = json.loads(MACBETH_VOICES_MANIFEST.read_text())

    updated = False
    for k, v in MACBETH_VOICES_SPEC.items():
        if (
            force
            or k not in manifest
            or manifest[k].get("voice_id") != v["voice_id"]
            or manifest[k].get("persona_style") != v["persona_style"]
        ):
            preview_path = VOICES_DIR / f"07_macbeth_{k}_preview.wav"
            manifest[k] = {
                "speaker_key": k,
                "voice_id": v["voice_id"],
                "display_name": v["display_name"],
                "gender": v["gender"],
                "language_code": v["language_code"],
                "persona_style": v["persona_style"],
                "prompt": v["prompt"],
                "preview_wav": str(preview_path.relative_to(ROOT)),
            }
            updated = True
            print(f"[VOICE OK] {k:16s} -> {v['voice_id']} ({v['display_name']})")

    if updated:
        MACBETH_VOICES_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    else:
        print(f"[SKIP] All 8 Macbeth studio voices already configured in {MACBETH_VOICES_MANIFEST.name}")
    return manifest


def synthesize_turn(
    tts_text: str,
    style: str,
    voice_id: str,
    out_wav_path: Path,
    api_key: str,
    retries: int = 4,
) -> Path:
    url = "https://generativelanguage.googleapis.com/v1beta/interactions"
    annotation = {"type": "speech_metadata"}
    if style:
        annotation["style"] = style

    payload = {
        "model": "gemini-3.8-flash-tts",
        "input": [
            {
                "type": "user_input",
                "content": [
                    {
                        "type": "text",
                        "text": tts_text,
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

    for attempt in range(1, retries + 1):
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
                        raw = base64.b64decode(block["data"])
                        out_wav_path.parent.mkdir(parents=True, exist_ok=True)
                        out_wav_path.write_bytes(raw)
                        return out_wav_path
            raise RuntimeError(f"No audio block returned: {json.dumps(data)[:300]}")
        except Exception as e:
            if attempt == retries:
                raise
            print(f"[TTS RETRY {attempt}/{retries}] {out_wav_path.name}: {e}")
            time.sleep(2 * attempt)
    raise RuntimeError(f"Failed to synthesize {out_wav_path}")


from voice_mastering import warm_master_voice_turn


def read_wav_pcm16(wav_path: Path) -> np.ndarray:
    """Read a WAV file (or raw PCM fallback) as 1D int16 numpy array at 24kHz mono,
    trimming leading/trailing dead digital silence > 80ms, applying warm zero-phase
    chest/presence/de-esser mastering, and applying a gentle 15ms fade-in/fade-out.
    """
    raw_bytes = wav_path.read_bytes()
    if raw_bytes[:4] == b"RIFF":
        with wave.open(str(wav_path), "rb") as wf:
            frames = wf.readframes(wf.getnframes())
            samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32)
    else:
        samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32)

    abs_s = np.abs(samples)
    non_silent = np.where(abs_s > 120)[0]
    if len(non_silent) > 0:
        pad = int(0.05 * SAMPLE_RATE)
        start = max(0, int(non_silent[0]) - pad)
        end = min(len(samples), int(non_silent[-1]) + pad)
        samples = samples[start:end]

    fade_len = min(int(0.015 * SAMPLE_RATE), len(samples) // 4)
    if fade_len > 0:
        fade_in = np.linspace(0.0, 1.0, fade_len, dtype=np.float32)
        fade_out = np.linspace(1.0, 0.0, fade_len, dtype=np.float32)
        samples[:fade_len] *= fade_in
        samples[-fade_len:] *= fade_out

    norm = warm_master_voice_turn(samples / 32768.0, sr=SAMPLE_RATE, target_rms=3450.0 / 32768.0)
    if fade_len > 0:
        norm[:fade_len] *= fade_in
        norm[-fade_len:] *= fade_out

    return np.clip(norm * 32767.0, -32767, 32767).astype(np.int16)


def write_wav_pcm16(wav_path: Path, samples: np.ndarray, sr: int = SAMPLE_RATE):
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(samples.astype(np.int16).tobytes())


def synthesize_stage_foley_pcm16(
    n_samples: int, kind: str, sr: int = SAMPLE_RATE, target_dbfs: float = FOLEY_TARGET_DBFS
) -> np.ndarray:
    """Synthesize realistic procedural stage foley using modal synthesis and bandpass filtering:
    - kind == 'thunder': distant rolling thunder rumble (38-160 Hz) + moorland wind (180-480 Hz)
      for Turn 0 ('Thunder and lightning. Enter three Witches.') at -26 dBFS.
    - kind == 'vanish_wind': eerie hollow moorland wind whoosh (140-640 Hz) + low sub-draught
      (55-160 Hz) for Turn 25 ('The Witches vanish.') at -26 dBFS.
    - kind == 'castle_bell': two deep, haunting bronze castle-bell tolls (modal inharmonic
      partials f0 = 196 Hz, 2.0*f0, 2.42*f0, 2.98*f0, 4.15*f0 with Rayleigh exponential decay
      over 3.2s) for Turn 47 ('A bell rings.') at -22 dBFS.
    - kind == 'castle_knocking': 3 heavy, reverberant oak-door thuds (75-180 Hz damped wooden
      impact transients + stone hall decay) for Turn 61 ('Knocking within.') and Turn 64 at -21 dBFS.
    """
    seed_map = {
        "thunder": 1606,
        "vanish_wind": 1623,
        "castle_bell": 1647,
        "castle_knocking": 1661,
    }
    rng = np.random.default_rng(seed_map.get(kind, 1606))
    white = rng.standard_normal(n_samples).astype(np.float64)
    sos_hp = signal.butter(2, 22.0, btype="highpass", fs=sr, output="sos")
    brown = signal.sosfiltfilt(sos_hp, np.cumsum(white))
    brown /= float(np.std(brown) + 1e-8)

    t = np.linspace(0.0, 1.0, n_samples, dtype=np.float64)
    t_sec = np.arange(n_samples, dtype=np.float64) / float(sr)

    if kind == "thunder":
        sos_rumble = signal.butter(2, [38.0, 155.0], btype="bandpass", fs=sr, output="sos")
        sos_wind = signal.butter(2, [170.0, 460.0], btype="bandpass", fs=sr, output="sos")
        rumble = signal.sosfiltfilt(sos_rumble, brown)
        wind = signal.sosfiltfilt(sos_wind, brown)
        env_roll1 = np.exp(-((t - 0.24) / 0.16) ** 2)
        env_roll2 = 0.85 * np.exp(-((t - 0.62) / 0.22) ** 2)
        env = np.clip(env_roll1 + env_roll2, 0.0, 1.0)
        raw = 0.82 * rumble * env + 0.24 * wind * np.sin(np.pi * t) ** 1.2
    elif kind == "vanish_wind":
        sos_low = signal.butter(2, [55.0, 165.0], btype="bandpass", fs=sr, output="sos")
        sos_mid = signal.butter(2, [165.0, 520.0], btype="bandpass", fs=sr, output="sos")
        sos_air = signal.butter(2, [420.0, 920.0], btype="bandpass", fs=sr, output="sos")
        low_part = signal.sosfiltfilt(sos_low, brown)
        mid_part = signal.sosfiltfilt(sos_mid, brown)
        air_part = signal.sosfiltfilt(sos_air, white)
        swell_mid = np.exp(-((t - 0.48) / 0.24) ** 2)
        swell_air = np.exp(-((t - 0.60) / 0.20) ** 2)
        raw = 0.55 * low_part * np.sin(np.pi * t) + 0.65 * mid_part * swell_mid + 0.18 * air_part * swell_air
    elif kind == "castle_bell":
        # Two deep, haunting bronze castle-bell tolls over 3.2s
        # Modal inharmonic partials: f0 = 196 Hz, 2.0*f0, 2.42*f0, 2.98*f0, 4.15*f0 (+ 0.5*f0 hum)
        f0 = 196.0
        modal_specs = [
            (0.50, 0.42, 1.85, 0.35),
            (1.00, 1.00, 1.45, 0.65),
            (2.00, 0.72, 1.05, 0.90),
            (2.42, 0.52, 0.82, 1.25),
            (2.98, 0.36, 0.68, 1.60),
            (4.15, 0.24, 0.48, 2.10),
        ]
        sos_clapper = signal.butter(2, [110.0, 340.0], btype="bandpass", fs=sr, output="sos")
        clapper_noise = signal.sosfiltfilt(sos_clapper, brown)
        raw = np.zeros(n_samples, dtype=np.float64)
        for t_hit, strike_gain in ((0.18, 1.0), (1.68, 0.92)):
            mask = t_sec >= t_hit
            if not np.any(mask):
                continue
            dt = t_sec[mask] - t_hit
            att = 1.0 - np.exp(-dt / 0.006)
            toll = np.zeros_like(dt)
            for ratio, amp, tau, beat_hz in modal_specs:
                fk = f0 * ratio
                mode_sig = (
                    0.78 * np.sin(2.0 * np.pi * fk * dt)
                    + 0.22 * np.sin(2.0 * np.pi * (fk + beat_hz) * dt + 0.4)
                )
                toll += amp * mode_sig * att * np.exp(-dt / tau)
            # Subtle cast-bronze clapper thud transient
            thud = 0.22 * clapper_noise[mask] * np.exp(-dt / 0.026)
            raw[mask] += strike_gain * (toll + thud)
    elif kind == "castle_knocking":
        # Three heavy, reverberant oak-door thuds (75-180 Hz damped wooden impact transients
        # + stone hall reverberant decay)
        sos_oak_low = signal.butter(2, [75.0, 180.0], btype="bandpass", fs=sr, output="sos")
        sos_oak_mid = signal.butter(2, [180.0, 410.0], btype="bandpass", fs=sr, output="sos")
        sos_stone_rev = signal.butter(2, [65.0, 240.0], btype="bandpass", fs=sr, output="sos")
        oak_low_noise = signal.sosfiltfilt(sos_oak_low, brown)
        oak_mid_noise = signal.sosfiltfilt(sos_oak_mid, white)
        stone_rev_noise = signal.sosfiltfilt(sos_stone_rev, brown)
        oak_low_noise /= float(np.std(oak_low_noise) + 1e-8)
        oak_mid_noise /= float(np.std(oak_mid_noise) + 1e-8)
        stone_rev_noise /= float(np.std(stone_rev_noise) + 1e-8)

        raw = np.zeros(n_samples, dtype=np.float64)
        for t_hit, knock_gain in ((0.22, 0.96), (0.92, 1.00), (1.62, 1.05)):
            mask = t_sec >= t_hit
            if not np.any(mask):
                continue
            dt = t_sec[mask] - t_hit
            att = 1.0 - np.exp(-dt / 0.0025)
            # Damped oak door modal frequencies (75-180 Hz) with slight impact pitch-drop
            phase1 = 2.0 * np.pi * 82.0 * (dt + 0.0030 * (1.0 - np.exp(-dt / 0.014)))
            phase2 = 2.0 * np.pi * 118.0 * (dt + 0.0025 * (1.0 - np.exp(-dt / 0.012)))
            phase3 = 2.0 * np.pi * 164.0 * (dt + 0.0020 * (1.0 - np.exp(-dt / 0.010)))
            wood_modes = (
                1.00 * np.sin(phase1) * np.exp(-dt / 0.085)
                + 0.72 * np.sin(phase2) * np.exp(-dt / 0.062)
                + 0.46 * np.sin(phase3) * np.exp(-dt / 0.045)
            ) * att
            wood_impact = (
                0.70 * oak_low_noise[mask] * np.exp(-dt / 0.055)
                + 0.32 * oak_mid_noise[mask] * np.exp(-dt / 0.022)
            )
            stone_tail = (
                0.34 * stone_rev_noise[mask] * (1.0 - np.exp(-dt / 0.018)) * np.exp(-dt / 0.38)
            )
            raw[mask] += knock_gain * (wood_modes + wood_impact + stone_tail)
    else:
        raise ValueError(f"Unknown foley kind: {kind}")

    # Smooth raised-cosine fade-in and fade-out so edges are 100% click-free
    fade_in_sec = 0.02 if kind in ("castle_bell", "castle_knocking") else 0.18
    fade_out_sec = 0.28 if kind in ("castle_bell", "castle_knocking") else 0.42
    fade_in = min(int(fade_in_sec * sr), n_samples // 4)
    fade_out = min(int(fade_out_sec * sr), n_samples // 3)
    if fade_in > 0:
        u_in = np.linspace(0.0, 1.0, fade_in)
        raw[:fade_in] *= 0.5 - 0.5 * np.cos(np.pi * u_in)
    if fade_out > 0:
        u_out = np.linspace(0.0, 1.0, fade_out)
        raw[-fade_out:] *= 0.5 + 0.5 * np.cos(np.pi * u_out)

    # Normalize RMS to target_dbfs
    target_rms = (10.0 ** (target_dbfs / 20.0)) * 32767.0
    cur_rms = float(np.sqrt(np.mean(raw ** 2)) + 1e-8)
    scaled = np.clip(raw * (target_rms / cur_rms), -18000.0, 18000.0)
    return scaled.astype(np.int16)


# =============================================================================
# Lyria 3.5 + FlashSR 48 kHz Upsampling & Intro/Outro Scoring
# =============================================================================
_FLASHSR_MODEL = None


def get_flashsr_upsampler():
    global _FLASHSR_MODEL
    if _FLASHSR_MODEL is not None:
        return _FLASHSR_MODEL
    if torch is None or not FLASHSR_CKPT.exists():
        return None
    import warnings
    warnings.filterwarnings("ignore", category=FutureWarning)
    from FastAudioSR import FASR

    upsampler = FASR(str(FLASHSR_CKPT))
    upsampler.model.dec.remove_weight_norm()
    upsampler.model.float()
    upsampler.model.eval()
    _FLASHSR_MODEL = upsampler
    return _FLASHSR_MODEL


def neural_flashsr_highband(music_48k: np.ndarray, sr: int = SCORED_SAMPLE_RATE) -> np.ndarray:
    upsampler = get_flashsr_upsampler()
    if upsampler is None:
        return np.zeros_like(music_48k, dtype=np.float32)

    torch.set_num_threads(4)
    mono_48k = np.mean(music_48k, axis=1).astype(np.float32)
    sos_aa = signal.butter(4, 7600.0, btype="lowpass", fs=sr, output="sos")
    mono_16k = signal.sosfiltfilt(sos_aa, mono_48k)[::3].astype(np.float32).copy()

    chunk_16k = 16000 * 8
    out_chunks = []
    with torch.no_grad():
        for i in range(0, len(mono_16k), chunk_16k):
            seg = mono_16k[i : i + chunk_16k]
            peak = float(np.max(np.abs(seg)) + 1e-6)
            t_in = torch.from_numpy((seg / peak).astype(np.float32)).view(1, 1, -1)
            y_sr = upsampler.model(t_in.to(upsampler.device)).reshape(-1).cpu().numpy()
            out_chunks.append((y_sr * peak).astype(np.float32))

    sr_mono = np.concatenate(out_chunks, axis=0)
    if len(sr_mono) < len(music_48k):
        sr_mono = np.pad(sr_mono, (0, len(music_48k) - len(sr_mono)))
    else:
        sr_mono = sr_mono[: len(music_48k)]

    sos_hb = signal.butter(2, [8000.0, 19500.0], btype="bandpass", fs=sr, output="sos")
    neural_hb = signal.sosfiltfilt(sos_hb, sr_mono).astype(np.float32)
    return np.stack([neural_hb, neural_hb], axis=1)


def generate_lyria_track(
    book_id: str, prompt: str, api_key: str, retries: int = 4, force: bool = False
) -> Path:
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    out_mp3 = MUSIC_DIR / f"{book_id}_lyria.mp3"
    if not force and out_mp3.exists() and out_mp3.stat().st_size > 100_000:
        print(f"[SKIP] {out_mp3.name} already exists ({out_mp3.stat().st_size} bytes)")
        return out_mp3

    url = "https://generativelanguage.googleapis.com/v1beta/interactions"
    payload = {
        "model": "lyria-3.5",
        "input": [{"type": "text", "text": prompt}],
    }

    for attempt in range(1, retries + 1):
        try:
            print(f"[LYRIA 3.5] Generating music for {book_id} (attempt {attempt})...")
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
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            for step in data.get("steps", []):
                for block in step.get("content", []):
                    if block.get("type") == "audio" and block.get("data"):
                        raw = base64.b64decode(block["data"])
                        out_mp3.write_bytes(raw)
                        print(f"[LYRIA OK] {out_mp3.name} ({len(raw)} bytes)")
                        return out_mp3
            raise RuntimeError(f"No audio block in Lyria 3.5 response for {book_id}")
        except Exception as e:
            if attempt == retries:
                raise
            print(f"[LYRIA RETRY {attempt}/{retries}] {book_id}: {e}")
            time.sleep(3 * attempt)
    raise RuntimeError(f"Failed to generate Lyria track for {book_id}")


def decode_audio_to_stereo_float(path: Path, sr: int = SCORED_SAMPLE_RATE) -> np.ndarray:
    cmd = [
        "ffmpeg",
        "-v",
        "error",
        "-i",
        str(path),
        "-af",
        f"aresample={sr}:resampler=soxr:precision=28",
        "-f",
        "f32le",
        "-acodec",
        "pcm_f32le",
        "-ac",
        "2",
        "-ar",
        str(sr),
        "-",
    ]
    raw = subprocess.check_output(cmd)
    arr = np.frombuffer(raw, dtype=np.float32)
    return arr.reshape(-1, 2)


def select_warm_ensemble_section(music: np.ndarray, sr: int = SCORED_SAMPLE_RATE) -> tuple[np.ndarray, float]:
    dur_sec = len(music) / float(sr)
    if dur_sec < 45.0:
        return music, 0.0

    sos_warm = signal.butter(2, [55.0, 480.0], btype="bandpass", fs=sr, output="sos")
    sos_harsh = signal.butter(2, [2000.0, 5000.0], btype="bandpass", fs=sr, output="sos")
    mono = np.mean(music, axis=1)
    warm_sig = signal.sosfiltfilt(sos_warm, mono)
    harsh_sig = signal.sosfiltfilt(sos_harsh, mono)

    win_sec = 12.0
    win_n = int(win_sec * sr)
    best_t = 20.0
    best_score = -1e9

    for t_cand in range(18, min(51, int(dur_sec - win_sec - 5))):
        idx0 = int(t_cand * sr)
        idx1 = idx0 + win_n
        w_rms = float(np.sqrt(np.mean(warm_sig[idx0:idx1] ** 2)) + 1e-8)
        h_rms = float(np.sqrt(np.mean(harsh_sig[idx0:idx1] ** 2)) + 1e-8)
        head_rms = float(np.sqrt(np.mean(warm_sig[idx0 : idx0 + int(1.5 * sr)] ** 2)) + 1e-8)
        score = 20.0 * np.log10(w_rms) + 8.0 * np.log10(head_rms) - 6.0 * np.log10(h_rms)
        if score > best_score:
            best_score = score
            best_t = float(t_cand)

    start_idx = int(best_t * sr)
    reordered = np.concatenate([music[start_idx:], music[:start_idx]], axis=0)
    fade_in = int(0.08 * sr)
    reordered[:fade_in] *= np.linspace(0.0, 1.0, fade_in, dtype=np.float32)[:, None]
    return reordered, best_t


def fit_music_length_equal_power(
    music: np.ndarray, target_samples: int, sr: int = SCORED_SAMPLE_RATE
) -> np.ndarray:
    fade_len = int(3.5 * sr)
    cur = music.copy()
    while len(cur) < target_samples + fade_len:
        theta = np.linspace(0.0, np.pi / 2.0, fade_len, dtype=np.float32)[:, None]
        tail = cur[-fade_len:]
        head = music[:fade_len]
        seam = tail * np.cos(theta) + head * np.sin(theta)
        cur = np.concatenate([cur[:-fade_len], seam, music[fade_len:]], axis=0)
    return cur[:target_samples]


def upsample_and_warm_master_music(music: np.ndarray, sr: int = SCORED_SAMPLE_RATE) -> np.ndarray:
    sos_dc = signal.butter(2, 20.0, btype="highpass", fs=sr, output="sos")
    y = signal.sosfiltfilt(sos_dc, music, axis=0).astype(np.float32)

    sos_low_shelf = signal.butter(2, 180.0, btype="lowpass", fs=sr, output="sos")
    low_band = signal.sosfiltfilt(sos_low_shelf, y, axis=0).astype(np.float32)
    shelf_gain = (10.0 ** (3.0 / 20.0)) - 1.0

    sos_body_band = signal.butter(2, [90.0, 320.0], btype="bandpass", fs=sr, output="sos")
    body_band = signal.sosfiltfilt(sos_body_band, y, axis=0).astype(np.float32)
    body_gain = (10.0 ** (1.5 / 20.0)) - 1.0

    y = y + shelf_gain * low_band + body_gain * body_band

    sos_tinny_band = signal.butter(2, [1200.0, 3800.0], btype="bandpass", fs=sr, output="sos")
    tinny_band = signal.sosfiltfilt(sos_tinny_band, y, axis=0).astype(np.float32)
    dip_factor = 1.0 - (10.0 ** (-2.5 / 20.0))
    y = y - dip_factor * tinny_band

    sos_hi_shelf = signal.butter(2, 5500.0, btype="highpass", fs=sr, output="sos")
    hi_band = signal.sosfiltfilt(sos_hi_shelf, y, axis=0).astype(np.float32)
    hi_cut = 1.0 - (10.0 ** (-3.0 / 20.0))
    y = y - hi_cut * hi_band

    sos_lp = signal.butter(4, 11500.0, btype="lowpass", fs=sr, output="sos")
    y = signal.sosfiltfilt(sos_lp, y, axis=0).astype(np.float32)
    return y.astype(np.float32)


def raised_cosine_window(
    t: np.ndarray, t0: float, t1: float, t2: float, t3: float
) -> np.ndarray:
    env = np.zeros_like(t, dtype=np.float32)
    m_in = (t >= t0) & (t < t1)
    if np.any(m_in) and t1 > t0:
        u = (t[m_in] - t0) / (t1 - t0)
        env[m_in] = 0.5 - 0.5 * np.cos(np.pi * u)
    m_hold = (t >= t1) & (t <= t2)
    env[m_hold] = 1.0
    m_out = (t > t2) & (t <= t3)
    if np.any(m_out) and t3 > t2:
        u = (t[m_out] - t2) / (t3 - t2)
        env[m_out] = 0.5 + 0.5 * np.cos(np.pi * u)
    return env


def build_structural_cue_envelope(
    book_rec: dict, target_n: int, sr: int = SCORED_SAMPLE_RATE
) -> np.ndarray:
    """Intro/outro-only music cue envelope:
    - Fades in 0.0s -> 1.2s, plays over the Title Card, opening page turn, and first lines,
      and fades out completely to 0.0 at 10.5s -> 16.5s.
    - Strictly 0.0 through the entire middle of the play (16.5s -> total_dur - 12.0s).
    - Fades back in over the last 12.0s (total_dur - 12.0s -> total_dur - 6.5s) and fades
      out at total_dur (total_dur - 2.0s -> total_dur).
    """
    t = np.arange(target_n, dtype=np.float32) / float(sr)
    total_dur = float(book_rec["total_duration_sec"])
    c_intro = raised_cosine_window(t, 0.0, 1.2, 10.5, 16.5)
    c_outro = raised_cosine_window(
        t,
        max(0.0, total_dur - 12.0),
        max(0.0, total_dur - 6.5),
        max(0.0, total_dur - 2.0),
        total_dur,
    )
    return np.maximum(c_intro, c_outro).astype(np.float32)


def build_chapter_bed_gain(
    book_rec: dict, gate: np.ndarray, target_n: int, sr: int = SCORED_SAMPLE_RATE
) -> np.ndarray:
    t = np.arange(target_n, dtype=np.float32) / float(sr)
    turns = book_rec["turns"]
    first_speech_start = float(turns[0]["start_sec"])
    last_speech_end = float(turns[-1]["end_sec"])

    body_bed = 0.31 - (0.31 - 0.28) * gate

    intro_level = 0.68
    ramp_down_start = max(0.0, first_speech_start - 0.9)
    ramp_down_end = first_speech_start + 0.3

    intro_weight = np.zeros_like(t, dtype=np.float32)
    intro_weight[t < ramp_down_start] = 1.0
    m_down = (t >= ramp_down_start) & (t <= ramp_down_end)
    if np.any(m_down) and ramp_down_end > ramp_down_start:
        u = (t[m_down] - ramp_down_start) / (ramp_down_end - ramp_down_start)
        intro_weight[m_down] = 0.5 + 0.5 * np.cos(np.pi * u)

    outro_level = 0.55
    ramp_up_start = last_speech_end + 0.15
    ramp_up_end = last_speech_end + 1.05

    outro_weight = np.zeros_like(t, dtype=np.float32)
    m_up = (t >= ramp_up_start) & (t < ramp_up_end)
    if np.any(m_up) and ramp_up_end > ramp_up_start:
        u = (t[m_up] - ramp_up_start) / (ramp_up_end - ramp_up_start)
        outro_weight[m_up] = 0.5 - 0.5 * np.cos(np.pi * u)
    outro_weight[t >= ramp_up_end] = 1.0

    gain = (
        intro_weight * intro_level
        + (1.0 - intro_weight) * (1.0 - outro_weight) * body_bed
        + outro_weight * outro_level
    )
    return gain.astype(np.float32)


def write_stereo_wav_pcm16(out_wav: Path, stereo_float: np.ndarray, sr: int = SCORED_SAMPLE_RATE):
    pcm16 = (np.clip(stereo_float, -0.99, 0.99) * 32767.0).astype(np.int16)
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm16.tobytes())


def mix_voice_and_music(
    book_rec: dict,
    voice_wav: Path,
    music_mp3: Path,
    out_wav: Path,
    sr: int = SCORED_SAMPLE_RATE,
    force_music_master: bool = False,
) -> Path:
    voice_st = decode_audio_to_stereo_float(voice_wav, sr=sr)
    target_n = len(voice_st)
    upsampled_music_wav = MUSIC_DIR / f"{book_rec['id']}_lyria.wav"

    music_raw = decode_audio_to_stereo_float(music_mp3, sr=sr)
    music_warm_sec, offset_sec = select_warm_ensemble_section(music_raw, sr=sr)
    core_len = min(len(music_warm_sec), int(52.0 * sr))
    music_core_mastered = upsample_and_warm_master_music(music_warm_sec[:core_len], sr=sr)
    music_mastered = fit_music_length_equal_power(music_core_mastered, target_n, sr=sr)

    mus_rms = float(np.sqrt(np.mean(music_mastered ** 2)))
    if mus_rms > 1e-6:
        music_mastered = music_mastered * (0.0473 / mus_rms)

    write_stereo_wav_pcm16(upsampled_music_wav, music_mastered * 3.2, sr=sr)

    # Smooth vocal activity envelope with 200ms lookahead and 950ms release hold
    voice_mono = np.mean(np.abs(voice_st), axis=1)
    hop = sr // 200
    n_hops = len(voice_mono) // hop + 1
    padded = np.pad(voice_mono, (0, n_hops * hop - len(voice_mono)))
    env_200 = np.max(padded.reshape(n_hops, hop), axis=1)

    active_200 = (env_200 > 0.010).astype(np.float32)
    kernel = np.ones(40 + 190, dtype=np.float32)
    dilated = np.convolve(np.pad(active_200, (190, 40)), kernel, mode="valid")[:n_hops]
    speech_gate_200 = np.clip(dilated, 0.0, 1.0)

    win = np.hanning(320).astype(np.float32)
    win /= np.sum(win)
    smooth_gate_200 = np.convolve(speech_gate_200, win, mode="same")

    gate = np.interp(
        np.arange(target_n, dtype=np.float32),
        np.arange(n_hops, dtype=np.float32) * hop,
        smooth_gate_200,
    ).astype(np.float32)

    # Dynamic Vocal-Pocket Dip ONLY during active speech (-2.0 dB zero-phase 800-2500 Hz)
    sos_vocal = signal.butter(2, [800.0, 2500.0], btype="bandpass", fs=sr, output="sos")
    vocal_band = signal.sosfiltfilt(sos_vocal, music_mastered, axis=0).astype(np.float32)
    vocal_dip_gain = 1.0 - (10.0 ** (-2.0 / 20.0))
    music_dynamic_eq = music_mastered - (vocal_dip_gain * gate[:, None]) * vocal_band

    chapter_bed_gain = build_chapter_bed_gain(book_rec, gate, target_n, sr=sr)
    cue_env = build_structural_cue_envelope(book_rec, target_n, sr=sr)
    total_music_gain = (chapter_bed_gain * cue_env)[:, None]

    mixed = voice_st + music_dynamic_eq * total_music_gain

    max_abs = float(np.max(np.abs(mixed)))
    if max_abs > 0.89:
        mixed = mixed * (0.89 / max_abs)
    mixed = np.clip(mixed, -0.99, 0.99)

    write_stereo_wav_pcm16(out_wav, mixed, sr=sr)
    print(
        f"[MIXED OK] {out_wav.name} (offset={offset_sec:.0f}s, "
        f"warm_eq=ON, "
        f"{out_wav.stat().st_size / (1024*1024):.2f} MB)"
    )
    return upsampled_music_wav


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-voices", action="store_true")
    parser.add_argument("--force-tts", action="store_true")
    parser.add_argument("--force-music", action="store_true")
    parser.add_argument("--turn", type=int, help="Optional 0-based turn index to regenerate")
    args = parser.parse_args()

    api_key = get_api_key()
    TURNS_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Create / verify the 8 Macbeth voices
    voices_map = ensure_macbeth_voices(api_key, force=args.force_voices)

    # 2. Synthesize all 65 Macbeth turns in parallel (bounded concurrency, reusing cached turns 0..27)
    tts_tasks = []
    for turn in MACBETH_TURNS_SPEC:
        t_idx = turn["turn_idx"]
        if args.turn is not None and t_idx != args.turn:
            continue
        wav_path = TURNS_DIR / f"{BOOK_ID}_turn_{t_idx:02d}.wav"
        if args.force_tts or args.turn is not None or not wav_path.exists():
            spk_info = voices_map[turn["speaker"]]
            voice_id = spk_info["voice_id"]
            persona_style = spk_info.get("persona_style", "")
            full_style = f"{persona_style}; {turn['style']}" if persona_style else turn["style"]
            tts_tasks.append((t_idx, turn, voice_id, full_style, wav_path))

    if tts_tasks:
        print(f"Synthesizing {len(tts_tasks)} Macbeth turns via Gemini 3.8 Flash TTS...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
            futs = {
                ex.submit(
                    synthesize_turn,
                    turn["tts_text"],
                    full_style,
                    voice_id,
                    wav_path,
                    api_key,
                ): (t_idx, wav_path)
                for (t_idx, turn, voice_id, full_style, wav_path) in tts_tasks
            }
            for fut in concurrent.futures.as_completed(futs):
                t_idx, wav_path = futs[fut]
                fut.result()
                print(f"[TTS OK] {wav_path.name} ({wav_path.stat().st_size} bytes)")
    else:
        print(f"[SKIP] All {len(MACBETH_TURNS_SPEC)} Macbeth turn WAVs already exist in audio/turns/")

    # 3. Assemble audio/07_macbeth_master.wav with exact timeline pauses & stage foley
    chunks = []
    opening_silence_sec = TITLE_CARD_HOLD_SEC + TITLE_TURN_PAUSE_SEC  # 2.6 + 2.8 = 5.4s
    opening_samples = int(round(opening_silence_sec * SAMPLE_RATE))
    chunks.append(np.zeros(opening_samples, dtype=np.int16))
    cursor_samples = opening_samples

    folio_boundaries: dict[int, float] = {0: TITLE_CARD_HOLD_SEC}
    scene_boundaries: dict[int, float] = {0: TITLE_CARD_HOLD_SEC}
    foley_overlays: list[tuple[int, int, str, int, float]] = []

    turn_records = []
    for i, turn in enumerate(MACBETH_TURNS_SPEC):
        t_idx = turn["turn_idx"]
        wav_path = TURNS_DIR / f"{BOOK_ID}_turn_{t_idx:02d}.wav"
        pcm = read_wav_pcm16(wav_path)

        turn_start_sample = cursor_samples
        start_sec = turn_start_sample / float(SAMPLE_RATE)
        dur_sec = len(pcm) / float(SAMPLE_RATE)
        end_sec = start_sec + dur_sec

        pause_sec = float(turn["pause_after_sec"])
        pause_samples = int(round(pause_sec * SAMPLE_RATE))

        chunks.append(pcm)
        chunks.append(np.zeros(pause_samples, dtype=np.int16))
        cursor_samples += len(pcm) + pause_samples

        # Record stage foley spans:
        # - Turn 0: distant rolling thunder (-26 dBFS)
        # - Turn 25: eerie moorland wind whoosh (-26 dBFS)
        # - Turn 47: two bronze castle-bell tolls over 3.2s (-22 dBFS)
        # - Turn 61: 3 heavy oak castle-gate knocks (-21 dBFS)
        # - Turn 64: 3 heavy oak castle-gate knocks (-21 dBFS)
        if t_idx == 0:
            f_start = max(0, turn_start_sample - int(0.15 * SAMPLE_RATE))
            f_end = turn_start_sample + len(pcm) + int(round(STAGE_ACTION_PAUSE_SEC * SAMPLE_RATE))
            foley_overlays.append((f_start, f_end, "thunder", t_idx, -26.0))
        elif t_idx == 25:
            f_start = turn_start_sample
            f_end = turn_start_sample + len(pcm) + int(round(STAGE_ACTION_PAUSE_SEC * SAMPLE_RATE))
            foley_overlays.append((f_start, f_end, "vanish_wind", t_idx, -26.0))
        elif t_idx == 47:
            f_start = turn_start_sample
            f_end = turn_start_sample + int(round(3.20 * SAMPLE_RATE))
            foley_overlays.append((f_start, f_end, "castle_bell", t_idx, -22.0))
        elif t_idx == 61:
            f_start = turn_start_sample
            f_end = turn_start_sample + len(pcm) + int(round(STAGE_ACTION_PAUSE_SEC * SAMPLE_RATE))
            foley_overlays.append((f_start, f_end, "castle_knocking", t_idx, -21.0))
        elif t_idx == 64:
            f_start = max(0, turn_start_sample - int(0.30 * SAMPLE_RATE))
            f_end = turn_start_sample + int(round(2.50 * SAMPLE_RATE))
            foley_overlays.append((f_start, f_end, "castle_knocking", t_idx, -21.0))

        # Compute folio & scene boundaries
        if i < len(MACBETH_TURNS_SPEC) - 1:
            cur_folio = turn["folio_idx"]
            next_folio = MACBETH_TURNS_SPEC[i + 1]["folio_idx"]
            cur_scene = turn["scene_idx"]
            next_scene = MACBETH_TURNS_SPEC[i + 1]["scene_idx"]

            if next_scene != cur_scene:
                hold_sec = float(turn.get("stage_action_hold_sec", 0.0))
                boundary_sec = round(end_sec + hold_sec, 4)
                scene_boundaries[next_scene] = boundary_sec
                folio_boundaries[next_folio] = boundary_sec
            elif next_folio != cur_folio:
                if "stage_cue_after" in turn:
                    boundary_sec = round(end_sec + float(turn.get("stage_action_hold_sec", pause_sec)), 4)
                else:
                    boundary_sec = round(end_sec + PRE_FOLIO_BREATH_SEC, 4)
                folio_boundaries[next_folio] = boundary_sec

        voice_info = voices_map[turn["speaker"]]
        rec = {
            "turn_idx": t_idx,
            "speaker_key": turn["speaker"],
            "speaker_label": turn["label"],
            "voice_id": voice_info["voice_id"],
            "voice_display_name": voice_info["display_name"],
            "is_stage_direction": bool(turn["is_stage_direction"]),
            "is_dialogue": bool(turn["is_dialogue"]),
            "stage_cue": turn["stage_cue"],
            "scene_idx": turn["scene_idx"],
            "folio_idx": turn["folio_idx"],
            "page_idx": turn["folio_idx"],
            "display_text": turn["display_text"],
            "tts_text": turn["tts_text"],
            "style": turn["style"],
            "start_sec": round(start_sec, 4),
            "end_sec": round(end_sec, 4),
            "duration_sec": round(dur_sec, 4),
            "pause_after_sec": round(pause_sec, 4),
            "wav_file": str(wav_path.relative_to(ROOT)),
        }
        if turn.get("stage_cue_after"):
            rec["stage_cue_after"] = turn["stage_cue_after"]
        if turn.get("stage_cue") or turn.get("stage_cue_after"):
            act_dur = float(turn.get("stage_action_hold_sec", STAGE_ACTION_PAUSE_SEC))
            rec["stage_action_start_sec"] = round(end_sec, 4)
            rec["stage_action_end_sec"] = round(end_sec + act_dur, 4)
            rec["stage_action_duration_sec"] = round(act_dur, 4)
        if "page_turn_pause_sec" in turn:
            hold_sec = float(turn.get("stage_action_hold_sec", 0.0))
            rec["page_turn_start_sec"] = round(end_sec + hold_sec, 4)
            rec["page_turn_end_sec"] = round(
                end_sec + hold_sec + turn["page_turn_pause_sec"], 4
            )
            rec["page_turn_duration_sec"] = turn["page_turn_pause_sec"]
        turn_records.append(rec)

    total_duration_sec = round(cursor_samples / float(SAMPLE_RATE), 4)
    master_pcm = np.concatenate(chunks).astype(np.int32)

    # Blend procedural stage foley into master_pcm
    foley_manifest_records = []
    for f_start, f_end, f_kind, t_idx, f_dbfs in foley_overlays:
        f_end = min(f_end, len(master_pcm))
        foley_seg = synthesize_stage_foley_pcm16(
            f_end - f_start, kind=f_kind, sr=SAMPLE_RATE, target_dbfs=f_dbfs
        )
        master_pcm[f_start:f_end] += foley_seg.astype(np.int32)
        seg_rms_dbfs = 20.0 * np.log10(
            float(np.sqrt(np.mean(foley_seg.astype(np.float64) ** 2))) / 32767.0 + 1e-12
        )
        foley_manifest_records.append({
            "turn_idx": t_idx,
            "kind": f_kind,
            "start_sec": round(f_start / float(SAMPLE_RATE), 4),
            "end_sec": round(f_end / float(SAMPLE_RATE), 4),
            "rms_dbfs": round(seg_rms_dbfs, 2),
        })
        print(
            f"[FOLEY OK] Turn {t_idx:02d} ({f_kind}): "
            f"{f_start / SAMPLE_RATE:.2f}s..{f_end / SAMPLE_RATE:.2f}s ({seg_rms_dbfs:.2f} dBFS)"
        )

    master_pcm_int16 = np.clip(master_pcm, -32767, 32767).astype(np.int16)
    master_wav_path = AUDIO_DIR / f"{BOOK_ID}_master.wav"
    write_wav_pcm16(master_wav_path, master_pcm_int16, sr=SAMPLE_RATE)
    print(f"[MASTER WAV] {master_wav_path.name}: {total_duration_sec:.2f}s ({len(turn_records)} turns)")

    # Build the 10 Right-Hand Text Folios (folio_idx = 0..9)
    folio_to_scene_cfg: dict[int, dict] = {}
    for sc_cfg in VISUAL_SCENES_SPEC:
        for f_idx in sc_cfg["folios"]:
            folio_to_scene_cfg[f_idx] = sc_cfg

    folios = []
    n_folios = len(FOLIO_TITLES)
    for f_idx in range(n_folios):
        sc_cfg = folio_to_scene_cfg[f_idx]
        s_idx = sc_cfg["scene_idx"]
        spread_num = sc_cfg["popup_spread_num"]
        f_start = round(folio_boundaries[f_idx], 4)
        f_end = round(folio_boundaries[f_idx + 1], 4) if f_idx < n_folios - 1 else total_duration_sec
        folios.append({
            "folio_idx": f_idx,
            "scene_idx": s_idx,
            "popup_spread_num": spread_num,
            "popup_spread_idx": spread_num - 1,
            "title": FOLIO_TITLES[f_idx],
            "caption": sc_cfg["caption"],
            "start_sec": f_start,
            "end_sec": f_end,
            "duration_sec": round(f_end - f_start, 4),
        })

    # Build the 4 Visual Scenes (scene_idx = 0, 1, 2, 3)
    scenes = []
    n_scenes = len(VISUAL_SCENES_SPEC)
    for sc_cfg in VISUAL_SCENES_SPEC:
        s_idx = sc_cfg["scene_idx"]
        spread_num = sc_cfg["popup_spread_num"]
        s_start = round(scene_boundaries[s_idx], 4)
        s_end = round(scene_boundaries[s_idx + 1], 4) if s_idx < n_scenes - 1 else total_duration_sec
        scenes.append({
            "scene_idx": s_idx,
            "id": f"scene_{s_idx + 1}",
            "popup_spread_num": spread_num,
            "popup_spread_idx": spread_num - 1,
            "folios": sc_cfg["folios"],
            "caption": sc_cfg["caption"],
            "image_file": f"illustrations/{BOOK_ID}_scene_{spread_num}.jpg",
            "bg_file": f"illustrations/popup/{BOOK_ID}_spread_{spread_num}_bg.jpg",
            "cutouts_file": f"illustrations/popup/{BOOK_ID}_spread_{spread_num}_cutouts.jpg",
            "start_sec": s_start,
            "end_sec": s_end,
            "duration_sec": round(s_end - s_start, 4),
        })

    book_record = {
        "id": BOOK_ID,
        "roman": "VII",
        "title": "The Tragedy of Macbeth",
        "author": "William Shakespeare",
        "year": "1623",
        "chapter_title": "Acts I & II · The Weird Sisters, Inverness & The Murder of Duncan",
        "genre": "Jacobean Tragedy · Victorian Toy Theatre Edition",
        "setting": "A Desert Moor, A Heath near Forres & Macbeth’s Castle at Inverness",
        "palette": {
            "paper": "#F3EDE0",
            "card": "#E8DFCE",
            "ink": "#191614",
            "muted": "#6B6257",
            "accent": "#7A2822",
            "rule": "#C9BFA9",
        },
        "title_card_end_sec": TITLE_CARD_HOLD_SEC,
        "opening_page_turn_pause_sec": TITLE_TURN_PAUSE_SEC,
        "stage_action_pause_sec": STAGE_ACTION_PAUSE_SEC,
        "page_turn_pause_sec": PAGE_TURN_PAUSE_SEC,
        "folio_crossfade_pause_sec": round(PRE_FOLIO_BREATH_SEC + FOLIO_FADE_PAUSE_SEC, 4),
        "outro_hold_sec": OUTRO_HOLD_SEC,
        "total_duration_sec": total_duration_sec,
        "unscored_master_wav": str(master_wav_path.relative_to(ROOT)),
        "master_wav": f"audio/{BOOK_ID}_master_scored.wav",
        "music_mp3": f"music/{BOOK_ID}_lyria.mp3",
        "music_wav": f"music/{BOOK_ID}_lyria.wav",
        "lyria_prompt": MACBETH_LYRIA_PROMPT,
        "char_sheet_image": f"illustrations/{BOOK_ID}_char_sheet.jpg",
        "foley_events": foley_manifest_records,
        "voices": voices_map,
        "scenes": scenes,
        "folios": folios,
        "turns": turn_records,
    }

    # 4. Generate Lyria 3.5 track + FlashSR 48 kHz upsampling + Intro/Outro scoring
    mp3_path = generate_lyria_track(
        BOOK_ID, MACBETH_LYRIA_PROMPT, api_key, force=args.force_music
    )
    scored_wav_path = AUDIO_DIR / f"{BOOK_ID}_master_scored.wav"
    upsampled_wav_path = mix_voice_and_music(
        book_record,
        master_wav_path,
        mp3_path,
        scored_wav_path,
        sr=SCORED_SAMPLE_RATE,
        force_music_master=args.force_music,
    )
    book_record["music_mp3"] = str(mp3_path.relative_to(ROOT))
    book_record["music_wav"] = str(upsampled_wav_path.relative_to(ROOT))
    book_record["master_wav"] = str(scored_wav_path.relative_to(ROOT))

    # 5. Save audio/macbeth_manifest.json (exposing both top-level fields and books=[book_record])
    manifest_payload = {
        "sample_rate": SAMPLE_RATE,
        "scored_sample_rate": SCORED_SAMPLE_RATE,
        **book_record,
        "books": [book_record],
    }
    MANIFEST_PATH.write_text(json.dumps(manifest_payload, indent=2) + "\n")
    print(f"[MANIFEST OK] Saved {MANIFEST_PATH} ({MANIFEST_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
