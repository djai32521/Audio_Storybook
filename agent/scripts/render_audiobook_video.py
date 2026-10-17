#!/usr/bin/env python3
"""Render 1080p 24fps 3D Multi-Plane Paper Pop-Up Book Video Audiobooks for Books 1-5.

Key craft & visual architecture:
1. True Multi-Plane Paper Pop-Up Diorama on each spread (3 spreads per chapter,
   ~35-45 seconds per spread, so the page turns only twice per chapter):
   - Plane 0 (z = 0.08): Exact 16:9 (896x504) recessed period stage backplate with a
     vertical center-fold crease and subtle inner stage recess shading.
   - Plane 1 (z = 0.44): Midground die-cut cardstock set-piece.
   - Plane 2 (z = 0.76): Foreground die-cut character standee A with a 7px cream laid-paper
     die-cut margin, 1.5px 3D bevelled cardstock edge, bottom fold-tab, and drop shadow.
   - Plane 3 (z = 0.94): Near-foreground die-cut character standee B with die-cut cardstock
     margin, bevelled edge, and multi-plane drop shadow.
2. Physical 3D Spine-Hinged Page Turn & Pop-Up Unfolding / Folding:
   - Hinged at the center book spine (spine_x = 1016): during the first half of the turn
     (0.0s .. 0.68s), the right-hand leaf lifts and curls toward the spine while the
     outgoing left-hand pop-up cutouts fold flat down onto the page.
   - During the second half (0.68s .. 1.45s), the leaf flips across the center spine onto
     the left side of the book with 3D cylindrical shading, horizontal foreshortening, and
     vertical perspective arch curvature.
   - From 1.15s .. 2.75s (during the dedicated 2.8s page-turn pause before speech begins),
     the new spread's 3D pop-up cutouts visibly hinge upright from flat on the paper into 3D.
3. Classic 3-State Paragraph Ink Highlighting on the Right-Hand Page:
   - Active turn in full dark ink, past turns in softened ink, future turns in veiled ink
     (with all turns in future ink during the 2.8s page-turn pause before Turn 0 speaks),
     smoothly crossfading over 0.22s as each turn begins.
"""

import argparse
import concurrent.futures
import json
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
TIMELINE_PATH = ROOT / "audio" / "timeline_manifest.json"
FONTS_DIR = ROOT / "fonts"
VIDEO_DIR = ROOT / "video"
PREVIEW_DIR = VIDEO_DIR / "previews"

W, H = 1920, 1080
FPS = 24
SPINE_X = 1016

# Exact 16:9 pop-up stage geometry on the left page of the open book spread (896 / 504 = 1.7778)
STAGE_X0, STAGE_Y0 = 68, 204
STAGE_W, STAGE_H = 896, 504

# Left-page ROI matches the exact 16:9 stage box so zero standee pixels ever protrude outside
ROI_OX, ROI_OY = STAGE_X0, STAGE_Y0
ROI_RX1, ROI_RY1 = STAGE_X0 + STAGE_W, STAGE_Y0 + STAGE_H
ROI_W, ROI_H = STAGE_W, STAGE_H

# Per-book, per-spread (0, 1, 2) configuration for the 3 die-cut cutouts (Left, Center, Right)
POPUP_STAGE_LAYOUT = {
    "01_pride_and_prejudice": {
        0: {
            "center": {"x_rel": 0.50, "y_base": 718, "z": 0.44, "target_h": 250, "flip_x": False, "speaker": None},
            "left":   {"x_rel": 0.23, "y_base": 746, "z": 0.78, "target_h": 402, "flip_x": False, "speaker": "mrs_bennet"},
            "right":  {"x_rel": 0.79, "y_base": 754, "z": 0.94, "target_h": 356, "flip_x": False, "speaker": "mr_bennet"},
        },
        1: {
            "center": {"x_rel": 0.50, "y_base": 712, "z": 0.42, "target_h": 260, "flip_x": False, "speaker": None},
            "left":   {"x_rel": 0.23, "y_base": 748, "z": 0.78, "target_h": 400, "flip_x": False, "speaker": "mr_bennet"},
            "right":  {"x_rel": 0.79, "y_base": 756, "z": 0.94, "target_h": 395, "flip_x": False, "speaker": "mrs_bennet"},
        },
        2: {
            "center": {"x_rel": 0.50, "y_base": 720, "z": 0.44, "target_h": 245, "flip_x": False, "speaker": None},
            "right":  {"x_rel": 0.79, "y_base": 746, "z": 0.76, "target_h": 405, "flip_x": False, "speaker": "mr_bennet"},
            "left":   {"x_rel": 0.23, "y_base": 756, "z": 0.94, "target_h": 395, "flip_x": False, "speaker": "mrs_bennet"},
        },
    },
    "02_hound_of_the_baskervilles": {
        0: {
            "center": {"x_rel": 0.50, "y_base": 722, "z": 0.44, "target_h": 265, "flip_x": False, "speaker": None},
            "left":   {"x_rel": 0.23, "y_base": 748, "z": 0.78, "target_h": 385, "flip_x": False, "speaker": "sherlock_holmes"},
            "right":  {"x_rel": 0.79, "y_base": 758, "z": 0.94, "target_h": 385, "flip_x": False, "speaker": "dr_watson"},
        },
        1: {
            "center": {"x_rel": 0.50, "y_base": 714, "z": 0.42, "target_h": 271, "flip_x": False, "speaker": None},
            "right":  {"x_rel": 0.79, "y_base": 748, "z": 0.78, "target_h": 337, "flip_x": False, "speaker": "sherlock_holmes"},
            "left":   {"x_rel": 0.23, "y_base": 758, "z": 0.94, "target_h": 385, "flip_x": False, "speaker": "dr_watson"},
        },
        2: {
            "center": {"x_rel": 0.50, "y_base": 720, "z": 0.42, "target_h": 260, "flip_x": False, "speaker": None},
            "left":   {"x_rel": 0.23, "y_base": 748, "z": 0.78, "target_h": 385, "flip_x": False, "speaker": "dr_watson"},
            "right":  {"x_rel": 0.79, "y_base": 758, "z": 0.94, "target_h": 385, "flip_x": False, "speaker": "sherlock_holmes"},
        },
    },
    "03_alice_in_wonderland": {
        0: {
            "center": {"x_rel": 0.50, "y_base": 716, "z": 0.44, "target_h": 260, "flip_x": False, "speaker": None},
            "left":   {"x_rel": 0.23, "y_base": 746, "z": 0.76, "target_h": 395, "flip_x": False, "speaker": "carroll_narrator"},
            "right":  {"x_rel": 0.78, "y_base": 756, "z": 0.94, "target_h": 350, "flip_x": False, "speaker": "alice"},
        },
        1: {
            "center": {"x_rel": 0.50, "y_base": 714, "z": 0.42, "target_h": 250, "flip_x": False, "speaker": None},
            "left":   {"x_rel": 0.22, "y_base": 748, "z": 0.78, "target_h": 415, "flip_x": False, "speaker": "alice"},
            "right":  {"x_rel": 0.79, "y_base": 758, "z": 0.94, "target_h": 360, "flip_x": False, "speaker": "white_rabbit"},
        },
        2: {
            "left":   {"x_rel": 0.22, "y_base": 560, "z": 0.46, "target_h": 152, "flip_x": False, "speaker": None},
            "right":  {"x_rel": 0.80, "y_base": 620, "z": 0.68, "target_h": 213, "flip_x": False, "speaker": None},
            "center": {"x_rel": 0.50, "y_base": 695, "z": 0.95, "target_h": 424, "flip_x": False, "speaker": "alice"},
        },
    },
    "04_the_time_machine": {
        0: {
            "center": {"x_rel": 0.50, "y_base": 714, "z": 0.42, "target_h": 259, "flip_x": False, "speaker": None},
            "right":  {"x_rel": 0.78, "y_base": 748, "z": 0.76, "target_h": 332, "flip_x": False, "speaker": "psychologist"},
            "left":   {"x_rel": 0.22, "y_base": 758, "z": 0.94, "target_h": 385, "flip_x": False, "speaker": "time_traveller"},
        },
        1: {
            "center": {"x_rel": 0.50, "y_base": 722, "z": 0.44, "target_h": 255, "flip_x": False, "speaker": None},
            "left":   {"x_rel": 0.23, "y_base": 748, "z": 0.78, "target_h": 385, "flip_x": False, "speaker": "time_traveller"},
            "right":  {"x_rel": 0.78, "y_base": 756, "z": 0.94, "target_h": 385, "flip_x": False, "speaker": "filby"},
        },
        2: {
            "center": {"x_rel": 0.50, "y_base": 726, "z": 0.50, "target_h": 255, "flip_x": False, "speaker": None},
            "left":   {"x_rel": 0.22, "y_base": 752, "z": 0.82, "target_h": 385, "flip_x": False, "speaker": "time_traveller"},
            "right":  {"x_rel": 0.79, "y_base": 758, "z": 0.94, "target_h": 385, "flip_x": False, "speaker": "filby"},
        },
    },
    "05_tom_sawyer": {
        0: {
            "center": {"x_rel": 0.52, "y_base": 720, "z": 0.44, "target_h": 260, "flip_x": False, "speaker": None},
            "right":  {"x_rel": 0.80, "y_base": 742, "z": 0.72, "target_h": 348, "flip_x": False, "speaker": None},
            "left":   {"x_rel": 0.22, "y_base": 758, "z": 0.94, "target_h": 415, "flip_x": False, "speaker": "aunt_polly"},
        },
        1: {
            "left":   {"x_rel": 0.22, "y_base": 716, "z": 0.42, "target_h": 299, "flip_x": False, "speaker": None},
            "center": {"x_rel": 0.52, "y_base": 748, "z": 0.78, "target_h": 421, "flip_x": False, "speaker": "aunt_polly"},
            "right":  {"x_rel": 0.80, "y_base": 758, "z": 0.94, "target_h": 348, "flip_x": False, "speaker": "tom_sawyer"},
        },
        2: {
            "center": {"x_rel": 0.50, "y_base": 716, "z": 0.44, "target_h": 183, "flip_x": False, "speaker": None},
            "right":  {"x_rel": 0.78, "y_base": 610, "z": 0.78, "target_h": 299, "flip_x": False, "speaker": "tom_sawyer"},
            "left":   {"x_rel": 0.23, "y_base": 758, "z": 0.94, "target_h": 402, "flip_x": False, "speaker": "aunt_polly"},
        },
    },
}


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def blend_rgb(
    c1: tuple[int, int, int], c2: tuple[int, int, int], alpha: float
) -> tuple[int, int, int]:
    return tuple(int(round(c1[i] * (1.0 - alpha) + c2[i] * alpha)) for i in range(3))


