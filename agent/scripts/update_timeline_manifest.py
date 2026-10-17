#!/usr/bin/env python3
"""Update audio/timeline_manifest.json and rebuild audio/01..05_*_master.wav
with decoupled Right-Hand Text Folios (3 readable pages per chapter) and
Left-Hand 3D Pop-Up Visual Scenes (page turns ONLY when the visual scene changes):
- Title Card hold: 0.0s -> 2.6s
- Opening 3D page turn + pop-up unfold pause: 2.8s (Turn 0 starts at 5.4s)
- Same-scene text folio transition (right-hand text updates, left-hand pop-up stays steady):
  0.40s post-sentence breath -> folio boundary -> 0.45s right-page text crossfade pause (0.85s total)
- New-scene 3D page turn transition (when visual scene changes mid-chapter):
  0.55s post-sentence breath -> scene/folio boundary -> 2.80s 3D page-turn + unfold pause
- Chapter outro hold: 2.4s after final turn
"""

import json
import wave
from pathlib import Path
import numpy as np

from books_spec import BOOKS_SPEC
from voice_mastering import warm_master_voice_turn

ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = ROOT / "audio"
TURNS_DIR = AUDIO_DIR / "turns"
MANIFEST_PATH = AUDIO_DIR / "timeline_manifest.json"

SAMPLE_RATE = 24000
TITLE_CARD_HOLD_SEC = 2.6
TITLE_TURN_PAUSE_SEC = 2.8
PRE_FOLIO_BREATH_SEC = 0.40
FOLIO_FADE_PAUSE_SEC = 0.45
PRE_PAGE_TURN_BREATH_SEC = 0.55
PAGE_TURN_PAUSE_SEC = 2.8
OUTRO_HOLD_SEC = 2.4

# 3 balanced right-hand text folios per chapter (folio_idx in {0, 1, 2})
# Keeps typography at comfortable 22-27pt without crowding the right-hand page.
TURN_FOLIO_MAP = {
    "01_pride_and_prejudice": [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2],
    "02_hound_of_the_baskervilles": [0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 2, 2],
    "03_alice_in_wonderland": [0, 0, 0, 0, 0, 1, 1, 1, 2],
    "04_the_time_machine": [0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2],
    "05_tom_sawyer": [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 2],
}

# Visual pop-up scenes per book:
# - Single-room chapters (Books 1, 2, 4) stay in 1 continuous visual pop-up scene across
#   all 3 text folios (zero mid-chapter page turns; only the right-hand text folio transitions).
# - Multi-location chapters (Books 3, 5) stay in Scene 0 across Folios 0 & 1, then perform
#   a full 3D page turn + pop-up unfold into Scene 1 at Folio 2 when the location changes.
BOOK_VISUAL_SCENES = {
    "01_pride_and_prejudice": [
        {
            "scene_idx": 0,
            "popup_spread_num": 1,
            "caption": "Longbourn Morning Room",
            "folios": [0, 1, 2],
        },
    ],
    "02_hound_of_the_baskervilles": [
        {
            "scene_idx": 0,
            "popup_spread_num": 2,
            "caption": "221B Baker Street",
            "folios": [0, 1, 2],
        },
    ],
    "03_alice_in_wonderland": [
        {
            "scene_idx": 0,
            "popup_spread_num": 2,
            "caption": "On the Sunny Riverbank",
            "folios": [0, 1],
        },
        {
            "scene_idx": 1,
            "popup_spread_num": 3,
            "caption": "Down the Deep Well",
            "folios": [2],
        },
    ],
    "04_the_time_machine": [
        {
            "scene_idx": 0,
            "popup_spread_num": 1,
            "caption": "The Firelit Smoking-Room",
            "folios": [0, 1, 2],
        },
    ],
    "05_tom_sawyer": [
        {
            "scene_idx": 0,
            "popup_spread_num": 2,
            "caption": "Inside Aunt Polly’s Cottage",
            "folios": [0, 1],
        },
        {
            "scene_idx": 1,
            "popup_spread_num": 3,
            "caption": "Over the High Board-Fence",
            "folios": [2],
        },
    ],
}


