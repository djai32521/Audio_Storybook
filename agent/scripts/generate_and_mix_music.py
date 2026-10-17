#!/usr/bin/env python3
"""Generate bespoke period-appropriate warm instrumental chamber scores for all 5 books
using Google Lyria 3.5 (model: "lyria-3.5" on POST /v1beta/interactions via Gemini API),
apply 48 kHz neural audio super-resolution (FlashSR / SnakeBeta AMPBlock0) + zero-phase
warm chamber mastering, and mix underneath the multi-voice audiobook readings with
continuous chapter-level bed gain (fading in/out ONLY at chapter start and chapter end,
never at page turns).
"""

import os
import sys

os.environ["OMP_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import base64
import concurrent.futures
import json
import subprocess
import time
import urllib.request
import wave
from pathlib import Path
import numpy as np
from scipy import signal

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

from books_spec import BOOKS_SPEC

ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = ROOT / "audio"
MUSIC_DIR = ROOT / "music"
MODELS_DIR = MUSIC_DIR / "models"
FLASHSR_CKPT = MODELS_DIR / "flashsr_upsampler.pth"
TIMELINE_PATH = AUDIO_DIR / "timeline_manifest.json"
SAMPLE_RATE = 24000

if str(MODELS_DIR) not in sys.path:
    sys.path.insert(0, str(MODELS_DIR))

LYRIA_PROMPTS = {
    "01_pride_and_prejudice": (
        "Warm Regency chamber string quartet and pianoforte in D major — resonant cello"
        " and contrabass arco and pizzicato foundation, warm viola and mellow violin,"
        " rich Steinway and fortepiano lower-midrange chords, recorded with close ribbon"
        " microphones in a warm wooden concert hall salon, lush 80 to 400 Hz acoustic"
        " body. Purely instrumental, no vocals, no percussion."
    ),
    "02_hound_of_the_baskervilles": (
        "Dark, velvety Victorian late-romantic low strings in D minor — deep resonant"
        " solo cello, warm double bass sustain, muted French horn and viola, rich"
        " low-register chamber warmth, Abbey Road studio ribbon microphone depth in a"
        " warm wooden concert hall, lush 80 to 400 Hz foundation. Purely instrumental,"
        " no vocals, no drums."
    ),
    "03_alice_in_wonderland": (
        "Warm pastoral English chamber ensemble in G major — rich cello and bassoon"
        " walking bassline, warm low-register clarinet, classical guitar and lute with"
        " mellow chamber strings, recorded with close ribbon microphones in a warm"
        " wooden concert hall, golden afternoon warmth, full 80 to 400 Hz acoustic"
        " body. Purely instrumental, no vocals, no percussion."
    ),
    "04_the_time_machine": (
        "Deep, resonant late-Victorian chamber strings and warm low grand piano in C"
        " minor — rich sustained cello and double bass foundation, warm viola melody,"
        " resonant low piano chords, recorded with close ribbon microphones in a warm"
        " wooden concert hall, lush acoustic hall bloom and 80 to 400 Hz body. Purely"
        " instrumental, no vocals, no drums."
    ),
    "05_tom_sawyer": (
        "Warm 19th-century Americana acoustic parlor ensemble in F major — rich upright"
        " double bass pizzicato, warm acoustic guitar thumb-picking, mellow cello and"
        " low-register fiddle harmony, recorded with close ribbon microphones on a warm"
        " wooden porch and parlor, full-bodied 80 to 400 Hz acoustic resonance. Purely"
        " instrumental, no vocals, no drums."
    ),
}

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


def neural_flashsr_highband(music_48k: np.ndarray, sr: int = 48000) -> np.ndarray:
    """Run the pretrained FlashSR (YatharthS/FlashSR HierSpeech++ SnakeBeta AMPBlock0)
    neural 48 kHz audio super-resolution model on the mid (L+R)/2 signal to reconstruct
    natural 8.0-20.0 kHz harmonic overtones above the MP3 codec roll-off.
    """
    upsampler = get_flashsr_upsampler()
    if upsampler is None:
        return np.zeros_like(music_48k, dtype=np.float32)

    torch.set_num_threads(4)
    # Downsample stereo mid to 16 kHz (exact 3:1 integer ratio from 48 kHz)
    mono_48k = np.mean(music_48k, axis=1).astype(np.float32)
    sos_aa = signal.butter(4, 7600.0, btype="lowpass", fs=sr, output="sos")
    mono_16k = signal.sosfiltfilt(sos_aa, mono_48k)[::3].astype(np.float32).copy()

    # Run FlashSR in 8s cache-friendly chunks
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

    # Zero-phase bandpass the reconstructed neural upper harmonics (8.0 - 19.5 kHz)
    sos_hb = signal.butter(2, [8000.0, 19500.0], btype="bandpass", fs=sr, output="sos")
    neural_hb = signal.sosfiltfilt(sos_hb, sr_mono).astype(np.float32)
    return np.stack([neural_hb, neural_hb], axis=1)


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


def generate_lyria_track(
    book_id: str, prompt: str, api_key: str, retries: int = 3, force: bool = False
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
                        print(f"[OK] {out_mp3.name} ({len(raw)} bytes)")
                        return out_mp3
            raise RuntimeError(f"No audio block in Lyria 3.5 response for {book_id}")
        except Exception as e:
            if attempt == retries:
                raise
            print(f"[RETRY {attempt}/{retries}] {book_id}: {e}")
            time.sleep(3 * attempt)
    raise RuntimeError(f"Failed to generate Lyria track for {book_id}")


def decode_audio_to_stereo_float(path: Path, sr: int = 48000) -> np.ndarray:
    """Decode any audio file via ffmpeg high-precision SoX resampler to (N, 2) float32 stereo at `sr` Hz."""
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


def select_warm_ensemble_section(music: np.ndarray, sr: int = 48000) -> tuple[np.ndarray, float]:
    """Scan the generated Lyria track between 18s and 50s to skip any sparse opening intro
    and start right where the full low-string/cello/piano ensemble has rich 50-500 Hz warmth.
    Applies a 0.08s micro-fade at the chosen entry point so sample-0 starts cleanly.
    """
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
    music: np.ndarray, target_samples: int, sr: int = 48000
) -> np.ndarray:
    """Ensure stereo `music` is at least `target_samples` long using a 3.5s
    equal-power quarter-sine crossfade if looping is needed, then trim to `target_samples`.
    """
    fade_len = int(3.5 * sr)
    cur = music.copy()
    while len(cur) < target_samples + fade_len:
        theta = np.linspace(0.0, np.pi / 2.0, fade_len, dtype=np.float32)[:, None]
        tail = cur[-fade_len:]
        head = music[:fade_len]
        seam = tail * np.cos(theta) + head * np.sin(theta)
        cur = np.concatenate([cur[:-fade_len], seam, music[fade_len:]], axis=0)
    return cur[:target_samples]


def upsample_and_warm_master_music(music: np.ndarray, sr: int = 48000) -> np.ndarray:
    """Zero-Phase Warm Chamber Mastering (no synthetic harmonic exciter or FlashSR fizz):
    1. 20 Hz sub-sonic DC removal only (zero-phase sosfiltfilt) — preserves full cello/contrabass fundamentals.
    2. Sub-bass & Warmth Foundation (50-280 Hz): +3.0 dB zero-phase low-shelf below 180 Hz
       + +1.5 dB warm low-mid body shelf across 90-320 Hz.
    3. Anti-Tinny Midrange Contour (1.2-3.8 kHz): -2.5 dB zero-phase bell cut centered at 2.2 kHz.
    4. Gentle High-Frequency Silk Roll-Off: -3.0 dB high-shelf cut above 5.5 kHz and 4th-order
       11.5 kHz lowpass filter to eliminate MP3 codec artifacts and upper-harmonic fizz.
    """
    # 1. 20 Hz sub-sonic DC removal only
    sos_dc = signal.butter(2, 20.0, btype="highpass", fs=sr, output="sos")
    y = signal.sosfiltfilt(sos_dc, music, axis=0).astype(np.float32)

    # 2. Sub-bass & Warmth Foundation (+3.0 dB low shelf below 180 Hz + +1.5 dB warm body 90-320 Hz)
    sos_low_shelf = signal.butter(2, 180.0, btype="lowpass", fs=sr, output="sos")
    low_band = signal.sosfiltfilt(sos_low_shelf, y, axis=0).astype(np.float32)
    shelf_gain = (10.0 ** (3.0 / 20.0)) - 1.0  # +0.4125 (+3.0 dB)

    sos_body_band = signal.butter(2, [90.0, 320.0], btype="bandpass", fs=sr, output="sos")
    body_band = signal.sosfiltfilt(sos_body_band, y, axis=0).astype(np.float32)
    body_gain = (10.0 ** (1.5 / 20.0)) - 1.0  # +0.1885 (+1.5 dB)

    y = y + shelf_gain * low_band + body_gain * body_band

    # 3. Anti-Tinny Midrange Contour (-2.5 dB zero-phase dip across 1200-3800 Hz)
    sos_tinny_band = signal.butter(2, [1200.0, 3800.0], btype="bandpass", fs=sr, output="sos")
    tinny_band = signal.sosfiltfilt(sos_tinny_band, y, axis=0).astype(np.float32)
    dip_factor = 1.0 - (10.0 ** (-2.5 / 20.0))  # 0.250 (-2.5 dB)
    y = y - dip_factor * tinny_band

    # 4. Gentle High-Frequency Silk Roll-Off (-3.0 dB above 5.5 kHz + 11.5 kHz lowpass)
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
    """Smooth trapezoidal cue envelope with raised-cosine fade-in [t0, t1],
    hold [t1, t2], and raised-cosine fade-out [t2, t3].
    """
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
    book_rec: dict, target_n: int, sr: int = 48000
) -> np.ndarray:
    """Chapter-boundary-only music cue envelope (NEVER at mid-chapter page changes):
    - Cue 1 (Chapter Start `c_intro`):
      Fades in from 0.0s -> 1.2s, holds across the Title Card (0.0..2.6s), the opening
      3D page turn (2.6..5.4s), and the opening narration lines (5.4..10.5s), then
      smoothly fades out to 0.0 (complete silence) between 10.5s and 16.5s.
    - Middle of the Chapter (including all mid-chapter page turns):
      Completely silent (0.0) from 16.5s until `total_dur - 12.0s`.
    - Cue 2 (Chapter End `c_outro`):
      Smoothly fades in for the closing lines & chapter curtain (`total_dur - 12.0s` ->
      `total_dur - 6.5s`), holds through the final sentence and into the outro hold, and
      fades out to 0.0 over the last 2.0s (`total_dur - 2.0s` -> `total_dur`).
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
    book_rec: dict, gate: np.ndarray, target_n: int, sr: int = 48000
) -> np.ndarray:
    """Build the ducking gain curve for the chapter start and chapter end music cues:
    - Opening Title Card + first page-turn intro (0.0s -> turns[0]['start_sec'] - 0.9s):
      warm welcoming foreground level (0.68).
    - Smooth 1.2s cosine ramp down to a gentle background bed level (0.28) once speech
      begins at `turns[0]['start_sec']` while `c_intro` is holding and fading out.
    - After the final spoken word (`last_turn['end_sec']`), gently rises to 0.55 over 0.9s
      for the chapter curtain before `c_outro` fades smoothly to 0.0.
    """
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


def write_stereo_wav_pcm16(out_wav: Path, stereo_float: np.ndarray, sr: int = 48000):
    pcm16 = (np.clip(stereo_float, -0.99, 0.99) * 32767.0).astype(np.int16)
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm16.tobytes())


def mix_voice_and_music(
    book_rec: dict, voice_wav: Path, music_mp3: Path, out_wav: Path, sr: int = 48000
) -> Path:
    """Upsample & master the Lyria 3.5 track at 48 kHz stereo (with FlashSR neural
    high-band restoration + zero-phase warm chamber mastering) and mix underneath
    the multi-voice audiobook chapter with chapter-boundary-only fading (`c_intro` + `c_outro`).
    """
    voice_st = decode_audio_to_stereo_float(voice_wav, sr=sr)
    target_n = len(voice_st)
    upsampled_music_wav = MUSIC_DIR / f"{book_rec['id']}_lyria.wav"

    if upsampled_music_wav.exists() and upsampled_music_wav.stat().st_size > 1_000_000:
        cached = decode_audio_to_stereo_float(upsampled_music_wav, sr=sr)
        if len(cached) >= target_n:
            music_mastered = cached[:target_n] / 3.2
        else:
            music_mastered = fit_music_length_equal_power(cached / 3.2, target_n, sr=sr)
        mus_rms = float(np.sqrt(np.mean(music_mastered ** 2)))
        if mus_rms > 1e-6:
            music_mastered = music_mastered * (0.0473 / mus_rms)
        offset_sec = -1.0
    else:
        cached = None

    if cached is None:
        music_raw = decode_audio_to_stereo_float(music_mp3, sr=sr)
        music_warm_sec, offset_sec = select_warm_ensemble_section(music_raw, sr=sr)
        core_len = min(len(music_warm_sec), int(52.0 * sr))
        music_core_mastered = upsample_and_warm_master_music(music_warm_sec[:core_len], sr=sr)
        music_mastered = fit_music_length_equal_power(music_core_mastered, target_n, sr=sr)

        mus_rms = float(np.sqrt(np.mean(music_mastered ** 2)))
        if mus_rms > 1e-6:
            music_mastered = music_mastered * (0.0473 / mus_rms)

        write_stereo_wav_pcm16(upsampled_music_wav, music_mastered * 3.2, sr=sr)

    # Compute smooth vocal activity envelope with 200ms lookahead and 950ms release hold
    voice_mono = np.mean(np.abs(voice_st), axis=1)
    hop = sr // 200  # 5ms hops
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

    # 5. Dynamic Vocal-Pocket Dip ONLY during active speech (-2.0 dB zero-phase 800-2500 Hz)
    sos_vocal = signal.butter(2, [800.0, 2500.0], btype="bandpass", fs=sr, output="sos")
    vocal_band = signal.sosfiltfilt(sos_vocal, music_mastered, axis=0).astype(np.float32)
    vocal_dip_gain = 1.0 - (10.0 ** (-2.0 / 20.0))  # 0.2057 (-2.0 dB)
    music_dynamic_eq = music_mastered - (vocal_dip_gain * gate[:, None]) * vocal_band

    # Continuous chapter bed gain + chapter-boundary-only raised-cosine cue envelope
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
    import multiprocessing
    api_key = get_api_key()
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:
        futs = {
            ex.submit(
                generate_lyria_track, book["id"], LYRIA_PROMPTS[book["id"]], api_key
            ): book["id"]
            for book in BOOKS_SPEC
        }
        mp3_map = {}
        for f in concurrent.futures.as_completed(futs):
            b_id = futs[f]
            mp3_map[b_id] = f.result()

    timeline = json.loads(TIMELINE_PATH.read_text())
    mix_jobs = []
    for book_rec in timeline["books"]:
        b_id = book_rec["id"]
        if b_id not in mp3_map:
            continue
        voice_wav = AUDIO_DIR / f"{b_id}_master.wav"
        scored_wav = AUDIO_DIR / f"{b_id}_master_scored.wav"
        mix_jobs.append((book_rec, voice_wav, mp3_map[b_id], scored_wav))

    ctx = multiprocessing.get_context("spawn")
    with concurrent.futures.ProcessPoolExecutor(max_workers=5, mp_context=ctx) as pool:
        fut_map = {
            pool.submit(mix_voice_and_music, br, vw, mm, sw, 48000): (br, sw, mm)
            for (br, vw, mm, sw) in mix_jobs
        }
        for fut in concurrent.futures.as_completed(fut_map):
            book_rec, scored_wav, mp3_path = fut_map[fut]
            upsampled_wav = fut.result()
            book_rec["master_wav"] = str(scored_wav.relative_to(ROOT))
            book_rec["music_mp3"] = str(mp3_path.relative_to(ROOT))
            book_rec["music_wav"] = str(upsampled_wav.relative_to(ROOT))

    TIMELINE_PATH.write_text(json.dumps(timeline, indent=2) + "\n")
    print(f"Updated {TIMELINE_PATH} with 48kHz FlashSR + warm-mastered Lyria 3.5 scored tracks.")


if __name__ == "__main__":
    main()