def load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(
        str(FONTS_DIR / name), size, layout_engine=ImageFont.Layout.BASIC
    )


def wrap_text_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines = []
    cur = words[0]
    for w in words[1:]:
        test = f"{cur} {w}"
        if font.getlength(test) <= max_width:
            cur = test
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def draw_tracked_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, ...],
    tracking: float = 0.0,
    anchor: str = "la",
) -> float:
    if not text:
        return 0.0
    if abs(tracking) < 0.05 or len(text) <= 1:
        draw.text(xy, text, font=font, fill=fill, anchor=anchor)
        return float(font.getlength(text))

    advances = []
    for i, ch in enumerate(text):
        if i == 0:
            adv = float(font.getlength(ch))
        else:
            prev = text[i - 1]
            adv = float(font.getlength(prev + ch) - font.getlength(prev))
        advances.append(adv)
    total_w = sum(advances) + tracking * (len(text) - 1)

    x, y = xy
    if anchor.startswith("m"):
        start_x = x - total_w / 2.0
    elif anchor.startswith("r"):
        start_x = x - total_w
    else:
        start_x = x

    v_anchor = "l" + (anchor[1] if len(anchor) > 1 else "a")
    cx = start_x
    for ch, adv in zip(text, advances):
        draw.text((cx, y), ch, font=font, fill=fill, anchor=v_anchor)
        cx += adv + tracking
    return total_w


def make_paper_canvas(paper_rgb: tuple[int, int, int], seed: int = 42) -> np.ndarray:
    """Create a 1920x1080 warm archival paper background with subtle organic grain
    and a center book spine crease at x = SPINE_X (1016).
    """
    rng = np.random.default_rng(seed)
    base = np.empty((H, W, 3), dtype=np.float32)
    base[:, :, 0] = paper_rgb[0]
    base[:, :, 1] = paper_rgb[1]
    base[:, :, 2] = paper_rgb[2]

    grain = rng.normal(0.0, 1.3, size=(H, W, 1)).astype(np.float32)
    laid_y = (np.sin(np.arange(H, dtype=np.float32) * (2.0 * math.pi / 4.0)) * 0.40)[
        :, None, None
    ]

    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    ny = (yy - H / 2.0) / (H / 2.0)
    nx = (xx - W / 2.0) / (W / 2.0)
    r2 = nx * nx * 0.7 + ny * ny * 0.9
    vignette = -np.clip(r2 - 0.35, 0.0, 1.5) * 6.0

    # Book spine crease at x = SPINE_X (1016)
    spine_dist = np.abs(xx - float(SPINE_X))
    spine_shadow = -8.5 * np.exp(-((spine_dist / 24.0) ** 2))

    canvas = base + grain + laid_y + vignette[:, :, None] + spine_shadow[:, :, None]
    return np.clip(canvas, 0, 255).astype(np.uint8)


def trim_outer_paper_margin(im: Image.Image) -> Image.Image:
    """Smart outer paper-border / frame trimmer for `_bg.jpg` backplates:
    If a `_bg.jpg` has a uniform/textured light cream border around an inner rectangular
    illustration, detects the inner artwork edges cleanly within the outer 12% margin
    using row/column color variance + smoothed gradient edge detection, without chopping
    full-bleed scene content.
    """
    arr = np.array(im.convert("RGB"), dtype=np.float32)
    h, w, _ = arr.shape

    corners = np.concatenate(
        [
            arr[:10, :10].reshape(-1, 3),
            arr[:10, -10:].reshape(-1, 3),
            arr[-10:, :10].reshape(-1, 3),
            arr[-10:, -10:].reshape(-1, 3),
        ],
        axis=0,
    )
    bg_color = np.median(corners, axis=0)
    # Only trim if outer corners are light cream/white paper
    if bg_color.mean() < 205.0:
        return im

    gray = arr.mean(axis=2)
    smooth_gray = ndimage.gaussian_filter(gray, sigma=1.5)
    grad = np.hypot(
        ndimage.sobel(smooth_gray, axis=1), ndimage.sobel(smooth_gray, axis=0)
    )
    diff = np.linalg.norm(arr - bg_color[None, None, :], axis=2)

    max_y = int(h * 0.12)
    max_x = int(w * 0.12)

    def is_margin_strip(strip_diff: np.ndarray, strip_gray: np.ndarray, strip_grad: np.ndarray) -> bool:
        return (
            float(strip_gray.mean()) > 210.0
            and float(np.percentile(strip_diff, 98)) < 32.0
            and float((strip_grad > 28.0).mean()) < 0.06
        )

    y0 = 0
    for y in range(max_y):
        if is_margin_strip(diff[y], gray[y], grad[y]):
            y0 = y + 1
        else:
            break

    y1 = h
    for y in range(h - 1, h - 1 - max_y, -1):
        if is_margin_strip(diff[y], gray[y], grad[y]):
            y1 = y
        else:
            break

    x0 = 0
    for x in range(max_x):
        if is_margin_strip(diff[:, x], gray[:, x], grad[:, x]):
            x0 = x + 1
        else:
            break

    x1 = w
    for x in range(w - 1, w - 1 - max_x, -1):
        if is_margin_strip(diff[:, x], gray[:, x], grad[:, x]):
            x1 = x
        else:
            break

    # Require genuine horizontal paper margin on both left and right before trimming,
    # so a full-bleed room with a light ceiling is never cropped.
    if x0 < 6 or x1 > w - 6:
        return im

    pad_in = 2
    x0 = min(max_x, x0 + pad_in)
    x1 = max(w - max_x, x1 - pad_in)
    if y0 > 4:
        y0 = min(max_y, y0 + pad_in)
    if y1 < h - 4:
        y1 = max(h - max_y, y1 - pad_in)

    if (x1 - x0) < int(w * 0.72) or (y1 - y0) < int(h * 0.72):
        return im
    return im.crop((x0, y0, x1, y1))