def read_wav_pcm16(wav_path: Path) -> np.ndarray:
    """Read a turn WAV file as 1D int16 numpy array at 24kHz mono,
    trimming leading/trailing dead digital silence > 80ms, applying a gentle 15ms
    cosine fade-in/fade-out, and normalizing active speech RMS to ~ -19.5 dBFS.
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


def write_wav_pcm16(wav_path: Path, samples: np.ndarray):
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(samples.astype(np.int16).tobytes())


def main():
    spec_by_id = {b["id"]: b for b in BOOKS_SPEC}
    data = json.loads(MANIFEST_PATH.read_text())

    for book in data["books"]:
        bid = book["id"]
        if bid not in TURN_FOLIO_MAP:
            continue
        fmap = TURN_FOLIO_MAP[bid]
        vis_scenes_cfg = BOOK_VISUAL_SCENES[bid]
        turns = book["turns"]
        spec_turns = spec_by_id[bid]["turns"]
        assert len(turns) == len(fmap) == len(spec_turns), (
            f"{bid}: {len(turns)} != {len(fmap)}"
        )

        # Map each folio_idx (0, 1, 2) to its visual scene descriptor
        folio_to_scene_cfg: dict[int, dict] = {}
        for sc_cfg in vis_scenes_cfg:
            for f_idx in sc_cfg["folios"]:
                folio_to_scene_cfg[f_idx] = sc_cfg

        for i, t in enumerate(turns):
            f_idx = fmap[i]
            s_idx = folio_to_scene_cfg[f_idx]["scene_idx"]
            t["folio_idx"] = f_idx
            t["page_idx"] = f_idx
            t["scene_idx"] = s_idx

        chunks = []
        # Title card hold (2.6s) + opening 3D page turn & pop-up unfold pause (2.8s) = 5.4s
        opening_silence_sec = TITLE_CARD_HOLD_SEC + TITLE_TURN_PAUSE_SEC
        opening_samples = int(round(opening_silence_sec * SAMPLE_RATE))
        chunks.append(np.zeros(opening_samples, dtype=np.int16))
        cursor_samples = opening_samples

        folio_boundaries: dict[int, float] = {0: TITLE_CARD_HOLD_SEC}
        scene_boundaries: dict[int, float] = {0: TITLE_CARD_HOLD_SEC}

        for i, t in enumerate(turns):
            wav_path = ROOT / t["wav_file"]
            pcm = read_wav_pcm16(wav_path)
            start_sec = cursor_samples / SAMPLE_RATE
            dur_sec = len(pcm) / SAMPLE_RATE
            end_sec = start_sec + dur_sec

            chunks.append(pcm)
            cursor_samples += len(pcm)

            t["start_sec"] = round(start_sec, 4)
            t["end_sec"] = round(end_sec, 4)
            t["duration_sec"] = round(dur_sec, 4)

            if i < len(turns) - 1:
                cur_folio = fmap[i]
                next_folio = fmap[i + 1]
                cur_scene = folio_to_scene_cfg[cur_folio]["scene_idx"]
                next_scene = folio_to_scene_cfg[next_folio]["scene_idx"]

                if next_folio == cur_folio:
                    # Normal conversational pause within the same right-hand text folio
                    pause_sec = spec_turns[i].get("pause_after_ms", 380) / 1000.0
                    pause_samples = int(round(pause_sec * SAMPLE_RATE))
                    chunks.append(np.zeros(pause_samples, dtype=np.int16))
                    cursor_samples += pause_samples
                    t["pause_after_sec"] = round(pause_sec, 4)
                elif next_scene == cur_scene:
                    # Same visual pop-up scene, next right-hand text folio:
                    # No 3D page turn! 0.40s post-sentence breath -> folio boundary ->
                    # 0.45s smooth right-page text crossfade before speech resumes.
                    breath_samples = int(round(PRE_FOLIO_BREATH_SEC * SAMPLE_RATE))
                    boundary_samples = cursor_samples + breath_samples
                    boundary_sec = round(boundary_samples / SAMPLE_RATE, 4)
                    folio_boundaries[next_folio] = boundary_sec

                    fade_pause_samples = int(round(FOLIO_FADE_PAUSE_SEC * SAMPLE_RATE))
                    total_pause_samples = breath_samples + fade_pause_samples
                    chunks.append(np.zeros(total_pause_samples, dtype=np.int16))
                    cursor_samples += total_pause_samples
                    t["pause_after_sec"] = round(total_pause_samples / SAMPLE_RATE, 4)
                else:
                    # New visual pop-up scene AND new text folio:
                    # 1) 0.55s natural post-sentence breath before the 3D page begins turning
                    breath_samples = int(round(PRE_PAGE_TURN_BREATH_SEC * SAMPLE_RATE))
                    boundary_samples = cursor_samples + breath_samples
                    boundary_sec = round(boundary_samples / SAMPLE_RATE, 4)
                    folio_boundaries[next_folio] = boundary_sec
                    scene_boundaries[next_scene] = boundary_sec

                    # 2) 2.8s dedicated silence for 3D page turn + pop-up character unfold
                    turn_pause_samples = int(round(PAGE_TURN_PAUSE_SEC * SAMPLE_RATE))
                    total_pause_samples = breath_samples + turn_pause_samples
                    chunks.append(np.zeros(total_pause_samples, dtype=np.int16))
                    cursor_samples += total_pause_samples
                    t["pause_after_sec"] = round(total_pause_samples / SAMPLE_RATE, 4)
            else:
                # End of chapter tail: 2.4s silence for gentle music swell & fade-out
                outro_samples = int(round(OUTRO_HOLD_SEC * SAMPLE_RATE))
                chunks.append(np.zeros(outro_samples, dtype=np.int16))
                cursor_samples += outro_samples
                t["pause_after_sec"] = round(OUTRO_HOLD_SEC, 4)

        total_dur = round(cursor_samples / SAMPLE_RATE, 4)
        book["title_card_end_sec"] = TITLE_CARD_HOLD_SEC
        book["total_duration_sec"] = total_dur

        master_pcm = np.concatenate(chunks)
        master_wav_path = AUDIO_DIR / f"{bid}_master.wav"
        write_wav_pcm16(master_wav_path, master_pcm)

        # Build the 3 right-hand text folio descriptors
        n_folios = 3
        new_folios = []
        for f_idx in range(n_folios):
            sc_cfg = folio_to_scene_cfg[f_idx]
            s_idx = sc_cfg["scene_idx"]
            spread_num = sc_cfg["popup_spread_num"]
            f_start = round(folio_boundaries[f_idx], 4)
            f_end = (
                round(folio_boundaries[f_idx + 1], 4)
                if f_idx < n_folios - 1
                else total_dur
            )
            new_folios.append(
                {
                    "folio_idx": f_idx,
                    "scene_idx": s_idx,
                    "popup_spread_num": spread_num,
                    "popup_spread_idx": spread_num - 1,
                    "title": sc_cfg["caption"],
                    "start_sec": f_start,
                    "end_sec": f_end,
                    "duration_sec": round(f_end - f_start, 4),
                }
            )
        book["folios"] = new_folios

        # Build the visual pop-up scene descriptors (1 or 2 scenes per chapter)
        n_scenes = len(vis_scenes_cfg)
        new_scenes = []
        for sc_cfg in vis_scenes_cfg:
            s_idx = sc_cfg["scene_idx"]
            spread_num = sc_cfg["popup_spread_num"]
            s_start = round(scene_boundaries[s_idx], 4)
            s_end = (
                round(scene_boundaries[s_idx + 1], 4)
                if s_idx < n_scenes - 1
                else total_dur
            )
            new_scenes.append(
                {
                    "scene_idx": s_idx,
                    "id": f"scene_{s_idx + 1}",
                    "popup_spread_num": spread_num,
                    "popup_spread_idx": spread_num - 1,
                    "folios": sc_cfg["folios"],
                    "caption": sc_cfg["caption"],
                    "image_file": f"illustrations/{bid}_scene_{spread_num}.jpg",
                    "bg_file": f"illustrations/popup/{bid}_spread_{spread_num}_bg.jpg",
                    "cutouts_file": f"illustrations/popup/{bid}_spread_{spread_num}_cutouts.jpg",
                    "start_sec": s_start,
                    "end_sec": s_end,
                    "duration_sec": round(s_end - s_start, 4),
                }
            )

        book["scenes"] = new_scenes
        print(
            f"[OK] {bid}: total={total_dur:.2f}s, scenes={n_scenes}, "
            + ", ".join(
                f"F{f['folio_idx']+1}(S{f['scene_idx']+1},sp{f['popup_spread_num']})=[{f['start_sec']:.2f}s..{f['end_sec']:.2f}s]"
                for f in new_folios
            )
        )

    MANIFEST_PATH.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Updated {MANIFEST_PATH} and rebuilt audio/01..05_*_master.wav")


if __name__ == "__main__":
    main()
