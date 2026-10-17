#!/usr/bin/env python3
"""Transparent, natural studio voice mastering helper for Gemini 3.8 Flash TTS turns.

Provides:
- Sub-rumble 2nd-order Butterworth high-pass at 60 Hz (zero-phase sosfiltfilt) to remove DC/sub-bass rumble while preserving 100% of natural vocal chest and full-bandwidth consonantal clarity up to 12 kHz+.
- Gentle active-speech RMS leveling (gain clamped to [0.70, 1.35]) so dialogue turns sit at a consistent, natural volume.
- Clean linear true-peak ceiling at -1.5 dBFS (0.84) with zero nonlinear np.tanh clipping and zero muffled EQ filters.
- 100% exact sample-length preservation (len(out) == len(in)).
"""

import numpy as np
from scipy import signal


def warm_master_voice_turn(
    samples_float32: np.ndarray,
    sr: int = 24000,
    target_rms: float = 0.112,
    is_thin_voice: bool | None = None,
) -> np.ndarray:
    """Apply transparent studio voice leveling (60 Hz sub-rumble HPF, gentle active RMS
    leveling, and linear true-peak ceiling at -1.5 dBFS) to a normalized [-1, 1] float32
    voice turn without any destructive EQ or low-pass filtering.
    Preserves exact sample length (`len(out) == len(samples_float32)`).
    """
    del is_thin_voice
    n_samples = len(samples_float32)
    if n_samples < 64:
        return samples_float32.astype(np.float32)

    y = samples_float32.astype(np.float64)

    # 1. Sub-rumble HPF: 2nd-order Butterworth high-pass at 60 Hz (zero-phase sosfiltfilt)
    sos_hp = signal.butter(2, 60.0, btype="highpass", fs=sr, output="sos")
    y = signal.sosfiltfilt(sos_hp, y)

    # 2. Gentle Active-Speech RMS Leveling + Clean Linear True-Peak Ceiling at -1.5 dBFS (0.84)
    active = y[np.abs(y) > 0.012]
    if len(active) > 100:
        active_rms = float(np.sqrt(np.mean(active ** 2)))
    else:
        active_rms = float(np.sqrt(np.mean(y ** 2)))

    if active_rms > 1e-5:
        gain = float(np.clip(target_rms / active_rms, 0.70, 1.35))
        y = y * gain

    max_abs = float(np.max(np.abs(y)))
    if max_abs > 0.84:
        y = y * (0.84 / max_abs)

    return y.astype(np.float32)