def extract_three_diecut_standees(
    cutouts_path: Path,
    paper_rgb: tuple[int, int, int],
    ink_rgb: tuple[int, int, int],
) -> tuple[dict[str, Image.Image], int]:
    """Segment the 3-column cutout sheet into ('left', 'center', 'right') RGBA die-cut
    paper standees using minimum-density valley finding + 2D connected-component grouping
    so no connected component is ever sliced by a vertical line.
    Returns (standees_dict, raw_sheet_height).
    """
    raw_im = Image.open(cutouts_path).convert("RGB")
    arr = np.array(raw_im, dtype=np.float32)
    h, w, _ = arr.shape

    # Estimate smooth background color field from top and bottom borders
    top = np.median(arr[:14, :, :], axis=0)
    bot = np.median(arr[-14:, :, :], axis=0)
    v = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None, None]
    bg_field = top[None, :, :] * (1.0 - v) + bot[None, :, :] * v
    dist = np.linalg.norm(arr - bg_field, axis=2)

    gray = arr.mean(axis=2)
    gx = ndimage.sobel(gray, axis=1)
    gy = ndimage.sobel(gray, axis=0)
    grad = np.hypot(gx, gy)

    # Treat bright, low-gradient cream/ivory interior regions as paper background
    is_paper_bg = (
        (gray > 218.0) & (grad < 16.0) & ((arr.max(axis=2) - arr.min(axis=2)) < 42.0)
    )

    # Core ink/paint mask: anything with strong contrast OR ink line gradient, excluding paper background
    core = ((dist > 22.0) | (grad > 18.0)) & (~is_paper_bg)
    core[:4, :] = False
    core[-4:, :] = False
    core[:, :4] = False
    core[:, -4:] = False

    struct = ndimage.generate_binary_structure(2, 2)
    fg1 = ndimage.binary_fill_holes(
        ndimage.binary_closing(core, structure=struct, iterations=1)
    )
    fg2 = ndimage.binary_closing(fg1, structure=struct, iterations=1)
    subject_fg = ndimage.binary_erosion(fg2, structure=struct, iterations=1) | (
        fg1 & (~core)
    )
    subject_fg = ndimage.binary_fill_holes(subject_fg)

    # 1. Minimum-density vertical valley finding (smoothed with a 15px window)
    col_fg_count = subject_fg.sum(axis=0).astype(np.float32)
    col_smooth = ndimage.uniform_filter1d(col_fg_count, size=15)

    s1_lo, s1_hi = int(w * 0.24), int(w * 0.44)
    s2_lo, s2_hi = int(w * 0.56), int(w * 0.76)

    # Add a tiny quadratic bias toward the middle of each search window so wide zero-foreground
    # valleys pick the center of the empty gap
    idx1 = np.arange(s1_lo, s1_hi, dtype=np.float32)
    bias1 = 0.05 * (((idx1 - 0.5 * (s1_lo + s1_hi)) / max(1.0, s1_hi - s1_lo)) ** 2)
    split_1 = s1_lo + int(np.argmin(col_smooth[s1_lo:s1_hi] + bias1))

    idx2 = np.arange(s2_lo, s2_hi, dtype=np.float32)
    bias2 = 0.05 * (((idx2 - 0.5 * (s2_lo + s2_hi)) / max(1.0, s2_hi - s2_lo)) ** 2)
    split_2 = s2_lo + int(np.argmin(col_smooth[s2_lo:s2_hi] + bias2))

    # 2. Label 2D connected components on full-sheet `subject_fg` and assign each component
    # intact to "left", "center", or "right" based on its horizontal centroid `cx`.
    lbl, n_cc = ndimage.label(subject_fg)
    bucket_masks = {
        "left": np.zeros((h, w), dtype=bool),
        "center": np.zeros((h, w), dtype=bool),
        "right": np.zeros((h, w), dtype=bool),
    }
    if n_cc > 0:
        sizes = ndimage.sum(subject_fg, lbl, range(1, n_cc + 1))
        max_sz = max(sizes) if len(sizes) > 0 else 0
        min_cc_sz = max(600.0, max_sz * 0.035)
        for cc_idx, sz in enumerate(sizes, 1):
            if sz < min_cc_sz:
                continue
            cc_mask = lbl == cc_idx
            _, xs_cc = np.where(cc_mask)
            cx = float(xs_cc.mean())
            if cx < split_1:
                bucket_masks["left"] |= cc_mask
            elif cx < split_2:
                bucket_masks["center"] |= cc_mask
            else:
                bucket_masks["right"] |= cc_mask

    # Fallback only if two adjacent subjects touched in the raw drawing, leaving a bucket empty
    for b_name, (x_lo, x_hi) in [
        ("left", (0, split_1)),
        ("center", (split_1, split_2)),
        ("right", (split_2, w)),
    ]:
        if bucket_masks[b_name].sum() < 200:
            bucket_masks[b_name][:, x_lo:x_hi] = subject_fg[:, x_lo:x_hi]

    rng = np.random.default_rng(101)
    card_base_rgb = blend_rgb(paper_rgb, ink_rgb, 0.03)
    edge_dark = blend_rgb(paper_rgb, ink_rgb, 0.44)
    edge_light = tuple(min(255, c + 10) for c in paper_rgb)

    standees: dict[str, Image.Image] = {}
    for col_name in ("left", "center", "right"):
        sub_mask = bucket_masks[col_name]
        # Prune any small stray fragments (< 5% of largest component in this bucket)
        lbl_b, n_b = ndimage.label(sub_mask)
        if n_b > 1:
            b_sizes = ndimage.sum(sub_mask, lbl_b, range(1, n_b + 1))
            b_max = max(b_sizes) if len(b_sizes) > 0 else 0
            for idx_b, sz_b in enumerate(b_sizes, 1):
                if sz_b < max(600.0, b_max * 0.05):
                    sub_mask[lbl_b == idx_b] = False

        ys, xs = np.where(sub_mask)
        if len(ys) < 50:
            standees[col_name] = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            continue

        pad = 12
        y0 = max(0, int(ys.min()) - pad)
        y1 = min(h, int(ys.max()) + pad + 1)
        x0 = max(0, int(xs.min()) - pad)
        x1 = min(w, int(xs.max()) + pad + 1)

        m_crop = ndimage.binary_fill_holes(sub_mask[y0:y1, x0:x1])
        rgb_crop = arr[y0:y1, x0:x1]
        ch, cw = m_crop.shape

        # Build a smooth die-cut cardstock silhouette with zero interior holes
        diecut_core = ndimage.binary_fill_holes(
            ndimage.binary_closing(m_crop, structure=struct, iterations=3)
        )

        dist_out = ndimage.distance_transform_edt(~diecut_core)
        dist_in_subj = ndimage.distance_transform_edt(m_crop)
        dist_out_subj = ndimage.distance_transform_edt(~m_crop)

        card_radius = 6.5
        bevel_inner = 5.0

        alpha = np.clip((card_radius + 0.8 - dist_out) / 1.4, 0.0, 1.0)

        card_tex = np.empty((ch, cw, 3), dtype=np.float32)
        card_tex[:, :, 0] = card_base_rgb[0]
        card_tex[:, :, 1] = card_base_rgb[1]
        card_tex[:, :, 2] = card_base_rgb[2]
        card_tex += rng.normal(0.0, 1.2, size=(ch, cw, 1)).astype(np.float32)

        subj_weight = np.clip((dist_in_subj - dist_out_subj + 0.8) / 1.8, 0.0, 1.0)[
            :, :, None
        ]
        comp_rgb = card_tex * (1.0 - subj_weight) + rgb_crop * subj_weight

        gy_d, gx_d = np.gradient(dist_out.astype(np.float32))
        light_dot = gx_d * 0.707 + gy_d * 0.707
        rim_mask = np.clip(1.0 - np.abs(dist_out - (bevel_inner + 0.7)) / 1.2, 0.0, 1.0)

        shade_w = (rim_mask * np.clip(light_dot + 0.2, 0.0, 1.0))[:, :, None]
        hilite_w = (rim_mask * np.clip(-light_dot, 0.0, 1.0) * 0.65)[:, :, None]

        ed_arr = np.array(edge_dark, dtype=np.float32)[None, None, :]
        el_arr = np.array(edge_light, dtype=np.float32)[None, None, :]
        comp_rgb = comp_rgb * (1.0 - shade_w) + ed_arr * shade_w
        comp_rgb = comp_rgb * (1.0 - hilite_w) + el_arr * hilite_w

        # Subtle horizontal paper fold-tab crease near the bottom of the standee
        fold_y = ch - pad - 2
        if 10 < fold_y < ch - 3:
            comp_rgb[fold_y : fold_y + 2, :, :] *= 0.88
            comp_rgb[fold_y + 2 : fold_y + 3, :, :] = np.minimum(
                255.0, comp_rgb[fold_y + 2 : fold_y + 3, :, :] * 1.06
            )

        rgba = np.zeros((ch, cw, 4), dtype=np.uint8)
        rgba[:, :, :3] = np.clip(comp_rgb, 0, 255).astype(np.uint8)
        rgba[:, :, 3] = np.clip(alpha * 255.0, 0, 255).astype(np.uint8)

        # Crop tightly to non-zero alpha so bounding box math is exact to the pixel
        ay, ax = np.where(rgba[:, :, 3] > 2)
        if len(ay) > 0:
            rgba = rgba[int(ay.min()) : int(ay.max()) + 1, int(ax.min()) : int(ax.max()) + 1]
        standees[col_name] = Image.fromarray(rgba, mode="RGBA")

    return standees, h


def prepare_popup_spread_pack(book: dict, scene_idx: int, paper_bg: np.ndarray) -> dict:
    """Load and pre-process the 16:9 Recessed Stage Backplate (896x504) + 3 Die-Cut Cardstock
    Standees for `scene_idx` of `book`, guaranteeing that every standee's full
    bounding box (including its white die-cut cardstock border AND its horizontal V-fold
    shear offset during unfolding) fits strictly inside `[sx0 + 14, sx0 + sw - 14]` and
    `[sy0 + 14, sy0 + sh - 10]` with zero pixels ever clipped at the stage edges.
    """
    book_id = book["id"]
    pal = book["palette"]
    paper_rgb = hex_to_rgb(pal["paper"])
    ink_rgb = hex_to_rgb(pal["ink"])
    rule_rgb = hex_to_rgb(pal["rule"])
    muted_rgb = hex_to_rgb(pal["muted"])

    sc = book["scenes"][scene_idx]
    bg_path = ROOT / sc.get("bg_file", sc["image_file"])
    cutouts_path = ROOT / sc.get("cutouts_file", sc["image_file"])
    popup_spread_idx = int(
        sc.get("popup_spread_idx", sc.get("popup_spread_num", scene_idx + 1) - 1)
    )

    # 1. Prepare exact 16:9 recessed stage backplate (STAGE_W=896, STAGE_H=504) without horizontal cropping
    raw_bg = Image.open(bg_path).convert("RGB")
    trimmed_bg = trim_outer_paper_margin(raw_bg)
    bg_resized = trimmed_bg.resize((STAGE_W, STAGE_H), Image.Resampling.LANCZOS)
    bg_arr = np.array(bg_resized, dtype=np.float32)

    # Add pop-up book center V-fold crease down the middle of the backplate + subtle stage recess shading
    xx = np.arange(STAGE_W, dtype=np.float32)[None, :]
    yy = np.arange(STAGE_H, dtype=np.float32)[:, None]
    mid_x = STAGE_W * 0.5
    crease_d = xx - mid_x
    crease_shade = -12.0 * np.exp(-((crease_d / 5.0) ** 2)) - 3.5 * np.tanh(crease_d / 90.0)
    top_shadow = -13.0 * np.exp(-(yy / 24.0))
    side_shadow = -12.0 * (
        np.exp(-(xx / 22.0)) + np.exp(-((STAGE_W - 1 - xx) / 22.0))
    )
    # Subtle horizontal stage floor fold-crease near y = STAGE_H - 34
    floor_crease_y = float(STAGE_H - 34)
    floor_crease = -6.5 * np.exp(-(((yy - floor_crease_y) / 4.5) ** 2))
    bg_arr = np.clip(
        bg_arr
        + crease_shade[:, :, None]
        + top_shadow[:, :, None]
        + side_shadow[:, :, None]
        + floor_crease[:, :, None],
        0,
        255,
    ).astype(np.uint8)

    # 2. Extract and scale the 3 die-cut standees ('left', 'center', 'right')
    raw_standees, raw_sheet_h = extract_three_diecut_standees(
        cutouts_path, paper_rgb, ink_rgb
    )
    layout_cfg = POPUP_STAGE_LAYOUT.get(book_id, {}).get(popup_spread_idx, {})

    sx0, sy0, sw, sh = STAGE_X0, STAGE_Y0, STAGE_W, STAGE_H
    safe_x0, safe_x1 = 14, sw - 14
    safe_y0, safe_y1 = 14, sh - 10
    max_avail_h = safe_y1 - safe_y0

    sy_back = sh - 34
    dy_front = safe_y1

    layers = []
    for col_name, cfg in layout_cfg.items():
        st_im = raw_standees[col_name]
        if cfg.get("flip_x", False):
            st_im = ImageOps.mirror(st_im)

        ow, oh = st_im.size
        z_val = float(cfg["z"])
        x_rel = float(cfg["x_rel"])

        # Determine bottom hinge `yh` in stage coordinates [0..sh], strictly <= safe_y1 (sh - 10)
        if cfg["y_base"] < 680:
            # Elevated wall props (e.g. Alice falling down the well)
            rel_y = (float(cfg["y_base"]) - 162.0) / 548.0
            yh = int(round(max(safe_y0 + 160, min(safe_y1, rel_y * sh))))
        else:
            yh = int(round(sy_back + z_val * (dy_front - sy_back)))
            yh = max(safe_y0 + 160, min(safe_y1, yh))

        # Scale target_h proportionally to the 504px stage height using calibrated POPUP_STAGE_LAYOUT target_h
        desired_h = int(round(float(cfg["target_h"]) * 0.82))
        max_h_here = min(max_avail_h, yh - safe_y0)
        target_h = max(32, min(desired_h, max_h_here))

        scale = target_h / float(max(1, oh))
        target_w = max(16, int(round(ow * scale)))

        # Enforce column width budget so wide props never crowd or clip stage edges
        max_col_w = int(round(sw * (0.42 if col_name == "center" else 0.33)))
        if target_w > max_col_w:
            scale = max_col_w / float(max(1, ow))
            target_w = max_col_w
            target_h = max(24, int(round(oh * scale)))

        # V-fold shear direction when folded flat:
        # In PIL inverse affine `x_in = x_out + shear_x * (y_out - yh)`, for `y_out < yh`,
        # `x_out = x_in - shear_x * (y_out - yh) = x_in + shear_x * |y_out - yh|`.
        # Thus `shear_flat > 0` leans the top of the left cutout INWARD (rightward toward center),
        # and `shear_flat < 0` leans the top of the right cutout INWARD (leftward toward center)!
        if x_rel < 0.40:
            shear_flat = 0.30
        elif x_rel > 0.60:
            shear_flat = -0.30
        else:
            shear_flat = -0.10

        # Maximum horizontal displacement of the standee's top edge across all `s_pop in [0, 1]`:
        # max over s_pop of `(1 - s_pop) * (0.10 + 0.90 * s_pop)` is `0.278` at `s_pop = 0.444`.
        max_dx_pos = int(math.ceil(max(0.0, shear_flat * 0.28 * target_h)))
        max_dx_neg = int(math.floor(min(0.0, shear_flat * 0.28 * target_h)))

        # Clamp horizontal position `base_x` so that BOTH upright AND sheared unfolding frames
        # stay strictly inside `[safe_x0, safe_x1]` = `[14, sw - 14]`
        min_bx = safe_x0 - max_dx_neg
        max_bx = safe_x1 - target_w - max_dx_pos
        if max_bx < min_bx:
            # Shrink slightly if needed so min_bx <= max_bx
            avail_w = (safe_x1 - safe_x0) - (max_dx_pos - max_dx_neg)
            scale = max(16, avail_w) / float(max(1, target_w))
            target_w = max(16, int(round(target_w * scale)))
            target_h = max(24, int(round(target_h * scale)))
            max_dx_pos = int(math.ceil(max(0.0, shear_flat * 0.28 * target_h)))
            max_dx_neg = int(math.floor(min(0.0, shear_flat * 0.28 * target_h)))
            min_bx = safe_x0 - max_dx_neg
            max_bx = max(min_bx, safe_x1 - target_w - max_dx_pos)

        st_scaled = st_im.resize((target_w, target_h), Image.Resampling.LANCZOS)

        x_anchor_rel = int(round(x_rel * sw))
        base_x = max(min_bx, min(max_bx, x_anchor_rel - target_w // 2))
        base_y = max(safe_y0, min(safe_y1 - target_h, yh - target_h))
        yh = base_y + target_h

        # Pre-build soft blurred shadow silhouette inside the stage ROI
        alpha_ch = st_scaled.split()[3]
        blur_rad = int(round(4.0 + 7.0 * z_val))
        sh_pad = blur_rad * 2 + 6
        sh_canvas = Image.new("L", (target_w + sh_pad * 2, target_h + sh_pad * 2), 0)
        sh_canvas.paste(alpha_ch, (sh_pad, sh_pad))
        sh_blurred = sh_canvas.filter(ImageFilter.GaussianBlur(radius=blur_rad))

        sh_opacity_up = 0.22 + 0.12 * z_val
        sh_arr_up = (np.array(sh_blurred, dtype=np.float32) * sh_opacity_up).astype(
            np.uint8
        )
        sh_rgba_up = Image.new("RGBA", sh_blurred.size, ink_rgb + (0,))
        sh_rgba_up.putalpha(Image.fromarray(sh_arr_up, mode="L"))

        card_roi = Image.new("RGBA", (ROI_W, ROI_H), (0, 0, 0, 0))
        card_roi.paste(st_scaled, (base_x, base_y))

        sh_roi = Image.new("RGBA", (ROI_W, ROI_H), (0, 0, 0, 0))
        sh_roi.paste(sh_rgba_up, (base_x - sh_pad, base_y - sh_pad))

        layers.append(
            {
                "col_name": col_name,
                "card_roi": card_roi,
                "sh_roi": sh_roi,
                "yh_roi": float(yh),
                "z": z_val,
                "shear_flat": shear_flat,
                "sh_ox_max": 10.0 + 12.0 * z_val,
                "sh_oy_max": 3.0 + 6.0 * z_val,
                "speaker": cfg.get("speaker"),
                "bbox_stage": (base_x, base_y, base_x + target_w, base_y + target_h),
            }
        )

    layers.sort(key=lambda d: d["z"])

    pack = {
        "bg_arr": bg_arr,
        "layers": layers,
        "paper_rgb": paper_rgb,
        "ink_rgb": ink_rgb,
        "rule_rgb": rule_rgb,
        "muted_rgb": muted_rgb,
        "upright_roi_rgb": None,
    }

    dummy_frame = paper_bg.copy()
    composite_popup_diorama_on_spread(
        dummy_frame,
        pack,
        fold_progress=1.0,
        chapter_progress=0.0,
    )
    pack["upright_roi_rgb"] = dummy_frame[ROI_OY:ROI_RY1, ROI_OX:ROI_RX1].copy()
    return pack


def composite_popup_diorama_on_spread(
    frame_buf: np.ndarray,
    popup_pack: dict,
    fold_progress: float,
    chapter_progress: float = 0.0,
    accent_rgb: tuple[int, int, int] = (80, 80, 80),
):
    """Composite the 4-plane 3D paper pop-up diorama onto `frame_buf` inside the exact
    16:9 stage box `(STAGE_X0, STAGE_Y0, STAGE_W, STAGE_H) = (68, 204, 896, 504)`:
    - When `fold_progress >= 0.999` and `upright_roi_rgb` is cached, copies the pre-rendered
      upright diorama directly so the cutouts stand 100% rock-steady while reading.
    - During page-turn unfolding (`0 < fold_progress < 1`) and folding-down (`1 -> 0`),
      animates each die-cut cardstock standee hinging up out of the V-fold crease (`sy: 0.10 -> 1.0`,
      `shear_x: shear_flat -> 0.0`) with rising cast shadows across the stage floor and backplate.
    """
    if fold_progress >= 0.999 and popup_pack.get("upright_roi_rgb") is not None:
        frame_buf[ROI_OY:ROI_RY1, ROI_OX:ROI_RX1] = popup_pack["upright_roi_rgb"]
    else:
        bg_arr = popup_pack["bg_arr"]
        rule_rgb = popup_pack["rule_rgb"]

        canvas_im = Image.fromarray(bg_arr).convert("RGBA")

        for idx_l, layer in enumerate(popup_pack["layers"]):
            stagger = idx_l * 0.18
            u = max(0.0, min(1.0, (fold_progress - stagger) / max(0.25, 1.0 - stagger)))
            s = u * u * (3.0 - 2.0 * u)
            s_pop = min(1.0, s + 0.032 * math.sin(math.pi * s) * (s ** 2))

            sy = 0.10 + 0.90 * s_pop
            shear_x = layer["shear_flat"] * (1.0 - s_pop)

            yh = layer["yh_roi"]
            inv_sy = 1.0 / sy
            a = 1.0
            b = shear_x
            c = -shear_x * yh
            d = 0.0
            e = inv_sy
            f = yh * (1.0 - inv_sy)

            sh_ox = 2.0 + layer["sh_ox_max"] * s_pop
            sh_oy = 1.0 + layer["sh_oy_max"] * s_pop
            sh_shear = shear_x * 0.65
            sh_xform = layer["sh_roi"].transform(
                (ROI_W, ROI_H),
                Image.Transform.AFFINE,
                (
                    1.0,
                    sh_shear,
                    -sh_ox - sh_shear * yh,
                    0.0,
                    inv_sy,
                    yh - (yh + sh_oy) * inv_sy,
                ),
                resample=Image.Resampling.BILINEAR,
            )

            card_xform = layer["card_roi"].transform(
                (ROI_W, ROI_H),
                Image.Transform.AFFINE,
                (a, b, c, d, e, f),
                resample=Image.Resampling.BICUBIC,
            )

            if s_pop < 0.98:
                shade = 0.74 + 0.26 * s_pop
                c_arr = np.array(card_xform, dtype=np.float32)
                c_arr[:, :, :3] *= shade
                card_xform = Image.fromarray(
                    np.clip(c_arr, 0, 255).astype(np.uint8), mode="RGBA"
                )

            canvas_im.alpha_composite(sh_xform)
            canvas_im.alpha_composite(card_xform)

        stage_rgb = np.array(canvas_im.convert("RGB"), dtype=np.uint8)
        # Crisp 1px stage border on all 4 sides of the 896x504 stage box
        stage_rgb[0, :] = rule_rgb
        stage_rgb[-1, :] = rule_rgb
        stage_rgb[:, 0] = rule_rgb
        stage_rgb[:, -1] = rule_rgb
        frame_buf[ROI_OY:ROI_RY1, ROI_OX:ROI_RX1] = stage_rgb

    # Subtle 2px chapter reading progress filament along the right-page footer rule (y=975..977)
    rx0, rx1 = 1064, 1844
    prog_w = int(round((rx1 - rx0) * max(0.0, min(1.0, chapter_progress))))
    if prog_w > 0:
        frame_buf[975:977, rx0 : rx0 + prog_w] = accent_rgb


def render_page_turn_transition(
    prev_spread: np.ndarray,
    next_spread: np.ndarray,
    progress: float,
    paper_rgb: tuple[int, int, int] = (246, 242, 234),
) -> np.ndarray:
    """Render a true 3D tilted inextensible cylindrical book page curl with Z-perspective
    and lifted top/bottom page edges (`y_top = 48 .. y_bot = 1032`, `x_left = 56 .. x_right = 1864`):
    - Tilted cylinder axis (`tilt = -0.11`, ~6.3 deg diagonal lift from bottom-right):
      `x_eff(x, y) = x - (y - 540.0) * (-0.11)` so the bottom-right corner lifts slightly ahead
      of the top-right corner as `curl_x(u)` sweeps from `1890.0` to `-160.0`.
    - Region A (`d < -R`): `prev_spread` lies 100% flat at 1:1 scale (zero horizontal squish).
    - Region C1 (`d in [-R, 0]`, Front Curve): `prev_spread` lifts smoothly off the page around
      a cylinder of radius `R = 115.0` (`z_front = R * (1 - cos(alpha))`), with inextensible arc
      mapping `src_x = x + (R * alpha - (d + R))` and 3D perspective `src_y = 540 + (y - 540)*(1 - z/focal)`.
    - Region C2 (`d in [0, W_flap]`, Curled Back Flap & Cylinder Crest): the turned-over backside
      of the leaf arches at height `z_back` (`115 .. 185px`) with 3D cylindrical specular highlight
      and shadow roll, translucent reverse ink bleed-through, and a crisp 2px paper edge.
    - Region B (`d > W_flap`): `next_spread` lies 100% flat at 1:1 scale with a soft 3D cast shadow
      falling across `d in [W_flap, W_flap + 105]`.
    """
    p = max(0.0, min(1.0, float(progress)))
    u = p * p * (3.0 - 2.0 * p)
    sin_u = math.sin(math.pi * u)

    x_left, x_right = 64.0, float(W - 64)   # 64 .. 1856 (matches spread border rules)
    y_top, y_bot = 56.0, float(H - 56)      # 56 .. 1024 (matches top/bottom spread border rules)
    y_mid = 540.0
    focal = 1500.0

    R = 115.0 * (0.35 + 0.65 * sin_u)
    W_flap = 225.0 * sin_u + 18.0 * math.sin(math.pi * min(1.0, u * 1.2))

    # Sweep curl_x from right (1890) to left (-160)
    curl_x = 1890.0 - u * (1890.0 - (-160.0))

    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]

    # Diagonal 3D tilt so bottom-right lifts slightly ahead of top-right
    tilt = -0.11
    x_eff = xx - (yy - y_mid) * tilt
    d = x_eff - curl_x

    paper_vec = np.array(paper_rgb, dtype=np.float32)[None, None, :]

    # Start with flat base: prev_spread where d < 0, next_spread where d >= 0
    out = np.where((d < 0.0)[:, :, None], prev_spread, next_spread).astype(np.float32)

    # Soft 3D cast shadow onto flat next_spread to the right of the curled back flap (d > W_flap)
    sh_d = d - W_flap
    in_book_y = np.clip((yy - y_top) / 6.0, 0.0, 1.0) * np.clip((y_bot - yy) / 6.0, 0.0, 1.0)
    sh_mask = (sh_d >= 0.0) & (sh_d < 125.0)
    sh_op = np.where(
        sh_mask,
        0.36 * sin_u * np.exp(-np.clip(sh_d, 0.0, 125.0) / 36.0) * in_book_y,
        0.0,
    )
    out *= 1.0 - sh_op[:, :, None]

    # Bounding column slice for the active 3D curl band `d in [-R - 4, W_flap + 16]`
    d_min_row = np.min(d, axis=0)
    d_max_row = np.max(d, axis=0)
    active_cols = np.where((d_max_row >= -R - 4.0) & (d_min_row <= W_flap + 16.0))[0]
    if len(active_cols) == 0:
        return np.clip(out, 0, 255).astype(np.uint8)

    c0 = int(active_cols[0])
    c1 = int(active_cols[-1]) + 1

    xx_b = xx[:, c0:c1]
    d_b = d[:, c0:c1]
    base_b = out[:, c0:c1].copy()

    # --- 1. Front Curve (`d_b in [-R, 0]`): prev_spread lifting off the flat book ---
    u_front = np.clip((d_b + R) / max(1.0, R), 0.0, 1.0)
    alpha = np.arcsin(u_front)  # [0, pi/2]
    s_front = R * alpha
    z_front = R * (1.0 - np.cos(alpha)) * sin_u

    # --- 2. Curled Back Flap & Cylinder Crest (`d_b in [0, W_flap]`): turned-over backside ---
    u_back = np.clip(d_b / max(1.0, W_flap), 0.0, 1.0)
    # Smoothly continues from z_front(d=0) = R*sin_u up to 1.62*R*sin_u and down to 0.90*R*sin_u at tip
    z_back = R * sin_u * (1.0 + 0.62 * np.sin(math.pi * u_back) - 0.10 * (u_back ** 2))

    is_front = (d_b >= -R) & (d_b < 0.0)
    is_back = (d_b >= 0.0) & (d_b <= W_flap)
    in_curl = is_front | is_back

    z_curl = np.where(is_front, z_front, np.where(is_back, z_back, 0.0))
    z_lift_weight = np.clip(z_curl / 55.0, 0.0, 1.0)

    # 3D perspective vertical coordinate: lifted z > 0 expands top/bottom edges outward!
    persp_scale = 1.0 - (z_curl / focal)
    src_y_f = y_mid + (yy - y_mid) * persp_scale
    src_y_idx = np.clip(np.rint(src_y_f).astype(np.int32), int(y_top), int(y_bot) - 1)

    # Inextensible horizontal source coordinate for Front Curve (`prev_spread`)
    disp_front = s_front - (d_b + R)  # >= 0, equals 0 at d_b = -R
    src_x_front_f = xx_b + disp_front
    src_x_front_idx = np.clip(np.rint(src_x_front_f).astype(np.int32), int(x_left), int(x_right) - 1)

    # Horizontal source coordinate for Back Flap (mirrored reverse bleed-through around fold)
    src_x_back_f = xx_b + (s_front - d_b) + (W_flap - d_b) * 0.85
    src_x_back_idx = np.clip(np.rint(src_x_back_f).astype(np.int32), int(x_left), int(x_right) - 1)

    valid_page = (
        in_curl
        & (src_y_f >= y_top)
        & (src_y_f <= y_bot)
        & (xx_b >= x_left)
        & (xx_b <= x_right)
    )

    # Sample front surface from prev_spread
    front_rgb = prev_spread[src_y_idx, src_x_front_idx].astype(np.float32)
    # Subtle 3D shading on front curve: 1.0 at d = -R (C1 continuous with flat page),
    # dimming slightly as the sheet curves vertical toward d = 0
    front_shade = 1.0 - 0.13 * sin_u * (np.sin(alpha) ** 1.6)
    front_rgb *= front_shade[:, :, None]

    # Sample back flap: 78% warm cream paper + 22% translucent bleed-through
    bleed_prev = prev_spread[src_y_idx, src_x_back_idx].astype(np.float32)
    bleed_next = next_spread[src_y_idx, src_x_back_idx].astype(np.float32)
    back_rgb = 0.78 * paper_vec + 0.14 * bleed_prev + 0.08 * bleed_next

    # 3D cylindrical shading on the Back Flap (`u_back in [0, 1]`):
    # - Starts at 0.87 at u_back = 0 (matching front_shade at d = 0!)
    # - Rises to a bright specular highlight ridge (+14%, 1.11) around u_back = 0.32
    # - Rolls into a warm curved cylinder shadow (-18%, 0.82) near u_back = 1.0
    spec_ridge = 0.24 * np.exp(-(((u_back - 0.32) / 0.22) ** 2))
    roll_shadow = -0.05 * (1.0 - u_back) - 0.16 * (u_back ** 1.8)
    back_shade = 1.0 + sin_u * (spec_ridge + roll_shadow - 0.08 * np.exp(-u_back / 0.08))
    back_rgb = np.clip(back_rgb * back_shade[:, :, None], 0.0, 255.0)

    curl_rgb = np.where(is_front[:, :, None], front_rgb, back_rgb)

    # Crisp 2px deckled paper edge along top/bottom lifted edges (`src_y = 48 / 1032`)
    # and along the trailing edge of the back flap (`d_b = W_flap`), weighted by z_lift_weight
    dist_tb = np.minimum(np.abs(src_y_f - y_top), np.abs(src_y_f - y_bot))
    dist_flap = np.where(is_back, np.abs(W_flap - d_b), 999.0)
    edge_dist = np.minimum(dist_tb, dist_flap)
    rim_w = (np.clip(1.8 - edge_dist, 0.0, 1.0) * z_lift_weight)[:, :, None]
    edge_col = paper_vec * 0.74
    curl_rgb = curl_rgb * (1.0 - 0.35 * rim_w) + edge_col * (0.35 * rim_w)

    # Soft drop shadow cast just outside the lifted top and bottom page edges (`src_y < 48` or `src_y > 1032`),
    # proportional to local lift height `z_lift_weight` so there is zero step at d = -R
    out_tb_dist = np.where(
        src_y_f < y_top,
        y_top - src_y_f,
        np.where(src_y_f > y_bot, src_y_f - y_bot, 999.0),
    )
    tb_sh = np.where(
        in_curl & (~valid_page) & (out_tb_dist < 14.0),
        1.0 - 0.22 * z_lift_weight * np.exp(-out_tb_dist / 5.5),
        1.0,
    )

    comp_b = np.where(valid_page[:, :, None], curl_rgb, base_b * tb_sh[:, :, None])
    out[:, c0:c1] = comp_b

    return np.clip(out, 0, 255).astype(np.uint8)


def render_title_card(book: dict, paper_bg: np.ndarray) -> np.ndarray:
    """Render the Fine-Press Chapter Title Plate (1920x1080) with Character Reference Plate,
    using 3x supersampled typography for subpixel-accurate kerning.
    """
    pal = book["palette"]
    paper_rgb = hex_to_rgb(pal["paper"])
    card_rgb = hex_to_rgb(pal["card"])
    ink_rgb = hex_to_rgb(pal["ink"])
    muted_rgb = hex_to_rgb(pal["muted"])
    accent_rgb = hex_to_rgb(pal["accent"])
    rule_rgb = hex_to_rgb(pal["rule"])

    rng = np.random.default_rng(77)
    canvas = np.empty((H, W, 3), dtype=np.float32)
    canvas[:, :, :] = paper_rgb
    canvas += rng.normal(0.0, 1.2, size=(H, W, 1)).astype(np.float32)
    im = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8)).convert("RGBA")
    draw = ImageDraw.Draw(im)

    draw.rectangle([64, 56, W - 64, H - 56], outline=rule_rgb + (255,), width=1)
    draw.rectangle([72, 64, W - 72, H - 64], outline=rule_rgb + (255,), width=1)

    rule_y = 282
    draw.line([(W / 2 - 260, rule_y), (W / 2 - 16, rule_y)], fill=rule_rgb + (255,), width=1)
    draw.line([(W / 2 + 16, rule_y), (W / 2 + 260, rule_y)], fill=rule_rgb + (255,), width=1)
    d_sz = 5
    draw.polygon(
        [(W / 2, rule_y - d_sz), (W / 2 + d_sz, rule_y), (W / 2, rule_y + d_sz), (W / 2 - d_sz, rule_y)],
        fill=accent_rgb + (255,),
    )

    char_rel = book.get(
        "char_sheet_image",
        book.get("char_sheet_file", f"illustrations/{book['id']}_char_sheet.jpg"),
    )
    char_path = ROOT / char_rel
    char_im = Image.open(char_path).convert("RGBA")
    plate_w, plate_h = 848, 477  # 16:9
    mat_pad = 18
    mat_x0 = (W - plate_w) // 2 - mat_pad
    mat_y0 = 368
    mat_x1 = mat_x0 + plate_w + 2 * mat_pad
    mat_y1 = mat_y0 + plate_h + 2 * mat_pad
    draw.rectangle(
        [mat_x0, mat_y0, mat_x1, mat_y1],
        fill=card_rgb + (255,),
        outline=rule_rgb + (255,),
        width=1,
    )

    char_resized = char_im.resize((plate_w, plate_h), Image.Resampling.LANCZOS)
    im.paste(char_resized, (mat_x0 + mat_pad, mat_y0 + mat_pad))
    draw.rectangle(
        [
            mat_x0 + mat_pad,
            mat_y0 + mat_pad,
            mat_x0 + mat_pad + plate_w,
            mat_y0 + mat_pad + plate_h,
        ],
        outline=rule_rgb + (255,),
        width=1,
    )

    ss = 3
    txt_hi = Image.new("RGBA", (W * ss, H * ss), (0, 0, 0, 0))
    draw_hi = ImageDraw.Draw(txt_hi)

    font_overline = load_font("Cinzel-Variable.ttf", 17 * ss)
    font_title = load_font("CormorantGaramond-Variable.ttf", 68 * ss)
    font_author = load_font("Cinzel-Variable.ttf", 20 * ss)
    font_chapter = load_font("EBGaramond-Italic-Variable.ttf", 30 * ss)
    font_cast_hdr = load_font("Cinzel-Variable.ttf", 14 * ss)
    font_cast = load_font("EBGaramond-Italic-Variable.ttf", 21 * ss)

    kicker = f"BOOK {book['roman']}  ·  {book['genre'].upper()}"
    draw_tracked_text(
        draw_hi,
        (W * ss / 2, 102 * ss),
        kicker,
        font_overline,
        accent_rgb + (255,),
        tracking=2.6 * ss,
        anchor="ma",
    )

    tw = font_title.getlength(book["title"])
    draw_hi.text(
        ((W * ss - tw) / 2, 140 * ss),
        book["title"],
        font=font_title,
        fill=ink_rgb + (255,),
    )

    author_line = f"{book['author'].upper()}   ·   {book['year']}"
    draw_tracked_text(
        draw_hi,
        (W * ss / 2, 232 * ss),
        author_line,
        font_author,
        muted_rgb + (255,),
        tracking=2.4 * ss,
        anchor="ma",
    )

    ch_text = f"{book['chapter_title']}  —  {book['setting']}"
    cw = font_chapter.getlength(ch_text)
    draw_hi.text(
        ((W * ss - cw) / 2, 302 * ss),
        ch_text,
        font=font_chapter,
        fill=ink_rgb + (255,),
    )

    seen_speakers = []
    for t in book["turns"]:
        lbl = t["speaker_label"].title()
        if lbl not in seen_speakers:
            seen_speakers.append(lbl)
    cast_names = "   ·   ".join(seen_speakers)

    draw_tracked_text(
        draw_hi,
        (W * ss / 2, 902 * ss),
        "ILLUSTRATED EDITION   ·   GEMINI 3.8 FLASH TTS CAST   ·   LYRIA 3.5 SCORE",
        font_cast_hdr,
        muted_rgb + (255,),
        tracking=1.8 * ss,
        anchor="ma",
    )
    cast_w = font_cast.getlength(cast_names)
    draw_hi.text(
        ((W * ss - cast_w) / 2, 932 * ss),
        cast_names,
        font=font_cast,
        fill=ink_rgb + (255,),
    )

    txt_lo = txt_hi.resize((W, H), Image.Resampling.LANCZOS)
    im = Image.alpha_composite(im, txt_lo)
    return np.array(im.convert("RGB"), dtype=np.uint8)


def layout_scene_turns_on_page(
    draw: ImageDraw.ImageDraw,
    scene_turns: list[dict],
    max_width: int,
    max_height: int,
    ss: int = 3,
) -> tuple[
    ImageFont.FreeTypeFont,
    ImageFont.FreeTypeFont,
    ImageFont.FreeTypeFont,
    list[dict],
]:
    """Choose the largest comfortable EB Garamond font size (from 27px down to 18px)
    at `ss`x supersampled resolution so all turns in the current folio fit cleanly on
    the right-hand book page without scrolling or clipping.
    """
    for font_size in [27, 25, 24, 22, 21, 20, 19, 18]:
        font_body = load_font("EBGaramond-Variable.ttf", font_size * ss)
        font_italic = load_font("EBGaramond-Italic-Variable.ttf", font_size * ss)
        font_rubric = load_font(
            "Cinzel-Variable.ttf", max(12, int(font_size * 0.54)) * ss
        )
        line_h = int(round(font_size * 1.44)) * ss
        para_gap = int(round(font_size * 0.62)) * ss

        blocks = []
        y_cursor = 0
        prev_speaker = None
        for t in scene_turns:
            show_rubric = t["is_dialogue"] and (t["speaker_key"] != prev_speaker)
            rubric_h = int(round(font_size * 0.95)) * ss if show_rubric else 0
            text_str = t.get("display_text", t.get("text", ""))
            lines = wrap_text_lines(draw, text_str, font_body, max_width * ss)
            block_h = rubric_h + len(lines) * line_h
            blocks.append(
                {
                    "turn_idx": t["turn_idx"],
                    "speaker_key": t["speaker_key"],
                    "speaker_label": t["speaker_label"],
                    "is_dialogue": t["is_dialogue"],
                    "show_rubric": show_rubric,
                    "rubric_h": rubric_h,
                    "lines": lines,
                    "line_h": line_h,
                    "y_offset": y_cursor,
                    "block_h": block_h,
                }
            )
            y_cursor += block_h + para_gap
            prev_speaker = t["speaker_key"]

        total_h = y_cursor - para_gap if blocks else 0
        if total_h <= max_height * ss or font_size == 18:
            return font_body, font_italic, font_rubric, blocks

    raise RuntimeError("Unreachable")


def render_spread_turn_layer(
    book: dict,
    folio_idx: int,
    active_turn_idx: int | None,
    paper_bg: np.ndarray,
) -> np.ndarray:
    """Render the 1920x1080 open-spread page layer for a given right-hand text folio (`folio_idx`)
    and its associated left-hand visual scene (`scene_idx = folios[folio_idx]["scene_idx"]`),
    using 3x supersampled subpixel typography and classic 3-state paragraph ink highlighting:
    - Active turn (`t_idx == active_turn_idx`): full dark `ink_rgb` and `accent_rgb`.
    - Past turns (`t_idx < active_turn_idx`): `past_ink` (0.50) and `past_rubric` (0.45).
    - Future turns (`t_idx > active_turn_idx`, or when `active_turn_idx is None` before the first
      turn of the folio starts speaking): `future_ink` (0.62) and `future_rubric` (0.58).
    """
    pal = book["palette"]
    paper_rgb = hex_to_rgb(pal["paper"])
    card_rgb = hex_to_rgb(pal["card"])
    ink_rgb = hex_to_rgb(pal["ink"])
    muted_rgb = hex_to_rgb(pal["muted"])
    accent_rgb = hex_to_rgb(pal["accent"])
    rule_rgb = hex_to_rgb(pal["rule"])

    folios = book.get("folios", book["scenes"])
    folio_info = folios[folio_idx]
    scene_idx = int(folio_info.get("scene_idx", folio_idx))
    n_scenes = len(book["scenes"])
    scene_info = book["scenes"][scene_idx]

    im = Image.fromarray(paper_bg.copy()).convert("RGBA")
    draw = ImageDraw.Draw(im)

    # Outer page frame hairlines
    draw.line([(64, 56), (W - 64, 56)], fill=rule_rgb + (255,), width=1)
    draw.line([(64, H - 56), (W - 64, H - 56)], fill=rule_rgb + (255,), width=1)
    # Center spine vertical hairline at x = SPINE_X (1016)
    draw.line([(SPINE_X, 56), (SPINE_X, H - 56)], fill=rule_rgb + (255,), width=1)

    left_x0, left_x1 = STAGE_X0, STAGE_X0 + STAGE_W  # 68, 964
    draw.line([(left_x0, 108), (left_x1, 108)], fill=rule_rgb + (255,), width=1)

    # Subtle mat card frame around the 896x504 (16:9) pop-up stage box and plate caption
    mat_x0, mat_y0 = STAGE_X0 - 12, STAGE_Y0 - 14
    mat_x1, mat_y1 = STAGE_X0 + STAGE_W + 12, STAGE_Y0 + STAGE_H + 66
    draw.rectangle(
        [mat_x0, mat_y0, mat_x1, mat_y1],
        fill=card_rgb + (255,),
        outline=rule_rgb + (255,),
        width=1,
    )

    # Left page footer rule
    draw.line([(left_x0, 976), (left_x1, 976)], fill=rule_rgb + (255,), width=1)

    # Right page rules (static 1px typographic rule at y = 166, no top audio visualiser)
    rx0, rx1 = 1064, 1844
    rw = rx1 - rx0
    draw.line([(rx0, 108), (rx1, 108)], fill=rule_rgb + (255,), width=1)
    draw.line([(rx0, 166), (rx1, 166)], fill=rule_rgb + (255,), width=1)
    draw.line([(rx0, 976), (rx1, 976)], fill=rule_rgb + (255,), width=1)

    ss = 3
    txt_hi = Image.new("RGBA", (W * ss, H * ss), (0, 0, 0, 0))
    draw_hi = ImageDraw.Draw(txt_hi)

    font_header = load_font("Cinzel-Variable.ttf", 14 * ss)
    font_plate_num = load_font("Cinzel-Variable.ttf", 14 * ss)
    font_caption = load_font("EBGaramond-Italic-Variable.ttf", 21 * ss)
    font_speaker_hdr = load_font("Cinzel-Variable.ttf", 16 * ss)
    font_speaker_sub = load_font("EBGaramond-Italic-Variable.ttf", 19 * ss)

    # --- LEFT PAGE TYPOGRAPHY ---
    draw_tracked_text(
        draw_hi,
        (left_x0 * ss, 78 * ss),
        f"BOOK {book['roman']}  ·  {book['author'].upper()}",
        font_header,
        muted_rgb + (255,),
        tracking=1.8 * ss,
        anchor="la",
    )
    draw_tracked_text(
        draw_hi,
        (left_x1 * ss, 78 * ss),
        book["year"],
        font_header,
        muted_rgb + (255,),
        tracking=1.6 * ss,
        anchor="ra",
    )

    plate_romans = ["I", "II", "III", "IV", "V"]
    plate_label = f"PLATE {plate_romans[scene_idx]} OF {plate_romans[n_scenes - 1]}"
    caption_y = STAGE_Y0 + STAGE_H + 22  # 730
    draw_tracked_text(
        draw_hi,
        (STAGE_X0 * ss, caption_y * ss),
        plate_label,
        font_plate_num,
        accent_rgb + (255,),
        tracking=1.8 * ss,
        anchor="la",
    )
    cap_text = scene_info["caption"]
    cap_w = font_caption.getlength(cap_text)
    draw_hi.text(
        ((STAGE_X0 + STAGE_W) * ss - cap_w, (caption_y - 4) * ss),
        cap_text,
        font=font_caption,
        fill=ink_rgb + (255,),
    )

    draw_tracked_text(
        draw_hi,
        (left_x0 * ss, 990 * ss),
        book["genre"].upper(),
        font_header,
        muted_rgb + (255,),
        tracking=1.6 * ss,
        anchor="la",
    )
    draw_tracked_text(
        draw_hi,
        (left_x1 * ss, 990 * ss),
        book["setting"].upper(),
        font_header,
        muted_rgb + (255,),
        tracking=1.6 * ss,
        anchor="ra",
    )

    # --- RIGHT PAGE TYPOGRAPHY ---
    folio_turns = [
        t
        for t in book["turns"]
        if int(t.get("folio_idx", t.get("page_idx", t["scene_idx"]))) == folio_idx
    ]
    draw_tracked_text(
        draw_hi,
        (rx0 * ss, 78 * ss),
        book["title"].upper(),
        font_header,
        muted_rgb + (255,),
        tracking=1.8 * ss,
        anchor="la",
    )
    short_chap = (
        folio_turns[0].get("chapter_heading", book["chapter_title"].split("·")[0].strip()).upper()
        if folio_turns
        else book["chapter_title"].split("·")[0].strip().upper()
    )
    draw_tracked_text(
        draw_hi,
        (rx1 * ss, 78 * ss),
        short_chap,
        font_header,
        muted_rgb + (255,),
        tracking=1.6 * ss,
        anchor="ra",
    )

    header_turn = None
    if active_turn_idx is not None:
        for t in folio_turns:
            if t["turn_idx"] == active_turn_idx:
                header_turn = t
                break
        if header_turn is None and active_turn_idx > 99999 and folio_turns:
            header_turn = folio_turns[-1]
    if header_turn is None:
        header_turn = folio_turns[0] if folio_turns else book["turns"][0]

    is_actively_speaking = (
        active_turn_idx is not None and active_turn_idx <= 99999 and header_turn["is_dialogue"]
    )
    spk_color = accent_rgb if is_actively_speaking else muted_rgb
    spk_w = draw_tracked_text(
        draw_hi,
        (rx0 * ss, 132 * ss),
        header_turn["speaker_label"],
        font_speaker_hdr,
        spk_color + (255,),
        tracking=1.8 * ss,
        anchor="la",
    )
    role_desc = "Character Dialogue" if header_turn["is_dialogue"] else "Literary Narration"
    draw_hi.text(
        (rx0 * ss + spk_w + 16 * ss, 129 * ss),
        f"—  {role_desc}",
        font=font_speaker_sub,
        fill=muted_rgb + (255,),
    )

    page_top = 194
    page_bottom = 952
    avail_h = page_bottom - page_top

    font_body, _font_italic, font_rubric, blocks = layout_scene_turns_on_page(
        draw_hi, folio_turns, max_width=rw, max_height=avail_h, ss=ss
    )

    total_text_h = (blocks[-1]["y_offset"] + blocks[-1]["block_h"]) if blocks else 0
    extra_space = max(0, avail_h * ss - total_text_h)
    y_start = page_top * ss + int(extra_space * 0.25)

    past_ink = blend_rgb(ink_rgb, paper_rgb, 0.50)
    future_ink = blend_rgb(ink_rgb, paper_rgb, 0.62)
    past_rubric = blend_rgb(accent_rgb, paper_rgb, 0.45)
    future_rubric = blend_rgb(accent_rgb, paper_rgb, 0.58)

    for b in blocks:
        t_idx = b["turn_idx"]
        if active_turn_idx is None:
            # Before the first turn of this folio speaks, all paragraphs on the right page
            # are rendered in `future_ink`
            text_color = future_ink + (255,)
            rub_color = future_rubric + (255,)
        elif t_idx == active_turn_idx:
            text_color = ink_rgb + (255,)
            rub_color = accent_rgb + (255,)
        elif t_idx < active_turn_idx:
            text_color = past_ink + (255,)
            rub_color = past_rubric + (255,)
        else:
            text_color = future_ink + (255,)
            rub_color = future_rubric + (255,)

        cy = y_start + b["y_offset"]
        if b["show_rubric"]:
            draw_tracked_text(
                draw_hi,
                (rx0 * ss, cy),
                b["speaker_label"],
                font_rubric,
                rub_color,
                tracking=1.5 * ss,
                anchor="la",
            )
            cy += b["rubric_h"]

        for line in b["lines"]:
            draw_hi.text((rx0 * ss, cy), line, font=font_body, fill=text_color)
            cy += b["line_h"]

    # Right page footer labels
    draw_tracked_text(
        draw_hi,
        (rx0 * ss, 990 * ss),
        f"SCENE {plate_romans[scene_idx]}",
        font_header,
        muted_rgb + (255,),
        tracking=1.6 * ss,
        anchor="la",
    )
    draw_tracked_text(
        draw_hi,
        (rx1 * ss, 990 * ss),
        f"FOLIO {book['roman']}.{folio_idx + 1}",
        font_header,
        muted_rgb + (255,),
        tracking=1.6 * ss,
        anchor="ra",
    )

    txt_lo = txt_hi.resize((W, H), Image.Resampling.LANCZOS)
    im = Image.alpha_composite(im, txt_lo)
    return np.array(im.convert("RGB"), dtype=np.uint8)


def render_book_preview_frames(book: dict):
    """Generate static PNG keyframes (Title Card + 3 Right-Hand Folios with their Left-Hand Pop-Up Scene) for visual audit."""
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    book_id = book["id"]
    pal = book["palette"]
    paper_rgb = hex_to_rgb(pal["paper"])
    accent_rgb = hex_to_rgb(pal["accent"])

    paper_bg = make_paper_canvas(paper_rgb, seed=hash(book_id) & 0xFFFF)
    title_arr = render_title_card(book, paper_bg)
    Image.fromarray(title_arr).save(PREVIEW_DIR / f"{book_id}_preview_title.png")

    folios = book.get("folios", book["scenes"])
    n_folios = max(1, len(folios))
    popup_packs = {
        s_idx: prepare_popup_spread_pack(book, s_idx, paper_bg)
        for s_idx in range(len(book["scenes"]))
    }

    for f_idx, folio in enumerate(folios):
        s_idx = int(folio.get("scene_idx", f_idx))
        f_turns = [
            t
            for t in book["turns"]
            if int(t.get("folio_idx", t.get("page_idx", t["scene_idx"]))) == f_idx
        ]
        mid_turn_idx = f_turns[len(f_turns) // 2]["turn_idx"] if f_turns else None
        layer = render_spread_turn_layer(book, f_idx, mid_turn_idx, paper_bg)

        composite_popup_diorama_on_spread(
            layer,
            popup_packs[s_idx],
            fold_progress=1.0,
            chapter_progress=(f_idx + 0.5) / float(n_folios),
            accent_rgb=accent_rgb,
        )
        Image.fromarray(layer).save(
            PREVIEW_DIR / f"{book_id}_preview_scene_{f_idx + 1}.png"
        )
    print(
        f"[PREVIEW] Saved {n_folios + 1} pop-up preview PNGs for {book_id} ({len(book['scenes'])} visual scenes, {n_folios} text folios)"
    )


def render_book_video(book: dict, out_mp4_override: Path | None = None) -> Path:
    """Render a full 1920x1080 24fps MP4 for a single book chapter with:
    - Decoupled Left-Hand 3D Pop-Up Visual Scenes (`scenes`) and Right-Hand Text Pages (`folios`):
      * When advancing to a new text folio within the SAME visual scene, the left-hand 3D pop-up
        diorama stays 100% upright and stationary while the right-hand page (`x >= SPINE_X + 2`)
        smoothly crossfades (`0.45s`) to the new folio text.
      * When advancing to a NEW visual scene (Title Card -> Scene I, or Scene I -> Scene II in
        multi-location chapters), a full 3D spine-hinged cylindrical page turn (`1.45s`) and
        coordinated pop-up folding-down (`0.0s .. 0.68s`) / unfolding (`1.15s .. 2.75s`) executes.
    - Classic 3-state turn-level ink highlighting with 0.22s crossfades.
    """
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    book_id = book["id"]
    out_mp4 = out_mp4_override if out_mp4_override is not None else (VIDEO_DIR / f"{book_id}.mp4")
    master_wav = ROOT / book["master_wav"]

    pal = book["palette"]
    paper_rgb = hex_to_rgb(pal["paper"])
    accent_rgb = hex_to_rgb(pal["accent"])

    paper_bg = make_paper_canvas(paper_rgb, seed=hash(book_id) & 0xFFFF)
    title_card = render_title_card(book, paper_bg)

    total_dur = float(book["total_duration_sec"])
    total_frames = int(round(total_dur * FPS))
    title_end_sec = float(book["title_card_end_sec"])
    scenes = book["scenes"]
    folios = book.get("folios", scenes)
    turns = book["turns"]

    # Pre-render pop-up diorama packs for each distinct visual scene
    popup_packs: dict[int, dict] = {
        s_idx: prepare_popup_spread_pack(book, s_idx, paper_bg)
        for s_idx in range(len(scenes))
    }

    # Pre-render static spread layers for every folio:
    # - `(f_idx, None)`: all turns on `f_idx` in `future_ink` (before first turn of folio speaks)
    # - `(f_idx, t_idx)`: `t_idx` active in `ink_rgb`
    # - `(f_idx, -1)`: all turns on `f_idx` in `past_ink` (after last turn of folio finishes)
    turn_layers: dict[tuple[int, int | None], np.ndarray] = {}
    folio_turns_map: dict[int, list[dict]] = {}

    for f_idx, _ in enumerate(folios):
        f_turns = [
            t
            for t in turns
            if int(t.get("folio_idx", t.get("page_idx", t["scene_idx"]))) == f_idx
        ]
        folio_turns_map[f_idx] = f_turns
        turn_layers[(f_idx, None)] = render_spread_turn_layer(book, f_idx, None, paper_bg)
        turn_layers[(f_idx, -1)] = render_spread_turn_layer(book, f_idx, 999999, paper_bg)
        for t in f_turns:
            t_idx = t["turn_idx"]
            turn_layers[(f_idx, t_idx)] = render_spread_turn_layer(
                book, f_idx, t_idx, paper_bg
            )

    is_long_part = total_dur > 240.0
    preset = "fast" if is_long_part else "veryslow"
    crf = "33" if total_dur > 1050.0 else ("31" if is_long_part else "19")
    audio_br = "133k" if total_dur > 1050.0 else ("136k" if is_long_part else "192k")

    cmd = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{W}x{H}",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-i",
        str(master_wav),
        "-c:v",
        "libx264",
        "-preset",
        preset,
        "-crf",
        crf,
        "-g",
        "2400",
        "-bf",
        "8",
    ]
    if is_long_part:
        maxrate = "24k" if total_dur > 1050.0 else "48k"
        cmd += ["-tune", "stillimage", "-maxrate", maxrate, "-bufsize", "192k"]
    cmd += [
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-ar",
        "48000",
        "-b:a",
        audio_br,
        "-shortest",
        "-movflags",
        "+faststart",
        str(out_mp4),
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None

    fade_in_dur = 0.55
    page_turn_dur = 1.45
    unfold_start_offset = 1.15
    unfold_dur = 1.60
    turn_crossfade_dur = 0.22
    folio_fade_dur = 0.45
    outro_fade_dur = 0.70
    title_turn_start = max(fade_in_dur + 0.35, title_end_sec - 1.15)

    paper_solid = np.empty((H, W, 3), dtype=np.uint8)
    paper_solid[:, :] = paper_rgb

    work_buf = np.empty((H, W, 3), dtype=np.uint8)
    prev_buf = np.empty((H, W, 3), dtype=np.uint8)

    for frame_num in range(total_frames):
        t_sec = frame_num / float(FPS)

        # Stage 1: Title Card before title page turn begins
        if t_sec < title_turn_start:
            if t_sec < fade_in_dur:
                a = t_sec / fade_in_dur
                frame = (
                    paper_solid.astype(np.float32) * (1.0 - a)
                    + title_card.astype(np.float32) * a
                ).astype(np.uint8)
                proc.stdin.write(frame.tobytes())
            else:
                proc.stdin.write(title_card.tobytes())
            continue

        # Determine active text folio `f_idx` directly from `folios[idx_f]["start_sec"]`
        f_idx = 0
        for idx_f, fl in enumerate(folios):
            if t_sec >= float(fl["start_sec"]):
                f_idx = idx_f
            else:
                break

        folio_win = folios[f_idx]
        s_idx = int(folio_win.get("scene_idx", f_idx))
        sc_win = scenes[s_idx]

        dt_folio = max(0.0, t_sec - float(folio_win["start_sec"]))
        dt_sc = max(0.0, t_sec - float(sc_win["start_sec"]))
        f_turns = folio_turns_map[f_idx]

        # Determine active turn within `f_idx`:
        # - `None` before the first turn of `f_idx` begins speaking
        # - `cur_turn["turn_idx"]` while a turn on `f_idx` is active
        # - `-1` after the last turn of `f_idx` finishes speaking (settling into `past_ink`)
        active_turn_idx: int | None = None
        prev_state_key: tuple[int, int | None] | None = None
        dt_turn = 999.0

        if f_turns and t_sec >= float(f_turns[0]["start_sec"]):
            k_active = 0
            for k, trn in enumerate(f_turns):
                if t_sec >= float(trn["start_sec"]):
                    k_active = k
                else:
                    break
            cur_turn = f_turns[k_active]
            if k_active == len(f_turns) - 1 and t_sec >= float(cur_turn["end_sec"]):
                active_turn_idx = -1
                dt_turn = t_sec - float(cur_turn["end_sec"])
                prev_state_key = (f_idx, cur_turn["turn_idx"])
            else:
                active_turn_idx = cur_turn["turn_idx"]
                dt_turn = t_sec - float(cur_turn["start_sec"])
                if k_active == 0:
                    prev_state_key = (f_idx, None)
                else:
                    prev_state_key = (f_idx, f_turns[k_active - 1]["turn_idx"])

        # Compose spread layer with smooth 0.22s ink crossfade when `active_turn_idx` advances
        cur_layer = turn_layers[(f_idx, active_turn_idx)]
        if prev_state_key is not None and 0.0 <= dt_turn < turn_crossfade_dur:
            alpha = dt_turn / turn_crossfade_dur
            prev_layer = turn_layers[prev_state_key]
            np.copyto(
                work_buf,
                (
                    prev_layer.astype(np.float32) * (1.0 - alpha)
                    + cur_layer.astype(np.float32) * alpha
                ).astype(np.uint8),
            )
        else:
            np.copyto(work_buf, cur_layer)

        # Check whether `f_idx` is a same-scene text-folio continuation or a new visual scene
        is_same_scene_folio_advance = (
            f_idx > 0
            and int(folios[f_idx - 1].get("scene_idx", f_idx - 1)) == s_idx
        )

        # For a same-scene text-folio advance (`Folio 0 -> 1` or `Folio 1 -> 2` within the same
        # visual scene), smoothly crossfade ONLY the right-hand text page (`x >= SPINE_X + 2`)
        # over `folio_fade_dur = 0.45s` while the left page and 3D pop-up diorama stay untouched!
        if is_same_scene_folio_advance and 0.0 <= dt_folio < folio_fade_dur:
            u_f = dt_folio / folio_fade_dur
            alpha_f = 0.5 - 0.5 * math.cos(math.pi * u_f)
            prev_folio_layer = turn_layers[(f_idx - 1, -1)]
            work_buf[:, SPINE_X + 2 :] = (
                prev_folio_layer[:, SPINE_X + 2 :].astype(np.float32) * (1.0 - alpha_f)
                + work_buf[:, SPINE_X + 2 :].astype(np.float32) * alpha_f
            ).astype(np.uint8)

        chap_prog = max(
            0.0, min(1.0, (t_sec - title_end_sec) / max(1.0, total_dur - title_end_sec))
        )

        # Pop-up unfold timing:
        # Unfolds ONLY at the start of a visual scene (`s_idx == 0` opening from Title Card,
        # or `s_idx > 0` when a new visual scene begins at `sc_win["start_sec"]`).
        # Across all subsequent text folios of the same visual scene, `dt_sc` is large, so
        # `in_fold == 1.0` continuously and the pop-up diorama stands rock-steady!
        if s_idx == 0:
            dt_open = max(0.0, t_sec - title_turn_start)
            in_fold = min(1.0, max(0.0, (dt_open - unfold_start_offset) / unfold_dur))
        else:
            in_fold = min(1.0, max(0.0, (dt_sc - unfold_start_offset) / unfold_dur))

        composite_popup_diorama_on_spread(
            work_buf,
            popup_packs[s_idx],
            fold_progress=in_fold,
            chapter_progress=chap_prog,
            accent_rgb=accent_rgb,
        )

        # 3D Spine-Hinged Page Turn from Title Card -> Scene I (when f_idx == 0)
        if f_idx == 0 and (t_sec - title_turn_start) < page_turn_dur:
            turn_u = (t_sec - title_turn_start) / page_turn_dur
            work_buf = render_page_turn_transition(
                title_card, work_buf, turn_u, paper_rgb=paper_rgb
            )

        # 3D Spine-Hinged Page Turn & Folding-Down of outgoing spread ONLY when the visual scene changes!
        elif (
            f_idx > 0
            and not is_same_scene_folio_advance
            and 0.0 <= dt_sc < page_turn_dur
        ):
            prev_f = f_idx - 1
            prev_s = s_idx - 1
            out_fold = max(0.0, 1.0 - min(1.0, dt_sc / 0.68))
            np.copyto(prev_buf, turn_layers[(prev_f, -1)])
            composite_popup_diorama_on_spread(
                prev_buf,
                popup_packs[prev_s],
                fold_progress=out_fold,
                chapter_progress=chap_prog,
                accent_rgb=accent_rgb,
            )
            turn_u = dt_sc / page_turn_dur
            work_buf = render_page_turn_transition(
                prev_buf, work_buf, turn_u, paper_rgb=paper_rgb
            )

        # Outro fade
        if total_dur - t_sec < outro_fade_dur:
            a = max(0.0, min(1.0, (total_dur - t_sec) / outro_fade_dur))
            out_frame = (
                paper_solid.astype(np.float32) * (1.0 - a)
                + work_buf.astype(np.float32) * a
            ).astype(np.uint8)
            proc.stdin.write(out_frame.tobytes())
        else:
            proc.stdin.write(work_buf.tobytes())

    proc.stdin.close()
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg failed for {book_id} with exit code {rc}")
    print(
        f"[VIDEO OK] {out_mp4.name} ({out_mp4.stat().st_size / (1024*1024):.2f} MB, {total_dur:.2f}s)"
    )
    return out_mp4


def concat_anthology_video(book_mp4s: list[Path], out_mp4: Path):
    concat_list = VIDEO_DIR / "concat_list.txt"
    lines = [f"file '{p.resolve()}'" for p in book_mp4s]
    concat_list.write_text("\n".join(lines) + "\n")
    cmd = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_list),
        "-c:v",
        "copy",
        "-c:a",
        "copy",
        "-movflags",
        "+faststart",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True)
    print(f"[ANTHOLOGY OK] {out_mp4} ({out_mp4.stat().st_size / (1024*1024):.2f} MB)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview-only", action="store_true")
    parser.add_argument("--book", help="Optional book_id filter")
    parser.add_argument(
        "--manifest", default=str(TIMELINE_PATH), help="Path to timeline manifest JSON"
    )
    parser.add_argument(
        "--anthology-out",
        default=str(VIDEO_DIR / "classic_novels_opening_chapters.mp4"),
        help="Output path for concatenated anthology MP4",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    timeline = json.loads(manifest_path.read_text())
    books = [b for b in timeline["books"] if not args.book or b["id"] == args.book]

    for b in books:
        render_book_preview_frames(b)

    if args.preview_only:
        return

    with concurrent.futures.ProcessPoolExecutor(max_workers=5) as ex:
        futs = {ex.submit(render_book_video, b): b["id"] for b in books}
        for f in concurrent.futures.as_completed(futs):
            f.result()

    if not args.book:
        ordered_mp4s = [VIDEO_DIR / f"{b['id']}.mp4" for b in timeline["books"]]
        anthology_mp4 = Path(args.anthology_out)
        concat_anthology_video(ordered_mp4s, anthology_mp4)


if __name__ == "__main__":
    main()
