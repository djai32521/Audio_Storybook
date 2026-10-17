#!/usr/bin/env python3
"""Render Full-Screen 1080p 24fps Victorian Paper Toy Theatre Video for Book VII: The Tragedy of Macbeth.

Architecture (Zero Book Chrome — 100% of the 1920x1080 Frame IS the Victorian Paper Toy Theatre):
1. Stage Facing & Dwell Heuristic (`MIN_FACING_DWELL_SEC = 18.0`):
   - Characters NEVER flip back and forth on short conversational lines (`< 15s`).
   - A standee only changes its horizontal orientation (`flip_x`) on a major blocking transition
     (such as another character vanishing or entering on the opposite side of the stage) where the
     new orientation is held for `>= 18.0s`.
   - Scene 0 (Act I, Scene 1): Second Witch (`center`) stays 100% rock-steady (`0` flips, no spinning).
   - Scene 1 (Act I, Scene 3): Macbeth (`->`) and Banquo (`->`) hold a steady rightward gaze toward
     the Weird Sisters (`<-`) throughout the entire encounter (`0` flips during Turns 14..24),
     pivoting left (`<-`, `21.2s` dwell) only after the Witches vanish (`Turn 25`), and pivoting
     right (`->`, `63.2s` dwell) when Ross enters (`Turn 28`).
   - Scene 2 (Act I, Scene 5): Lady Macbeth (`<-`) enters reading the letter (`x = 1060`), then glides
     to `x = 1300` as Macbeth (`->`, `x = 600`) enters so both stand face-to-face (`0` flips).
   - Scene 3 (Act II, Scenes 1 & 2): Macbeth (`->`, `x = 560`) gazes at the hovering spectral dagger
     (`<-`, `x = 1080, y_bottom = 660`, drawn without a floor push-strip or floor shadow, with a
     ghostly golden-amber glow and `±5px` sinusoidal vertical hover) before exiting right (`x -> 1820`)
     into Duncan's chamber; Lady Macbeth (`->`, `x = 580`, `pre_flip_x = True`) enters from the left
     wing and Macbeth re-enters from the right wing with two bloody daggers (`<-`, `x = 1310`) to
     stand face-to-face (`0` flips) through the knocking at the gate.
2. Layer 0 (Deep Moorland Heath & Inverness Castle Backdrops, 1920x1080):
   - Full-stage copperplate & watercolour backdrops (`07_macbeth_spread_{1..4}_bg.jpg`) with
     atmospheric chiaroscuro vignette, opening thunder-and-lightning sky flashes, spectral dagger
     glow, castle bell resonance, knocking-at-the-gate archway/torch pulses, and speaker-tracked
     candle-footlight floor pools.
3. Layer 1 (Perspective-Foreshortened Stage Floor & Recessed Horizontal Slider Slots, y = 884..1036):
   - Antique painted timber-and-flagstone Toy Theatre stage deck with perspective plank seams
     and two recessed horizontal slider track slots (`TRACK_REAR_Y = 918` and `TRACK_FRONT_Y = 946`).
4. Layer 2 (2K-Supersampled Die-Cut Paper Characters on Brass/Cardstock Slider Strips):
   - Upright die-cut cardstock standees downsampled from dedicated 2K (`1792x2400`) lossless PNG
     plates with 3D beveled cream paper borders, paper grain, and tarnished-brass/cardstock slider
     push-strips running inside the stage slots into the nearest side wing.
5. Layer 3A (Foreground Cut-Paper Scenic Side-Wing Flats, x = 0..222 & x = 1698..1920):
   - Sits IN FRONT of Layer 2 so entering and exiting characters physically slide out from behind
     (and back behind) the opaque foreground paper side-wings.
6. Layer 4 (Painted Crimson-and-Gold Paper Act-Drop Curtain, x = 132..1788, y = 78..952):
   - Lowers and rises vertically with a rolling timber baton, gold-tassel bottom fringe, and cast
     shadow for the Opening (`0.0s..5.0s`), all three Scene Changes (`0->1`, `1->2`, `2->3`), and
     the Finale Curtain Call (`722.2s..724.8s`).
7. Layer 3B (Outer Victorian Toy Theatre Proscenium Pilasters, Top Crimson Swagged Valance &
   Front Stage Apron with 9 Warm Brass Candle Footlight Shields).
"""

import argparse
import json
import math
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "audio" / "macbeth_manifest.json"
FONTS_DIR = ROOT / "fonts"
VIDEO_DIR = ROOT / "video"
PREVIEW_DIR = VIDEO_DIR / "previews"
PROSCENIUM_ASSET_PATH = ROOT / "illustrations" / "popup" / "07_macbeth_proscenium_wings.jpg"

W, H = 1920, 1080
FPS = 24

# Minimum horizontal orientation dwell time (seconds) to forbid mid-dialogue back-and-forth flips
MIN_FACING_DWELL_SEC = 18.0

# Stage floor & recessed horizontal slider track geometry (1920x1080 full-screen Toy Theatre)
STAGE_FLOOR_Y = 884
TRACK_REAR_Y = 918
TRACK_FRONT_Y = 946
APRON_TOP_Y = 1022

# Foreground side-wing occlusion boundaries (Layer 3A sits in front of Layer 2 characters)
LEFT_WING_EDGE_X = 218
RIGHT_WING_EDGE_X = 1702

# Memoization cache for 2K solo PNG foreground extractions
_STANDEE_2K_CACHE: dict[Path, tuple[np.ndarray, np.ndarray]] = {}

# Full-screen 1920x1080 Toy Theatre character layout across all 4 Visual Scenes
MACBETH_STAGE_LAYOUT = {
    0: {
        # Visual Scene 0 (Act I, Scene 1 — A Desert Place): Three individual Weird Sisters
        "center": {
            "standee_file": "07_macbeth_standee_s1_center.png",
            "x_center": 960,
            "y_hinge": TRACK_REAR_Y + 2,
            "track_y": TRACK_REAR_Y,
            "z": 0.55,
            "target_h": 495,
            "max_w": 420,
            "home_wing": "left",
            "speaker": "second_witch",
            "pre_flip_x": False,
        },
        "left": {
            "standee_file": "07_macbeth_standee_s1_left.png",
            "x_center": 470,
            "y_hinge": TRACK_FRONT_Y + 2,
            "track_y": TRACK_FRONT_Y,
            "z": 0.82,
            "target_h": 615,
            "max_w": 390,
            "home_wing": "left",
            "speaker": "first_witch",
            "pre_flip_x": False,
        },
        "right": {
            "standee_file": "07_macbeth_standee_s1_right.png",
            "x_center": 1450,
            "y_hinge": TRACK_FRONT_Y + 2,
            "track_y": TRACK_FRONT_Y,
            "z": 0.90,
            "target_h": 628,
            "max_w": 390,
            "home_wing": "right",
            "speaker": "third_witch",
            "pre_flip_x": False,
        },
    },
    1: {
        # Visual Scene 1 (Act I, Scene 3 — A Heath near Forres):
        # Left = Macbeth (facing right ->), Center = Banquo (facing right ->, pivots left <- after vanish,
        # then right -> when Ross enters), Right Witches = Weird Sisters cluster (<-), Right Ross = Ross (<-)
        "center": {
            "standee_file": "07_macbeth_standee_s2_center.png",
            "x_center": 835,
            "y_hinge": TRACK_REAR_Y + 2,
            "track_y": TRACK_REAR_Y,
            "z": 0.64,
            "target_h": 604,
            "max_w": 390,
            "home_wing": "left",
            "speaker": "banquo",
            "pre_flip_x": False,
        },
        "right_witches": {
            "standee_file": "07_macbeth_standee_s2_right.png",
            "x_center": 1435,
            "y_hinge": TRACK_REAR_Y + 4,
            "track_y": TRACK_REAR_Y,
            "z": 0.78,
            "target_h": 584,
            "max_w": 470,
            "home_wing": "right",
            "speaker": "weird_sisters",
            "pre_flip_x": False,
        },
        "right_ross": {
            "standee_file": "07_macbeth_standee_s2_ross.png",
            "x_center": 1410,
            "y_hinge": TRACK_FRONT_Y + 2,
            "track_y": TRACK_FRONT_Y,
            "z": 0.86,
            "target_h": 622,
            "max_w": 400,
            "home_wing": "right",
            "speaker": "ross",
            "pre_flip_x": False,
        },
        "left": {
            "standee_file": "07_macbeth_standee_s2_left.png",
            "x_center": 455,
            "y_hinge": TRACK_FRONT_Y + 2,
            "track_y": TRACK_FRONT_Y,
            "z": 0.92,
            "target_h": 632,
            "max_w": 400,
            "home_wing": "left",
            "speaker": "macbeth",
            "pre_flip_x": False,
        },
    },
    2: {
        # Visual Scene 2 (Act I, Scene 5 — Inverness. Macbeth's Castle):
        # Right = Lady Macbeth (facing left <-, enters to x=1060 for letter/invocation, glides to x=1300),
        # Left = Macbeth (facing right ->, enters to x=600)
        "right": {
            "standee_file": "07_macbeth_standee_s3_lady.png",
            "x_center": 1300,
            "y_hinge": TRACK_REAR_Y + 2,
            "track_y": TRACK_REAR_Y,
            "z": 0.72,
            "target_h": 612,
            "max_w": 395,
            "home_wing": "right",
            "speaker": "lady_macbeth",
            "pre_flip_x": False,
        },
        "left": {
            "standee_file": "07_macbeth_standee_s2_left.png",
            "x_center": 600,
            "y_hinge": TRACK_FRONT_Y + 2,
            "track_y": TRACK_FRONT_Y,
            "z": 0.88,
            "target_h": 632,
            "max_w": 400,
            "home_wing": "left",
            "speaker": "macbeth",
            "pre_flip_x": False,
        },
    },
    3: {
        # Visual Scene 3 (Act II, Scenes 1 & 2 — Midnight at Inverness):
        # Beat A: macbeth_dagger_soliloquy (x=560, ->) + floating_dagger (x=1080, y_bottom=660, <-, no rod/shadow)
        # Beat B: lady_after_murder (x=580, -> via pre_flip_x=True) + macbeth_bloody_daggers (x=1310, <-)
        "lady_after_murder": {
            "standee_file": "07_macbeth_standee_s3_lady.png",
            "x_center": 580,
            "y_hinge": TRACK_REAR_Y + 2,
            "track_y": TRACK_REAR_Y,
            "z": 0.72,
            "target_h": 612,
            "max_w": 395,
            "home_wing": "left",
            "speaker": "lady_macbeth",
            "pre_flip_x": True,
        },
        "macbeth_dagger_soliloquy": {
            "standee_file": "07_macbeth_standee_s2_left.png",
            "x_center": 560,
            "y_hinge": TRACK_FRONT_Y + 2,
            "track_y": TRACK_FRONT_Y,
            "z": 0.84,
            "target_h": 632,
            "max_w": 400,
            "home_wing": "left",
            "speaker": "macbeth",
            "pre_flip_x": False,
        },
        "macbeth_bloody_daggers": {
            "standee_file": "07_macbeth_standee_s4_macbeth_daggers.png",
            "x_center": 1310,
            "y_hinge": TRACK_FRONT_Y + 2,
            "track_y": TRACK_FRONT_Y,
            "z": 0.90,
            "target_h": 632,
            "max_w": 410,
            "home_wing": "right",
            "speaker": "macbeth",
            "pre_flip_x": False,
        },
        "floating_dagger": {
            "standee_file": "07_macbeth_standee_s4_dagger.png",
            "x_center": 1080,
            "y_hinge": 660,
            "track_y": 660,
            "z": 0.96,
            "target_h": 270,
            "max_w": 235,
            "home_wing": "right",
            "speaker": "dagger",
            "pre_flip_x": False,
            "is_floating": True,
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


def smoothstep(u: float) -> float:
    u = max(0.0, min(1.0, float(u)))
    return u * u * (3.0 - 2.0 * u)


def smootherstep(u: float) -> float:
    u = max(0.0, min(1.0, float(u)))
    return u * u * u * (u * (u * 6.0 - 15.0) + 10.0)


def load_font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(
        str(FONTS_DIR / name), size, layout_engine=ImageFont.Layout.BASIC
    )


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


def extract_single_standee_2k(standee_png_path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Extract the full-resolution 2K `(rgb_crop, mask_crop)` directly from a dedicated solo
    standee lossless PNG (`illustrations/popup/07_macbeth_standee_*.png`, 1792x2400) with
    memoization so shared character plates across scenes are extracted only once.
    """
    resolved = standee_png_path.resolve()
    if resolved in _STANDEE_2K_CACHE:
        rgb_c, mask_c = _STANDEE_2K_CACHE[resolved]
        return rgb_c.copy(), mask_c.copy()

    im = Image.open(standee_png_path).convert("RGB")
    arr = np.array(im, dtype=np.float32)
    h, w, _ = arr.shape

    top = np.median(arr[:16, :, :], axis=0)
    bot = np.median(arr[-16:, :, :], axis=0)
    v = np.linspace(0.0, 1.0, h, dtype=np.float32)[:, None, None]
    bg_field = top[None, :, :] * (1.0 - v) + bot[None, :, :] * v
    dist = np.linalg.norm(arr - bg_field, axis=2)

    gray = arr.mean(axis=2)
    grad = np.hypot(ndimage.sobel(gray, axis=1), ndimage.sobel(gray, axis=0))

    is_paper_bg = (gray > 218.0) & (grad < 16.0) & ((arr.max(axis=2) - arr.min(axis=2)) < 42.0)
    core = ((dist > 22.0) | (grad > 18.0)) & (~is_paper_bg)
    core[:4, :] = False
    core[-4:, :] = False
    core[:, :4] = False
    core[:, -4:] = False

    struct = ndimage.generate_binary_structure(2, 2)
    fg = ndimage.binary_closing(core, structure=struct, iterations=2)

    holes = ndimage.binary_fill_holes(fg) & (~fg)
    lbl_h, n_h = ndimage.label(holes)
    if n_h > 0:
        h_sizes = ndimage.sum(holes, lbl_h, range(1, n_h + 1))
        for idx_h, sz_h in enumerate(h_sizes, 1):
            if sz_h < 2500:
                fg |= lbl_h == idx_h

    fg = ndimage.binary_erosion(fg, structure=struct, iterations=1)
    fg &= ~is_paper_bg

    lbl, n_cc = ndimage.label(fg)
    if n_cc > 0:
        sizes = ndimage.sum(fg, lbl, range(1, n_cc + 1))
        max_sz = max(sizes) if len(sizes) > 0 else 0
        keep = np.zeros_like(fg)
        for idx_c, sz in enumerate(sizes, 1):
            if sz >= max(800.0, max_sz * 0.12):
                keep |= lbl == idx_c
        fg = keep

    ys, xs = np.where(fg)
    pad = 10
    y0 = max(0, int(ys.min()) - pad)
    y1 = min(h, int(ys.max()) + pad + 1)
    x0 = max(0, int(xs.min()) - pad)
    x1 = min(w, int(xs.max()) + pad + 1)
    res = (arr[y0:y1, x0:x1].copy(), fg[y0:y1, x0:x1].copy())
    _STANDEE_2K_CACHE[resolved] = res
    return res[0].copy(), res[1].copy()


def build_highres_diecut_standee(
    rgb_crop: np.ndarray,
    mask_crop: np.ndarray,
    target_h: int,
    max_w: int,
    paper_rgb: tuple[int, int, int],
    ink_rgb: tuple[int, int, int],
    seed: int = 101,
    is_floating: bool = False,
) -> Image.Image:
    """Downsample a 2K raw character cutout (~1950px tall) to its full-screen 1080p stage
    height (`~500-632px`) with Lanczos supersampling and crisp copperplate sharpening, then
    generate a native 1080p die-cut cardstock border, 3D paper bevel rim, and paper-grain texture.
    When `is_floating=True` (the spectral dagger in Scene 3), omits the bottom fold-tab crease
    and uses a warm golden-amber spectral parchment border.
    """
    oh, ow = mask_crop.shape
    scale = target_h / float(max(1, oh))
    tw = max(32, int(round(ow * scale)))
    th = max(32, target_h)
    if tw > max_w:
        scale = max_w / float(max(1, ow))
        tw = max_w
        th = max(32, int(round(oh * scale)))

    rgb_im = Image.fromarray(np.clip(rgb_crop, 0, 255).astype(np.uint8), mode="RGB")
    rgb_hi = rgb_im.resize((tw, th), Image.Resampling.LANCZOS)
    rgb_hi = rgb_hi.filter(ImageFilter.UnsharpMask(radius=0.95, percent=58, threshold=2))

    mask_im = Image.fromarray((mask_crop.astype(np.uint8) * 255), mode="L")
    mask_hi = np.array(mask_im.resize((tw, th), Image.Resampling.LANCZOS)) > 115

    pad = 16
    ch, cw = th + pad * 2, tw + pad * 2
    m_pad = np.zeros((ch, cw), dtype=bool)
    m_pad[pad : pad + th, pad : pad + tw] = mask_hi

    rgb_pad = np.full((ch, cw, 3), 255.0, dtype=np.float32)
    rgb_pad[pad : pad + th, pad : pad + tw] = np.array(rgb_hi, dtype=np.float32)

    struct = ndimage.generate_binary_structure(2, 2)
    diecut_core = ndimage.binary_closing(m_pad, structure=struct, iterations=2)
    holes_dc = ndimage.binary_fill_holes(diecut_core) & (~diecut_core)
    lbl_dc, n_dc = ndimage.label(holes_dc)
    if n_dc > 0:
        dc_sizes = ndimage.sum(holes_dc, lbl_dc, range(1, n_dc + 1))
        for idx_dc, sz_dc in enumerate(dc_sizes, 1):
            if sz_dc < 240:
                diecut_core |= lbl_dc == idx_dc

    dist_out = ndimage.distance_transform_edt(~diecut_core)
    dist_in_subj = ndimage.distance_transform_edt(m_pad)
    dist_out_subj = ndimage.distance_transform_edt(~m_pad)

    card_radius = 4.5 if is_floating else 6.0
    bevel_inner = 3.2 if is_floating else 4.5
    alpha = np.clip((card_radius + 0.9 - dist_out) / 1.5, 0.0, 1.0)

    rng = np.random.default_rng(seed)
    if is_floating:
        card_base_rgb = (246, 218, 152)
        edge_dark = (168, 118, 48)
        edge_light = (255, 242, 198)
    else:
        card_base_rgb = blend_rgb(paper_rgb, ink_rgb, 0.18)
        edge_dark = blend_rgb(paper_rgb, ink_rgb, 0.62)
        edge_light = blend_rgb(paper_rgb, ink_rgb, 0.06)

    card_tex = np.empty((ch, cw, 3), dtype=np.float32)
    card_tex[:, :, 0] = card_base_rgb[0]
    card_tex[:, :, 1] = card_base_rgb[1]
    card_tex[:, :, 2] = card_base_rgb[2]
    card_tex += rng.normal(0.0, 1.4, size=(ch, cw, 1)).astype(np.float32)

    subj_weight = np.clip((dist_in_subj - dist_out_subj + 0.9) / 1.8, 0.0, 1.0)[:, :, None]
    comp_rgb = card_tex * (1.0 - subj_weight) + rgb_pad * subj_weight

    gy_d, gx_d = np.gradient(dist_out.astype(np.float32))
    light_dot = gx_d * 0.707 + gy_d * 0.707
    rim_mask = np.clip(1.0 - np.abs(dist_out - (bevel_inner + 0.8)) / 1.4, 0.0, 1.0)
    outer_ink_rim = np.clip(1.0 - np.abs(dist_out - card_radius) / 1.1, 0.0, 1.0)[
        :, :, None
    ]

    shade_w = (rim_mask * np.clip(light_dot + 0.22, 0.0, 1.0))[:, :, None]
    hilite_w = (rim_mask * np.clip(-light_dot, 0.0, 1.0) * 0.70)[:, :, None]

    ed_arr = np.array(edge_dark, dtype=np.float32)[None, None, :]
    el_arr = np.array(edge_light, dtype=np.float32)[None, None, :]
    comp_rgb = comp_rgb * (1.0 - shade_w) + ed_arr * shade_w
    comp_rgb = comp_rgb * (1.0 - hilite_w) + el_arr * hilite_w
    comp_rgb = comp_rgb * (1.0 - 0.55 * outer_ink_rim) + ed_arr * (0.55 * outer_ink_rim)

    ay, ax = np.where(alpha > 0.02)
    if len(ay) > 0:
        y_min, y_max = int(ay.min()), int(ay.max())
        x_min, x_max = int(ax.min()), int(ax.max())
        if not is_floating:
            fold_y = y_max - 8
            if y_min + 20 < fold_y < y_max - 3:
                comp_rgb[fold_y : fold_y + 2, :, :] *= 0.84
                comp_rgb[fold_y + 2 : fold_y + 4, :, :] = np.minimum(
                    255.0, comp_rgb[fold_y + 2 : fold_y + 4, :, :] * 1.08
                )
        rgba = np.zeros((y_max - y_min + 1, x_max - x_min + 1, 4), dtype=np.uint8)
        rgba[:, :, :3] = np.clip(
            comp_rgb[y_min : y_max + 1, x_min : x_max + 1], 0, 255
        ).astype(np.uint8)
        rgba[:, :, 3] = np.clip(
            alpha[y_min : y_max + 1, x_min : x_max + 1] * 255.0, 0, 255
        ).astype(np.uint8)
        return Image.fromarray(rgba, mode="RGBA")

    return Image.new("RGBA", (64, 64), (0, 0, 0, 0))


def build_stage_floor_and_backdrop(
    raw_bg: Image.Image,
    scene_idx: int,
    paper_rgb: tuple[int, int, int],
    ink_rgb: tuple[int, int, int],
) -> tuple[np.ndarray, Image.Image]:
    """From `07_macbeth_spread_{1..4}_bg.jpg`:
    1. Build `Layer 0 + Layer 1` (1920x1080 RGB):
       - Frame the central moorland heath (Scenes 0 & 1) or Inverness castle hall/courtyard
         (Scenes 2 & 3) across the stage opening (`y = 0 .. STAGE_FLOOR_Y + 24`).
       - Paint the perspective-foreshortened antique wooden/flagstone Toy Theatre stage floor
         (`y = STAGE_FLOOR_Y .. H`) with two recessed horizontal slider track slots at
         `TRACK_REAR_Y = 918` and `TRACK_FRONT_Y = 946`.
    2. Build `Layer 3A` (1920x1080 RGBA):
       - Foreground Cut-Paper Scenic Side-Wing Flats (`x = 0..224` on the left and
         `x = 1696..1920` on the right, `y = 60..954`) extracted from the outer rock crags or
         stone castle piers of `raw_bg`, complete with a die-cut silhouette profile, a 6px
         cream cardstock bevel border, and a 24px soft drop shadow cast onto Layer 2 and Layer 0/1!
    """
    src_arr = np.array(raw_bg.convert("RGB"), dtype=np.float32)
    sh, sw, _ = src_arr.shape
    backdrop_h = STAGE_FLOOR_Y + 24
    stage_arr = np.zeros((H, W, 3), dtype=np.float32)

    if scene_idx == 0:
        cx0, cx1 = int(sw * 0.182), int(sw * 0.820)
        center_crop = raw_bg.crop((cx0, 0, cx1, sh)).resize(
            (W, backdrop_h), Image.Resampling.LANCZOS
        )
        center_crop = center_crop.filter(
            ImageFilter.UnsharpMask(radius=1.2, percent=45, threshold=3)
        )
        stage_arr[:backdrop_h, :, :] = np.array(center_crop, dtype=np.float32)
    elif scene_idx == 1:
        cx0, cx1 = int(sw * 0.156), int(sw * 0.825)
        center_crop = raw_bg.crop((cx0, 0, cx1, sh)).resize(
            (W, backdrop_h), Image.Resampling.LANCZOS
        )
        center_crop = center_crop.filter(
            ImageFilter.UnsharpMask(radius=1.2, percent=45, threshold=3)
        )
        stage_arr[:backdrop_h, :, :] = np.array(center_crop, dtype=np.float32)
    elif scene_idx == 2:
        # Great Hall of Inverness: crop between the outer foreground piers so the vaulted hall,
        # Celtic tapestries, flaming wall torches, and central Gothic arch span the stage opening
        cx0, cx1 = int(sw * 0.085), int(sw * 0.915)
        center_crop = raw_bg.crop((cx0, 0, cx1, sh)).resize(
            (W, backdrop_h), Image.Resampling.LANCZOS
        )
        center_crop = center_crop.filter(
            ImageFilter.UnsharpMask(radius=1.15, percent=48, threshold=3)
        )
        stage_arr[:backdrop_h, :, :] = np.array(center_crop, dtype=np.float32)
    else:
        # Scene 3 (Midnight Courtyard at Inverness): fit the full courtyard width into the visible
        # stage opening (x = 156 .. 1764) so the left Gothic arch, central crenellated wall with
        # lightning, right chamber stairs, wall torch, and studded wooden gate are all 100% visible
        # between the left/right foreground wings (218 .. 1702)!
        inner_x0, inner_x1 = 156, W - 156
        inner_w = inner_x1 - inner_x0
        full_crop = raw_bg.resize((inner_w, backdrop_h), Image.Resampling.LANCZOS)
        full_crop = full_crop.filter(
            ImageFilter.UnsharpMask(radius=1.15, percent=48, threshold=3)
        )
        full_arr = np.array(full_crop, dtype=np.float32)
        stage_arr[:backdrop_h, inner_x0:inner_x1, :] = full_arr
        stage_arr[:backdrop_h, :inner_x0, :] = full_arr[:, :1, :]
        stage_arr[:backdrop_h, inner_x1:, :] = full_arr[:, -1:, :]

    # Atmospheric stage lighting vignette on the painted backdrop
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    nx = (xx - W * 0.5) / (W * 0.5)
    ny = (yy - H * 0.44) / (H * 0.5)
    vig = np.clip(1.0 - 0.22 * (nx * nx * 0.85 + np.maximum(0.0, -ny) * 0.9), 0.72, 1.0)
    stage_arr[:backdrop_h] *= vig[:backdrop_h, :, None]

    # 2. Build Layer 1: Perspective-Foreshortened Toy Theatre Stage Floor (y = STAGE_FLOOR_Y .. H)
    rng = np.random.default_rng(303 + scene_idx)
    floor_h = H - STAGE_FLOOR_Y
    fy = np.arange(floor_h, dtype=np.float32)[:, None]
    fx = np.arange(W, dtype=np.float32)[None, :]
    v_floor = fy / float(max(1, floor_h - 1))

    deck_back = np.array([42.0, 35.0, 29.0], dtype=np.float32)
    deck_front = np.array([28.0, 22.0, 18.0], dtype=np.float32)
    floor_grad = (
        deck_back[None, None, :] * (1.0 - v_floor[:, :, None])
        + deck_front[None, None, :] * v_floor[:, :, None]
    )
    floor_rgb = np.broadcast_to(floor_grad, (floor_h, W, 3)).copy()

    moor_ground_tint = np.median(
        stage_arr[STAGE_FLOOR_Y - 45 : STAGE_FLOOR_Y - 5, 350 : W - 350, :],
        axis=(0, 1),
    )
    floor_rgb = floor_rgb * 0.68 + moor_ground_tint[None, None, :] * 0.32

    vp_x, vp_y = W * 0.5, 360.0
    dy_vp = (STAGE_FLOOR_Y + fy) - vp_y
    persp_u = (fx - vp_x) / (dy_vp / float(H - vp_y))
    plank_phase = (persp_u / 108.0) * math.pi * 2.0
    plank_seam = np.exp(-((np.sin(plank_phase * 0.5) / 0.045) ** 2))
    plank_tone = 0.04 * np.sin(plank_phase) + 0.02 * np.cos(plank_phase * 2.3)

    grain_noise = ndimage.uniform_filter1d(
        rng.normal(0.0, 2.8, size=(floor_h, W)).astype(np.float32), size=18, axis=1
    )
    floor_rgb *= (1.0 - 0.28 * plank_seam + plank_tone)[:, :, None]
    floor_rgb += grain_noise[:, :, None]

    foot_cx = np.exp(-(((fx - W * 0.5) / 680.0) ** 2))
    foot_cy = np.exp(-(((1.0 - v_floor) / 0.72) ** 2))
    candle_rgb = np.array([245.0, 182.0, 96.0], dtype=np.float32)[None, None, :]
    floor_rgb += candle_rgb * (0.11 * foot_cx * foot_cy)[:, :, None]

    blend_band = 18
    for dy_b in range(blend_band):
        y_abs = STAGE_FLOOR_Y + dy_b
        w_f = smoothstep(dy_b / float(blend_band))
        stage_arr[y_abs] = stage_arr[y_abs] * (1.0 - w_f) + floor_rgb[dy_b] * w_f
    stage_arr[STAGE_FLOOR_Y + blend_band :] = floor_rgb[blend_band:]

    lip_y = STAGE_FLOOR_Y + 14
    stage_arr[lip_y : lip_y + 2, :, :] *= 0.62
    stage_arr[lip_y + 2 : lip_y + 4, :, :] = np.minimum(
        255.0, stage_arr[lip_y + 2 : lip_y + 4, :, :] * 1.12
    )

    bevel_gold = np.array([196.0, 162.0, 112.0], dtype=np.float32)[None, None, :]
    for y_tr in (TRACK_REAR_Y, TRACK_FRONT_Y):
        stage_arr[y_tr - 2 : y_tr, :, :] *= 0.52
        stage_arr[y_tr : y_tr + 5, :, :] *= 0.16
        stage_arr[y_tr + 5 : y_tr + 7, :, :] = (
            stage_arr[y_tr + 5 : y_tr + 7, :, :] * 0.58 + bevel_gold * 0.42
        )
        stage_arr[y_tr + 7 : y_tr + 8, :, :] *= 0.78

    stage_rgb_u8 = np.clip(stage_arr, 0, 255).astype(np.uint8)

    # 3. Build Layer 3A: Foreground Cut-Paper Scenic Side-Wing Flats (x = 0..226 & x = 1694..1920)
    wing_w = 248
    if scene_idx == 0:
        l_src = raw_bg.crop((0, int(sh * 0.22), int(sw * 0.103), sh)).resize(
            (wing_w, H), Image.Resampling.LANCZOS
        )
        r_src = raw_bg.crop((int(sw * 0.897), int(sh * 0.26), sw, sh)).resize(
            (wing_w, H), Image.Resampling.LANCZOS
        )
    elif scene_idx == 1:
        l_src = raw_bg.crop((0, 0, int(sw * 0.160), sh)).resize(
            (wing_w, H), Image.Resampling.LANCZOS
        )
        r_src = raw_bg.crop((int(sw * 0.840), 0, sw, sh)).resize(
            (wing_w, H), Image.Resampling.LANCZOS
        )
    elif scene_idx == 2:
        # Outer twin stone castle columns from spread_3_bg.jpg
        l_src = raw_bg.crop((0, 0, int(sw * 0.125), sh)).resize(
            (wing_w, H), Image.Resampling.LANCZOS
        )
        r_src = raw_bg.crop((int(sw * 0.875), 0, sw, sh)).resize(
            (wing_w, H), Image.Resampling.LANCZOS
        )
    else:
        # Outer stone castle turret walls from spread_4_bg.jpg
        l_src = raw_bg.crop((0, 0, int(sw * 0.115), sh)).resize(
            (wing_w, H), Image.Resampling.LANCZOS
        )
        r_src = raw_bg.crop((int(sw * 0.885), 0, sw, sh)).resize(
            (wing_w, H), Image.Resampling.LANCZOS
        )

    l_src = l_src.filter(ImageFilter.UnsharpMask(radius=1.2, percent=55, threshold=2))
    r_src = r_src.filter(ImageFilter.UnsharpMask(radius=1.2, percent=55, threshold=2))

    l_arr = np.array(l_src, dtype=np.float32) * 0.90
    r_arr = np.array(r_src, dtype=np.float32) * 0.90

    y_norm = np.linspace(0.0, 1.0, H, dtype=np.float32)
    if scene_idx in (0, 1):
        crag_profile_l = (
            222.0
            + 8.0 * np.sin(y_norm * math.pi * 5.0 + 0.4 * scene_idx)
            + 5.5 * np.cos(y_norm * math.pi * 11.0 + 1.1)
            + 3.0 * np.sin(y_norm * math.pi * 23.0)
            + 10.0 * (y_norm**2)
        )
        crag_profile_r = (
            float(W)
            - 222.0
            - 8.0 * np.sin(y_norm * math.pi * 5.0 + 0.9 + 0.4 * scene_idx)
            - 5.5 * np.cos(y_norm * math.pi * 11.0 + 0.3)
            - 3.0 * np.sin(y_norm * math.pi * 23.0 + 0.7)
            - 10.0 * (y_norm**2)
        )
    else:
        # Architectural stone-pier & ashlar-block cut-paper wing profile for Inverness Castle
        ashlar = 3.0 * np.tanh(3.0 * np.sin(y_norm * math.pi * 18.0))
        capital_jut = 10.0 * np.exp(-(((y_norm - 0.34) / 0.035) ** 2))
        plinth_jut = 12.0 * np.clip((y_norm - 0.76) / 0.24, 0.0, 1.0)
        crag_profile_l = 221.0 + ashlar + capital_jut + plinth_jut
        crag_profile_r = float(W) - (221.0 + ashlar + capital_jut + plinth_jut)

    wing_mask = (xx <= crag_profile_l[:, None]) | (xx >= crag_profile_r[:, None])
    wing_mask[TRACK_FRONT_Y + 6 :, :] = False

    dist_out_w = ndimage.distance_transform_edt(~wing_mask)
    dist_in_w = ndimage.distance_transform_edt(wing_mask)

    card_r = 5.5
    wing_alpha = np.clip((card_r + 0.8 - dist_out_w) / 1.4, 0.0, 1.0)
    wing_alpha[TRACK_FRONT_Y + 8 :, :] = 0.0

    wing_rgb = np.zeros((H, W, 3), dtype=np.float32)
    wing_rgb[:, :wing_w, :] = l_arr
    wing_rgb[:, W - wing_w :, :] = r_arr

    card_col = np.array(blend_rgb(paper_rgb, ink_rgb, 0.24), dtype=np.float32)[
        None, None, :
    ]
    edge_dk = np.array(blend_rgb(paper_rgb, ink_rgb, 0.65), dtype=np.float32)[
        None, None, :
    ]

    in_w = np.clip((dist_in_w - dist_out_w + 1.0) / 2.0, 0.0, 1.0)[:, :, None]
    comp_w = card_col * (1.0 - in_w) + wing_rgb * in_w

    outer_line = np.clip(1.0 - np.abs(dist_out_w - card_r) / 1.2, 0.0, 1.0)[:, :, None]
    inner_line = np.clip(1.0 - np.abs(dist_in_w - 1.2) / 1.1, 0.0, 1.0)[:, :, None]
    comp_w = comp_w * (1.0 - 0.65 * outer_line) + edge_dk * (0.65 * outer_line)
    comp_w = comp_w * (1.0 - 0.40 * inner_line) + edge_dk * (0.40 * inner_line)

    sh_alpha = np.clip(np.exp(-dist_out_w / 18.0) * 0.58, 0.0, 0.58)
    sh_alpha[wing_alpha > 0.95] = 0.0
    sh_alpha[TRACK_FRONT_Y + 8 :, :] = 0.0

    wing_layer_rgba = np.zeros((H, W, 4), dtype=np.uint8)
    total_a = np.clip(wing_alpha + sh_alpha * (1.0 - wing_alpha), 0.0, 1.0)
    safe_a = np.maximum(total_a, 1e-5)[:, :, None]
    fg_contrib = (wing_alpha[:, :, None] * comp_w) / safe_a
    wing_layer_rgba[:, :, :3] = np.clip(fg_contrib, 0, 255).astype(np.uint8)
    wing_layer_rgba[:, :, 3] = np.clip(total_a * 255.0, 0, 255).astype(np.uint8)

    return stage_rgb_u8, Image.fromarray(wing_layer_rgba, mode="RGBA")


def build_outer_proscenium_and_footlights(
    paper_rgb: tuple[int, int, int],
    ink_rgb: tuple[int, int, int],
    accent_rgb: tuple[int, int, int],
) -> Image.Image:
    """Build Layer 3B (1920x1080 RGBA): The Outer Pollock's Victorian Toy Theatre Proscenium Frame:
    - Left & Right Gilded/Engraved Architectural Pilasters (`x = 0..136`, `x = 1784..1920`, `y = 0..1034`)
    - Top Proscenium Arch & Festooned Crimson-and-Gold Drapery Valance (`y = 0..106`) with
      scalloped gold fringe, tassels, and central gilded Shakespearean crest cartouche
    - Front Timber-and-Gilt Stage Apron (`y = 1022..1080`) with 9 burnished-brass candle
      footlight shields casting warm upward amber candle glow onto the stage!
    """
    rng = np.random.default_rng(808)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

    rgba = np.zeros((H, W, 4), dtype=np.float32)

    pil_w = 136.0
    in_left_pil = xx <= pil_w
    in_right_pil = xx >= (W - pil_w)
    in_pil = (in_left_pil | in_right_pil) & (yy <= APRON_TOP_Y + 12)

    u_pil = np.where(
        in_left_pil, xx / pil_w, np.where(in_right_pil, (W - 1 - xx) / pil_w, 0.0)
    )
    u_pil = np.clip(u_pil, 0.0, 1.0)

    walnut = np.array([38.0, 26.0, 20.0], dtype=np.float32)
    crimson_panel = np.array([96.0, 26.0, 22.0], dtype=np.float32)
    gold_leaf = np.array([204.0, 164.0, 92.0], dtype=np.float32)
    cream_card = np.array(blend_rgb(paper_rgb, ink_rgb, 0.12), dtype=np.float32)

    in_panel_x = (u_pil >= 0.22) & (u_pil <= 0.74)
    in_panel_y = (yy >= 130.0) & (yy <= APRON_TOP_Y - 36.0)
    in_panel = in_panel_x & in_panel_y

    flute = 0.08 * np.sin(u_pil * math.pi * 18.0)
    damask = 0.06 * np.sin(yy * 0.12) * np.cos(xx * 0.12)

    pil_rgb = np.where(
        in_panel[:, :, None],
        crimson_panel[None, None, :] * (1.0 + damask[:, :, None]),
        walnut[None, None, :] * (1.0 + flute[:, :, None]),
    )

    gold_band = (
        np.exp(-(((u_pil - 0.20) / 0.022) ** 2))
        + np.exp(-(((u_pil - 0.76) / 0.022) ** 2))
        + np.exp(-(((u_pil - 0.91) / 0.025) ** 2))
    )
    cap_bands = (
        np.exp(-(((yy - 124.0) / 4.0) ** 2))
        + np.exp(-(((yy - 134.0) / 3.0) ** 2))
        + np.exp(-(((yy - (APRON_TOP_Y - 32.0)) / 4.0) ** 2))
        + np.exp(-(((yy - (APRON_TOP_Y - 22.0)) / 3.0) ** 2))
    )
    gold_w = np.clip(gold_band + cap_bands * 0.85, 0.0, 1.0)[:, :, None]
    pil_rgb = pil_rgb * (1.0 - 0.78 * gold_w) + gold_leaf[None, None, :] * (
        0.78 * gold_w
    )

    card_rim = np.clip(1.0 - np.abs(u_pil - 0.965) / 0.025, 0.0, 1.0)[:, :, None]
    pil_rgb = pil_rgb * (1.0 - 0.65 * card_rim) + cream_card[None, None, :] * (
        0.65 * card_rim
    )

    pil_dist = np.minimum(
        np.maximum(0.0, xx - pil_w), np.maximum(0.0, (W - pil_w) - xx)
    )
    pil_sh = np.where(
        (~in_pil) & (pil_dist < 32.0) & (yy <= APRON_TOP_Y),
        0.62 * np.exp(-pil_dist / 12.0),
        0.0,
    )

    rgba[in_pil, :3] = pil_rgb[in_pil]
    rgba[in_pil, 3] = 255.0
    sh_mask_p = pil_sh > 0.005
    rgba[sh_mask_p, :3] = 10.0
    rgba[sh_mask_p, 3] = np.maximum(rgba[sh_mask_p, 3], pil_sh[sh_mask_p] * 255.0)

    swag_u = (xx - 120.0) / (W - 240.0)
    swag_wave = np.abs(np.sin(np.clip(swag_u, 0.0, 1.0) * math.pi * 5.0))
    corner_arch = 34.0 * (np.clip(np.abs(xx - W * 0.5) / (W * 0.5 - 110.0), 0.0, 1.2) ** 3)
    valance_bot_y = 76.0 + 20.0 * swag_wave + corner_arch

    in_valance = yy <= valance_bot_y
    fold_shade = (
        0.82
        + 0.22 * np.sin(swag_u * math.pi * 5.0 * 2.0)
        + 0.08 * np.cos(yy * 0.28 + swag_wave * 4.0)
    )
    crimson_base = np.array([112.0, 24.0, 20.0], dtype=np.float32)
    val_rgb = crimson_base[None, None, :] * fold_shade[:, :, None]

    cornice_rib = 0.5 + 0.5 * np.sin(yy * 0.65)
    val_rgb = np.where(
        (yy <= 22.0)[:, :, None],
        walnut[None, None, :] * 0.55
        + gold_leaf[None, None, :] * (0.45 * cornice_rib[:, :, None]),
        val_rgb,
    )

    dist_val_bot = valance_bot_y - yy
    in_fringe = in_valance & (dist_val_bot >= 0.0) & (dist_val_bot <= 12.0)
    tassel_pat = 0.65 + 0.35 * np.sin(xx * 0.52)
    val_rgb = np.where(
        in_fringe[:, :, None],
        gold_leaf[None, None, :] * tassel_pat[:, :, None],
        val_rgb,
    )
    in_val_rim = in_valance & (dist_val_bot < 2.2)
    val_rgb = np.where(
        in_val_rim[:, :, None],
        val_rgb * 0.45,
        val_rgb,
    )

    rgba[in_valance, :3] = val_rgb[in_valance]
    rgba[in_valance, 3] = 255.0

    val_out_d = yy - valance_bot_y
    val_sh = np.where(
        (val_out_d > 0.0) & (val_out_d < 34.0),
        0.64 * np.exp(-val_out_d / 12.5),
        0.0,
    )
    sh_mask_v = val_sh > 0.005
    need_sh_v = sh_mask_v & (rgba[:, :, 3] < 250.0)
    rgba[need_sh_v, :3] = 8.0
    rgba[need_sh_v, 3] = np.maximum(rgba[need_sh_v, 3], val_sh[need_sh_v] * 255.0)

    in_apron = yy >= APRON_TOP_Y
    apron_u = np.clip((yy - APRON_TOP_Y) / float(H - APRON_TOP_Y), 0.0, 1.0)
    apron_rgb = walnut[None, None, :] * (0.85 - 0.25 * apron_u[:, :, None])
    apron_rail = np.exp(-(((yy - (APRON_TOP_Y + 4.5)) / 3.2) ** 2))[:, :, None]
    apron_rgb = apron_rgb * (1.0 - 0.72 * apron_rail) + gold_leaf[None, None, :] * (
        0.72 * apron_rail
    )

    rgba[in_apron, :3] = apron_rgb[in_apron]
    rgba[in_apron, 3] = 255.0

    grain = rng.normal(0.0, 1.3, size=(H, W, 1)).astype(np.float32)
    opaque_m = rgba[:, :, 3] > 240.0
    rgba[opaque_m, :3] = np.clip(rgba[opaque_m, :3] + grain[opaque_m], 0.0, 255.0)

    pros_im = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), mode="RGBA")
    draw = ImageDraw.Draw(pros_im)

    footlight_xs = [290, 458, 625, 792, 960, 1128, 1295, 1462, 1630]
    for fx_c in footlight_xs:
        halo_w, halo_h = 110, 66
        hy, hx = np.mgrid[0:halo_h, 0:halo_w].astype(np.float32)
        hd = np.hypot((hx - halo_w * 0.5) / 42.0, (hy - halo_h * 0.72) / 28.0)
        ha = np.clip(np.exp(-(hd * hd) * 1.3) * 0.42, 0.0, 0.42)
        halo_arr = np.zeros((halo_h, halo_w, 4), dtype=np.uint8)
        halo_arr[:, :, 0] = 255
        halo_arr[:, :, 1] = 198
        halo_arr[:, :, 2] = 102
        halo_arr[:, :, 3] = (ha * 255.0).astype(np.uint8)
        pros_im.alpha_composite(
            Image.fromarray(halo_arr, mode="RGBA"),
            (fx_c - halo_w // 2, APRON_TOP_Y - 44),
        )

        sh_w, sh_h = 54, 34
        sx0, sy0 = fx_c - sh_w // 2, APRON_TOP_Y - 14
        sx1, sy1 = fx_c + sh_w // 2, APRON_TOP_Y + 20
        draw.pieslice(
            [sx0 - 3, sy0 - 3, sx1 + 3, sy1 + 14],
            start=180,
            end=360,
            fill=blend_rgb(paper_rgb, ink_rgb, 0.18) + (255,),
            outline=ink_rgb + (255,),
            width=2,
        )
        draw.pieslice(
            [sx0, sy0, sx1, sy1 + 12],
            start=180,
            end=360,
            fill=(184, 142, 74, 255),
            outline=(72, 48, 24, 255),
            width=2,
        )
        for rib_dx in (-14, -7, 0, 7, 14):
            draw.line(
                [(fx_c + rib_dx * 0.6, sy0 + 3), (fx_c + rib_dx, APRON_TOP_Y + 6)],
                fill=(228, 192, 118, 230),
                width=1,
            )
        draw.line(
            [(sx0 - 4, APRON_TOP_Y + 6), (sx1 + 4, APRON_TOP_Y + 6)],
            fill=(62, 42, 22, 255),
            width=2,
        )

    ss = 3
    crest_hi = Image.new("RGBA", (W * ss, 120 * ss), (0, 0, 0, 0))
    d_hi = ImageDraw.Draw(crest_hi)
    cx_hi = (W // 2) * ss
    d_hi.rounded_rectangle(
        [cx_hi - 165 * ss, 12 * ss, cx_hi + 165 * ss, 68 * ss],
        radius=12 * ss,
        fill=blend_rgb(paper_rgb, ink_rgb, 0.08) + (255,),
        outline=(196, 156, 86, 255),
        width=2 * ss,
    )
    d_hi.rounded_rectangle(
        [cx_hi - 159 * ss, 17 * ss, cx_hi + 159 * ss, 63 * ss],
        radius=9 * ss,
        outline=accent_rgb + (255,),
        width=1 * ss,
    )
    font_crest = load_font("Cinzel-Variable.ttf", 14 * ss)
    font_sub = load_font("EBGaramond-Italic-Variable.ttf", 14 * ss)
    draw_tracked_text(
        d_hi,
        (cx_hi, 23 * ss),
        "THEATRVM BRITANNICVM",
        font_crest,
        ink_rgb + (255,),
        tracking=1.8 * ss,
        anchor="ma",
    )
    draw_tracked_text(
        d_hi,
        (cx_hi, 42 * ss),
        "First Folio  ·  1623",
        font_sub,
        accent_rgb + (255,),
        tracking=0.8 * ss,
        anchor="ma",
    )
    crest_lo = crest_hi.resize((W, 120), Image.Resampling.LANCZOS)
    pros_im.alpha_composite(crest_lo, (0, 0))

    return pros_im


def build_act_drop_curtain(
    book: dict,
    mode: str,
    paper_rgb: tuple[int, int, int],
    ink_rgb: tuple[int, int, int],
    accent_rgb: tuple[int, int, int],
    rule_rgb: tuple[int, int, int],
) -> np.ndarray:
    """Build the painted Victorian Toy Theatre Crimson-and-Gold Act-Drop Curtain (`H x W x 3` uint8)
    for `mode in ("opening", "scene_change_1", "scene_change_2", "scene_change_3", "finale")`.
    """
    seed_map = {
        "opening": 505,
        "scene_change_1": 506,
        "scene_change_2": 507,
        "scene_change_3": 508,
        "finale": 509,
    }
    rng = np.random.default_rng(seed_map.get(mode, 505))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

    pleat_phase = (xx - W * 0.5) / 38.0 * math.pi * 2.0
    pleat_wave = (
        0.55 * np.sin(pleat_phase)
        + 0.28 * np.cos(pleat_phase * 0.5 + 0.6)
        + 0.17 * np.sin(pleat_phase * 1.7)
    )
    nx = (xx - W * 0.5) / 780.0
    ny = (yy - 520.0) / 460.0
    curtain_vig = np.clip(1.0 - 0.24 * (nx * nx + ny * ny * 0.7), 0.65, 1.05)

    crimson_hi = np.array([128.0, 28.0, 24.0], dtype=np.float32)
    crimson_lo = np.array([62.0, 12.0, 11.0], dtype=np.float32)
    w_pleat = np.clip(0.5 + 0.42 * pleat_wave, 0.0, 1.0)[:, :, None]
    curt_rgb = (
        crimson_lo[None, None, :] * (1.0 - w_pleat) + crimson_hi[None, None, :] * w_pleat
    ) * curtain_vig[:, :, None]

    damask = (
        np.sin(xx * 0.18 + yy * 0.18) * np.sin(xx * 0.18 - yy * 0.18) * 3.5
    )[:, :, None]
    grain = rng.normal(0.0, 1.5, size=(H, W, 1)).astype(np.float32)
    curt_rgb += damask + grain

    foot_glow = (
        np.clip((yy - 600.0) / 350.0, 0.0, 1.0) ** 1.6
        * np.exp(-(((xx - W * 0.5) / 620.0) ** 2))
    )[:, :, None]
    curt_rgb += np.array([240.0, 172.0, 84.0], dtype=np.float32)[None, None, :] * (
        0.18 * foot_glow
    )

    gold_rgb = np.array([210.0, 170.0, 96.0], dtype=np.float32)[None, None, :]
    border_x = np.exp(-(((xx - 215.0) / 3.5) ** 2)) + np.exp(
        -(((xx - (W - 215.0)) / 3.5) ** 2)
    )
    border_x2 = np.exp(-(((xx - 226.0) / 1.8) ** 2)) + np.exp(
        -(((xx - (W - 226.0)) / 1.8) ** 2)
    )
    b_w = np.clip(border_x * 0.75 + border_x2 * 0.45, 0.0, 1.0)[:, :, None]
    curt_rgb = curt_rgb * (1.0 - b_w) + gold_rgb * b_w

    curt_im = Image.fromarray(np.clip(curt_rgb, 0, 255).astype(np.uint8), mode="RGB").convert(
        "RGBA"
    )

    ss = 3
    ov_hi = Image.new("RGBA", (W * ss, H * ss), (0, 0, 0, 0))
    d_hi = ImageDraw.Draw(ov_hi)

    cx0, cy0, cx1, cy1 = 470, 225, W - 470, 775
    d_hi.rounded_rectangle(
        [(cx0 + 8) * ss, (cy0 + 10) * ss, (cx1 + 8) * ss, (cy1 + 10) * ss],
        radius=22 * ss,
        fill=(18, 6, 6, 135),
    )
    d_hi.rounded_rectangle(
        [cx0 * ss, cy0 * ss, cx1 * ss, cy1 * ss],
        radius=20 * ss,
        fill=blend_rgb(paper_rgb, ink_rgb, 0.04) + (255,),
        outline=(196, 154, 82, 255),
        width=4 * ss,
    )
    d_hi.rounded_rectangle(
        [(cx0 + 12) * ss, (cy0 + 12) * ss, (cx1 - 12) * ss, (cy1 - 12) * ss],
        radius=14 * ss,
        outline=accent_rgb + (255,),
        width=2 * ss,
    )
    d_hi.rounded_rectangle(
        [(cx0 + 18) * ss, (cy0 + 18) * ss, (cx1 - 18) * ss, (cy1 - 18) * ss],
        radius=10 * ss,
        outline=rule_rgb + (255,),
        width=1 * ss,
    )

    for px_c in (cx0 + 30, cx1 - 30):
        for py_c in (cy0 + 30, cy1 - 30):
            r_d = 5 * ss
            d_hi.polygon(
                [
                    (px_c * ss, py_c * ss - r_d),
                    (px_c * ss + r_d, py_c * ss),
                    (px_c * ss, py_c * ss + r_d),
                    (px_c * ss - r_d, py_c * ss),
                ],
                fill=accent_rgb + (255,),
            )

    mid_x = (W // 2) * ss
    font_kicker = load_font("Cinzel-Variable.ttf", 16 * ss)
    font_title = load_font("CormorantGaramond-Variable.ttf", 62 * ss)
    font_scene_big = load_font("Cinzel-Variable.ttf", 42 * ss)
    font_sub = load_font("EBGaramond-Italic-Variable.ttf", 29 * ss)
    font_meta = load_font("Cinzel-Variable.ttf", 15 * ss)
    font_quote = load_font("EBGaramond-Italic-Variable.ttf", 23 * ss)

    if mode in ("opening", "finale"):
        kicker = "WILLIAM SHAKESPEARE   ·   FIRST FOLIO EDITION, 1623"
        draw_tracked_text(
            d_hi,
            (mid_x, 280 * ss),
            kicker,
            font_kicker,
            accent_rgb + (255,),
            tracking=2.4 * ss,
            anchor="ma",
        )

        title_str = "THE TRAGEDIE OF MACBETH"
        draw_tracked_text(
            d_hi,
            (mid_x, 336 * ss),
            title_str,
            font_title,
            ink_rgb + (255,),
            tracking=1.2 * ss,
            anchor="ma",
        )

        ry = 432 * ss
        d_hi.line([(mid_x - 260 * ss, ry), (mid_x - 18 * ss, ry)], fill=rule_rgb + (255,), width=2 * ss)
        d_hi.line([(mid_x + 18 * ss, ry), (mid_x + 260 * ss, ry)], fill=rule_rgb + (255,), width=2 * ss)
        ds = 6 * ss
        d_hi.polygon(
            [(mid_x, ry - ds), (mid_x + ds, ry), (mid_x, ry + ds), (mid_x - ds, ry)],
            fill=accent_rgb + (255,),
        )

        if mode == "opening":
            sub_str = "Acts I & II  —  The Weird Sisters, Inverness & The Murder of Duncan"
            sub2_str = "A Desert Moor   ·   A Heath near Forres   ·   Macbeth’s Castle at Inverness"
            cast_hdr = "DRAMATIS PERSONAE UPON THE STAGE"
            cast_str = "The Weird Sisters   ·   Macbeth   ·   Lady Macbeth   ·   Banquo   ·   Ross"
        else:
            sub_str = "Explicit Actus Primus & Secundus  —  Midnight at Inverness"
            sub2_str = "“Wake Duncan with thy knocking! I would thou couldst!”"
            cast_hdr = "VICTORIAN PAPER TOY THEATRE EDITION"
            cast_str = "The Weird Sisters   ·   Macbeth   ·   Lady Macbeth   ·   Banquo   ·   Ross"

        w_s1 = font_sub.getlength(sub_str)
        d_hi.text(((W * ss - w_s1) / 2.0, 462 * ss), sub_str, font=font_sub, fill=ink_rgb + (255,))

        w_s2 = font_quote.getlength(sub2_str)
        d_hi.text(
            ((W * ss - w_s2) / 2.0, 512 * ss),
            sub2_str,
            font=font_quote,
            fill=hex_to_rgb(book["palette"]["muted"]) + (255,),
        )

        d_hi.line(
            [(mid_x - 180 * ss, 608 * ss), (mid_x + 180 * ss, 608 * ss)],
            fill=rule_rgb + (255,),
            width=1 * ss,
        )
        draw_tracked_text(
            d_hi,
            (mid_x, 634 * ss),
            cast_hdr,
            font_meta,
            accent_rgb + (255,),
            tracking=2.0 * ss,
            anchor="ma",
        )
        w_cast = font_quote.getlength(cast_str)
        d_hi.text(
            ((W * ss - w_cast) / 2.0, 668 * ss),
            cast_str,
            font=font_quote,
            fill=ink_rgb + (255,),
        )
    else:
        if mode == "scene_change_1":
            act_str = "ACT I   ·   SCENE III"
            loc_str = "A Heath near Forres"
            q_str = "“A drum, a drum! Macbeth doth come.”"
            cast_str = "THE THREE WEIRD SISTERS   ·   MACBETH   ·   BANQUO   ·   ROSS"
        elif mode == "scene_change_2":
            act_str = "ACT I   ·   SCENE V"
            loc_str = "Inverness. Macbeth’s Castle"
            q_str = "“Look like the innocent flower, but be the serpent under’t.”"
            cast_str = "LADY MACBETH   ·   MACBETH, THANE OF GLAMIS & CAWDOR"
        else:
            act_str = "ACT II   ·   SCENES I & II"
            loc_str = "Midnight at Inverness"
            q_str = "“Is this a dagger which I see before me, the handle toward my hand?”"
            cast_str = "MACBETH   ·   THE DAGGER OF THE MIND   ·   LADY MACBETH"

        draw_tracked_text(
            d_hi,
            (mid_x, 292 * ss),
            "THE TRAGEDIE OF MACBETH",
            font_kicker,
            accent_rgb + (255,),
            tracking=2.6 * ss,
            anchor="ma",
        )
        draw_tracked_text(
            d_hi,
            (mid_x, 355 * ss),
            act_str,
            font_scene_big,
            ink_rgb + (255,),
            tracking=2.2 * ss,
            anchor="ma",
        )

        ry = 438 * ss
        d_hi.line([(mid_x - 240 * ss, ry), (mid_x - 18 * ss, ry)], fill=rule_rgb + (255,), width=2 * ss)
        d_hi.line([(mid_x + 18 * ss, ry), (mid_x + 240 * ss, ry)], fill=rule_rgb + (255,), width=2 * ss)
        ds = 6 * ss
        d_hi.polygon(
            [(mid_x, ry - ds), (mid_x + ds, ry), (mid_x, ry + ds), (mid_x - ds, ry)],
            fill=accent_rgb + (255,),
        )

        w_loc = font_sub.getlength(loc_str)
        d_hi.text(
            ((W * ss - w_loc) / 2.0, 472 * ss),
            loc_str,
            font=font_sub,
            fill=ink_rgb + (255,),
        )

        w_q = font_quote.getlength(q_str)
        d_hi.text(
            ((W * ss - w_q) / 2.0, 535 * ss),
            q_str,
            font=font_quote,
            fill=hex_to_rgb(book["palette"]["muted"]) + (255,),
        )

        draw_tracked_text(
            d_hi,
            (mid_x, 646 * ss),
            cast_str,
            font_meta,
            accent_rgb + (255,),
            tracking=2.0 * ss,
            anchor="ma",
        )

    ov_lo = ov_hi.resize((W, H), Image.Resampling.LANCZOS)
    curt_im = Image.alpha_composite(curt_im, ov_lo)
    return np.array(curt_im.convert("RGB"), dtype=np.uint8)


def composite_act_drop_curtain(
    frame_rgb: np.ndarray,
    curtain_rgb: np.ndarray,
    curtain_drop: float,
) -> np.ndarray:
    """Composite Layer 4 (the painted crimson-and-gold Act-Drop Curtain) over `frame_rgb`
    (which contains Layers 0, 1, 2, and 3A), BEFORE Layer 3B (the outer proscenium arch and
    footlights) is composited on top.
    """
    if curtain_drop <= 0.001:
        return frame_rgb

    y_top = 74
    y_max_bot = TRACK_FRONT_Y + 12  # 958
    y_hem = int(round(y_top + (y_max_bot - y_top) * max(0.0, min(1.0, curtain_drop))))
    if y_hem <= y_top + 4:
        return frame_rgb

    out = frame_rgb.astype(np.float32).copy()

    shift_y = y_max_bot - y_hem
    curt_slice = curtain_rgb[shift_y : shift_y + y_hem, :, :].astype(np.float32)

    baton_h = min(22, y_hem - y_top)
    if baton_h >= 6:
        by = np.arange(baton_h, dtype=np.float32)[:, None]
        bx = np.arange(W, dtype=np.float32)[None, :]
        u_b = by / float(max(1, baton_h - 1))
        in_roller = u_b < 0.52
        roller_cyl = 0.65 + 0.45 * np.sin((u_b / 0.52) * math.pi)
        timber_col = np.array([76.0, 32.0, 22.0], dtype=np.float32)[None, None, :] * roller_cyl[:, :, None]
        fringe_wave = 0.72 + 0.28 * np.sin(bx * 0.48)
        gold_fringe = np.array([214.0, 172.0, 92.0], dtype=np.float32)[None, None, :] * fringe_wave[:, :, None]
        fringe_col = np.where(in_roller[:, :, None], timber_col, gold_fringe)
        fringe_col[-2:, :, :] *= 0.48
        curt_slice[y_hem - baton_h : y_hem, :, :] = fringe_col

    out[:y_hem, :, :] = curt_slice

    sh_h = min(56, H - y_hem)
    if sh_h > 2:
        sy = np.arange(sh_h, dtype=np.float32)[:, None, None]
        sh_mul = 1.0 - 0.58 * np.exp(-sy / 18.0)
        out[y_hem : y_hem + sh_h, :, :] *= sh_mul

    return np.clip(out, 0, 255).astype(np.uint8)


def prepare_scene_theatre_pack(book: dict, scene_idx: int) -> dict:
    """Prepare the full-screen 1920x1080 Toy Theatre assets for `scene_idx`:
    - `stage_bg_rgb`: Layer 0 (Deep Heath / Castle Backdrop) + Layer 1 (Grooved Stage Floor)
    - `scenic_wings_im`: Layer 3A (Foreground Cut-Paper Scenic Side-Wing Flats)
    - `layers`: Layer 2 (2K Die-Cut Cardstock Character Standees + Cast Shadows)
    """
    pal = book["palette"]
    paper_rgb = hex_to_rgb(pal["paper"])
    ink_rgb = hex_to_rgb(pal["ink"])
    rule_rgb = hex_to_rgb(pal["rule"])
    muted_rgb = hex_to_rgb(pal["muted"])

    sc = book["scenes"][scene_idx]
    bg_path = ROOT / sc.get("bg_file", sc["image_file"])
    popup_dir = ROOT / "illustrations" / "popup"
    popup_spread_idx = int(
        sc.get("popup_spread_idx", sc.get("popup_spread_num", scene_idx + 1) - 1)
    )

    raw_bg = Image.open(bg_path).convert("RGB")
    stage_bg_rgb, scenic_wings_im = build_stage_floor_and_backdrop(
        raw_bg, scene_idx, paper_rgb, ink_rgb
    )

    layout_cfg = MACBETH_STAGE_LAYOUT[popup_spread_idx]

    layers = []
    for idx_c, (col_name, cfg) in enumerate(layout_cfg.items()):
        standee_path = popup_dir / str(cfg["standee_file"])
        rgb_crop, mask_crop = extract_single_standee_2k(standee_path)
        is_floating = bool(cfg.get("is_floating", False))

        st_im = build_highres_diecut_standee(
            rgb_crop,
            mask_crop,
            target_h=int(cfg["target_h"]),
            max_w=int(cfg["max_w"]),
            paper_rgb=paper_rgb,
            ink_rgb=ink_rgb,
            seed=201 + scene_idx * 10 + idx_c,
            is_floating=is_floating,
        )
        if bool(cfg.get("pre_flip_x", False)):
            st_im = ImageOps.mirror(st_im)

        st_im_flip = ImageOps.mirror(st_im)
        tw, th = st_im.size
        x_center = int(cfg["x_center"])
        y_hinge = int(cfg["y_hinge"])
        track_y = int(cfg["track_y"])
        z_val = float(cfg["z"])
        home_wing = str(cfg["home_wing"])

        base_x = x_center - tw // 2
        base_y = y_hinge - th

        if home_wing == "left":
            dx_off = -float((base_x + tw) - (LEFT_WING_EDGE_X - 24))
        else:
            dx_off = float((RIGHT_WING_EDGE_X + 24) - base_x)

        alpha_ch = st_im.split()[3]
        blur_rad = int(round(9.0 + 10.0 * z_val))
        sh_pad = blur_rad * 2 + 10
        sh_canvas = Image.new("L", (tw + sh_pad * 2, th + sh_pad * 2), 0)
        sh_canvas.paste(alpha_ch, (sh_pad, sh_pad))
        sh_blurred = sh_canvas.filter(ImageFilter.GaussianBlur(radius=blur_rad))
        sh_arr_f = np.array(sh_blurred, dtype=np.float32) / 255.0
        sh_arr_f_flip = np.fliplr(sh_arr_f).copy()

        layers.append(
            {
                "col_name": col_name,
                "st_im": st_im,
                "st_im_flip": st_im_flip,
                "st_arr": np.array(st_im, dtype=np.float32),
                "st_arr_flip": np.array(st_im_flip, dtype=np.float32),
                "sh_arr_f": sh_arr_f,
                "sh_arr_f_flip": sh_arr_f_flip,
                "sh_pad": sh_pad,
                "base_x": base_x,
                "base_y": base_y,
                "tw": tw,
                "th": th,
                "y_hinge": y_hinge,
                "track_y": track_y,
                "z": z_val,
                "home_wing": home_wing,
                "dx_off": dx_off,
                "speaker": cfg["speaker"],
                "is_floating": is_floating,
            }
        )

    layers.sort(key=lambda d: d["z"])

    return {
        "scene_idx": scene_idx,
        "stage_bg_rgb": stage_bg_rgb,
        "scenic_wings_im": scenic_wings_im,
        "layers": layers,
        "paper_rgb": paper_rgb,
        "ink_rgb": ink_rgb,
        "rule_rgb": rule_rgb,
        "muted_rgb": muted_rgb,
        "frame_cache": {},
    }


def build_timeline_cues(book: dict) -> dict:
    """Extract all stage action, curtain, and spotlight timing cues dynamically from
    `audio/macbeth_manifest.json` (`scenes`, `turns`, `foley_events`).
    """
    turns = book["turns"]
    scenes = book["scenes"]

    title_end_sec = float(book.get("title_card_end_sec", 2.6))
    total_dur = float(book["total_duration_sec"])

    turn0 = turns[0]
    turn_enter_witches = next(
        (t for t in turns if t.get("stage_cue") == "enter_witches_sc1"), turn0
    )
    turn_exit_witches = next(
        (t for t in turns if t.get("stage_cue") == "exit_witches_sc1"), turns[10]
    )
    turn_enter_macbeth = next(
        (t for t in turns if t.get("stage_cue") == "enter_macbeth_banquo"), turns[13]
    )
    turn_vanish_witches = next(
        (t for t in turns if t.get("stage_cue") == "vanish_witches"), turns[25]
    )
    turn_enter_ross = next(
        (t for t in turns if t.get("stage_cue") == "enter_ross"), turns[28]
    )
    turn_enter_lady_sc3 = next(
        (t for t in turns if t.get("stage_cue") == "enter_lady_macbeth_sc3"), turns[34]
    )
    turn_enter_macbeth_sc3 = next(
        (t for t in turns if t.get("stage_cue") == "enter_macbeth_sc3"), turns[38]
    )
    turn_enter_lady_sc4 = next(
        (t for t in turns if t.get("stage_cue") == "enter_lady_macbeth_sc4"), turns[49]
    )
    turn_reenter_macbeth_daggers = next(
        (t for t in turns if t.get("stage_cue") == "reenter_macbeth_daggers"), turns[51]
    )

    scene_boundaries = []
    for idx in range(len(scenes) - 1):
        sc_end = float(scenes[idx]["end_sec"])
        next_turns = [t for t in turns if int(t["scene_idx"]) == idx + 1]
        next_start = float(next_turns[0]["start_sec"]) if next_turns else (sc_end + 2.8)
        scene_boundaries.append(
            {
                "from_scene": idx,
                "to_scene": idx + 1,
                "start_sec": sc_end,
                "end_sec": next_start,
                "mid_sec": 0.5 * (sc_end + next_start),
                "mode": f"scene_change_{idx + 1}",
            }
        )

    last_turn_end = float(turns[-1]["end_sec"])

    # Build merged speaker spotlight segments so spotlights transition smoothly over 0.35s
    # only when the active speaker changes and hold 100% constant during turns and brief pauses.
    raw_spk_turns = []
    for t in turns:
        if not t.get("is_dialogue", True) or t.get("is_stage_direction", False):
            continue
        spk = (
            "weird_sisters"
            if t.get("speaker_label") == "THE WEIRD SISTERS"
            else t["speaker_key"]
        )
        raw_spk_turns.append(
            {
                "scene_idx": int(t["scene_idx"]),
                "spk": spk,
                "start_sec": float(t["start_sec"]),
                "end_sec": float(t["end_sec"]),
            }
        )

    speaker_segments = []
    for item in raw_spk_turns:
        if (
            speaker_segments
            and speaker_segments[-1]["scene_idx"] == item["scene_idx"]
            and speaker_segments[-1]["spk"] == item["spk"]
            and (item["start_sec"] - speaker_segments[-1]["end_sec"]) < 4.5
        ):
            speaker_segments[-1]["end_sec"] = item["end_sec"]
        else:
            speaker_segments.append(dict(item))

    # Bridge brief inter-turn pauses (< 2.5s) within the same scene so spotlight handoffs
    # crossfade smoothly over 0.35s without dipping to black between lines.
    for i in range(len(speaker_segments) - 1):
        cur_seg = speaker_segments[i]
        nxt_seg = speaker_segments[i + 1]
        if (
            cur_seg["scene_idx"] == nxt_seg["scene_idx"]
            and (nxt_seg["start_sec"] - cur_seg["end_sec"]) < 2.5
        ):
            cur_seg["end_sec"] = nxt_seg["start_sec"]

    return {
        "title_end_sec": title_end_sec,
        "opening_curtain_up_end": title_end_sec + 1.50,
        "enter_witches_start": float(turn_enter_witches["start_sec"]) + 0.75,
        "enter_witches_end": float(turn_enter_witches["start_sec"]) + 2.95,
        "exit_witches_start": float(turn_exit_witches["start_sec"]),
        "exit_witches_end": float(turn_exit_witches["start_sec"]) + 2.00,
        "enter_macbeth_start": float(turn_enter_macbeth["start_sec"]),
        "enter_macbeth_end": float(turn_enter_macbeth["start_sec"]) + 2.30,
        "vanish_witches_start": float(turn_vanish_witches["start_sec"]) + 0.30,
        "vanish_witches_end": float(turn_vanish_witches["start_sec"]) + 2.50,
        "enter_ross_start": float(turn_enter_ross["start_sec"]),
        "enter_ross_end": float(turn_enter_ross["start_sec"]) + 2.10,
        "enter_lady_sc2_start": float(turn_enter_lady_sc3["start_sec"]),
        "enter_lady_sc2_end": float(turn_enter_lady_sc3["start_sec"]) + 2.20,
        "enter_macbeth_sc2_start": float(turn_enter_macbeth_sc3["start_sec"]),
        "enter_macbeth_sc2_end": float(turn_enter_macbeth_sc3["start_sec"]) + 2.10,
        "enter_lady_sc3_start": float(turn_enter_lady_sc4["start_sec"]),
        "enter_lady_sc3_end": float(turn_enter_lady_sc4["start_sec"]) + 2.20,
        "reenter_macbeth_daggers_start": float(turn_reenter_macbeth_daggers["start_sec"]),
        "reenter_macbeth_daggers_end": float(turn_reenter_macbeth_daggers["start_sec"]) + 2.20,
        "scene_boundaries": scene_boundaries,
        "closing_curtain_start": last_turn_end,
        "closing_curtain_down_end": min(total_dur - 0.65, last_turn_end + 1.50),
        "total_dur": total_dur,
        "turns": turns,
        "speaker_segments": speaker_segments,
        "foley_events": book.get("foley_events", []),
    }


def get_curtain_state(t_sec: float, cues: dict) -> tuple[float, str, int]:
    """Return `(curtain_drop, curtain_mode, active_scene_idx)` at `t_sec`:
    - `curtain_drop` in `[0.0, 1.0]` (`1.0` = fully lowered to stage floor, `0.0` = raised in fly-loft)
    - `curtain_mode` in `("opening", "scene_change_1", "scene_change_2", "scene_change_3", "finale")`
    - `active_scene_idx` in `(0, 1, 2, 3)` (switches cleanly at each scene-change midpoint while the
      Act-Drop Curtain is 100% down!).
    """
    title_end = cues["title_end_sec"]
    open_up_end = cues["opening_curtain_up_end"]
    close_start = cues["closing_curtain_start"]
    close_end = cues["closing_curtain_down_end"]

    active_scene_idx = 0
    for sb in cues["scene_boundaries"]:
        if t_sec >= sb["mid_sec"]:
            active_scene_idx = sb["to_scene"]

    # 1. Opening Act-Drop Curtain (0.00s .. 4.10s)
    if t_sec <= title_end:
        return 1.0, "opening", active_scene_idx
    if t_sec < open_up_end:
        u_up = smootherstep((t_sec - title_end) / max(0.1, open_up_end - title_end))
        return 1.0 - u_up, "opening", active_scene_idx

    # 2. Scene-Change Act-Drop Curtains (0->1, 1->2, 2->3)
    for sb in cues["scene_boundaries"]:
        sc_end = sb["start_sec"]
        sc_next = sb["end_sec"]
        mode = sb["mode"]
        if sc_end <= t_sec < sc_next:
            pause_dur = max(0.5, sc_next - sc_end)
            down_dur = pause_dur * (0.95 / 2.80)
            hold_dur = pause_dur * (0.90 / 2.80)
            t_down_end = sc_end + down_dur
            t_hold_end = t_down_end + hold_dur
            if t_sec < t_down_end:
                u_dn = smootherstep((t_sec - sc_end) / max(0.1, down_dur))
                return u_dn, mode, active_scene_idx
            if t_sec < t_hold_end:
                return 1.0, mode, active_scene_idx
            u_up = smootherstep((t_sec - t_hold_end) / max(0.1, sc_next - t_hold_end))
            return 1.0 - u_up, mode, active_scene_idx

    # 3. Closing Finale Act-Drop Curtain
    if t_sec >= close_start:
        if t_sec >= close_end:
            return 1.0, "finale", active_scene_idx
        u_close = smootherstep((t_sec - close_start) / max(0.1, close_end - close_start))
        return u_close, "finale", active_scene_idx

    return 0.0, "opening", active_scene_idx


def get_macbeth_stage_state(
    scene_idx: int, t_sec: float, cues: dict
) -> dict[str, tuple[float, float, float, float]]:
    """Return per-standee `(u_pos, alpha, u_flip, extra_dx)` for `scene_idx` at `t_sec`,
    strictly enforcing the Stage Facing & Dwell Heuristic (`MIN_FACING_DWELL_SEC >= 18.0s`).
    All stationary intervals have 0 pixel delta between frames.
    """
    if scene_idx == 0:
        t_in0 = cues["enter_witches_start"]
        t_in1 = cues["enter_witches_end"]
        t_out0 = cues["exit_witches_start"]
        t_out1 = cues["exit_witches_end"]

        if t_sec < t_in0:
            return {
                "left": (0.0, 0.0, 0.0, 0.0),
                "center": (0.0, 0.0, 0.0, 0.0),
                "right": (0.0, 0.0, 0.0, 0.0),
            }
        if t_sec < t_in1:
            span = max(0.5, t_in1 - t_in0)
            u_c = smootherstep((t_sec - t_in0) / (span * 0.92))
            u_l = smootherstep((t_sec - (t_in0 + span * 0.14)) / (span * 0.86))
            u_r = smootherstep((t_sec - (t_in0 + span * 0.06)) / (span * 0.90))
            return {
                "left": (u_l, 1.0, 0.0, 0.0),
                "center": (u_c, 1.0, 0.0, 0.0),
                "right": (u_r, 1.0, 0.0, 0.0),
            }
        if t_sec < t_out0:
            return {
                "left": (1.0, 1.0, 0.0, 0.0),
                "center": (1.0, 1.0, 0.0, 0.0),
                "right": (1.0, 1.0, 0.0, 0.0),
            }
        if t_sec < t_out1:
            span = max(0.3, t_out1 - t_out0)
            u_ex_l = 1.0 - smootherstep((t_sec - t_out0) / (span * 0.90))
            u_ex_c = 1.0 - smootherstep((t_sec - (t_out0 + span * 0.06)) / (span * 0.94))
            u_ex_r = 1.0 - smootherstep((t_sec - t_out0) / (span * 0.92))
            return {
                "left": (u_ex_l, 1.0, 0.0, 0.0),
                "center": (u_ex_c, 1.0, 0.0, 0.0),
                "right": (u_ex_r, 1.0, 0.0, 0.0),
            }
        return {
            "left": (0.0, 0.0, 0.0, 0.0),
            "center": (0.0, 0.0, 0.0, 0.0),
            "right": (0.0, 0.0, 0.0, 0.0),
        }

    if scene_idx == 1:
        t_mb0 = cues["enter_macbeth_start"]
        t_mb1 = cues["enter_macbeth_end"]
        t_van0 = cues["vanish_witches_start"]
        t_van1 = cues["vanish_witches_end"]
        t_ross0 = cues["enter_ross_start"]
        t_ross1 = cues["enter_ross_end"]

        if t_sec < 193.40:
            banquo_flip = 0.0
        elif t_sec < 193.82:
            banquo_flip = smootherstep((t_sec - 193.40) / 0.42)
        elif t_sec < 214.80:
            banquo_flip = 1.0
        elif t_sec < 215.22:
            banquo_flip = 1.0 - smootherstep((t_sec - 214.80) / 0.42)
        else:
            banquo_flip = 0.0

        step_in_u = smootherstep((t_sec - 193.20) / 1.45) if t_sec > 193.20 else 0.0
        step_out_u = smootherstep((t_sec - 214.10) / 1.80) if t_sec > 214.10 else 0.0
        converse_u = max(0.0, step_in_u - step_out_u)
        macbeth_extra_dx = 65.0 * converse_u
        banquo_extra_dx = 105.0 * converse_u

        if t_sec < t_van0:
            witches_state = (1.0, 1.0, 0.0, 0.0)
        elif t_sec < t_van1:
            u_van = smootherstep((t_sec - t_van0) / max(0.3, t_van1 - t_van0))
            a_van = 1.0 - smoothstep(max(0.0, (u_van - 0.25) / 0.75))
            witches_state = (1.0 - u_van, a_van, 0.0, 0.0)
        else:
            witches_state = (0.0, 0.0, 0.0, 0.0)

        if t_sec < t_ross0:
            ross_state = (0.0, 0.0, 0.0, 0.0)
        elif t_sec < t_ross1:
            u_ross = smootherstep((t_sec - t_ross0) / max(0.3, t_ross1 - t_ross0))
            ross_state = (u_ross, 1.0, 0.0, 0.0)
        else:
            ross_state = (1.0, 1.0, 0.0, 0.0)

        if t_sec < t_mb0:
            left_state = (0.0, 0.0, 0.0, 0.0)
            center_state = (0.0, 0.0, 0.0, 0.0)
        elif t_sec < t_mb1:
            span = max(0.4, t_mb1 - t_mb0)
            u_banquo = smootherstep((t_sec - t_mb0) / (span * 0.92))
            u_macbeth = smootherstep((t_sec - (t_mb0 + span * 0.12)) / (span * 0.88))
            center_state = (u_banquo, 1.0, banquo_flip, banquo_extra_dx)
            left_state = (u_macbeth, 1.0, 0.0, macbeth_extra_dx)
        else:
            left_state = (1.0, 1.0, 0.0, macbeth_extra_dx)
            center_state = (1.0, 1.0, banquo_flip, banquo_extra_dx)

        return {
            "left": left_state,
            "center": center_state,
            "right_witches": witches_state,
            "right_ross": ross_state,
        }

    if scene_idx == 2:
        t_lady0 = cues["enter_lady_sc2_start"]
        t_lady1 = cues["enter_lady_sc2_end"]
        t_mb0 = cues["enter_macbeth_sc2_start"]
        t_mb1 = cues["enter_macbeth_sc2_end"]

        if t_sec < t_lady0:
            lady_u = 0.0
            lady_alpha = 0.0
        elif t_sec < t_lady1:
            lady_u = smootherstep((t_sec - t_lady0) / max(0.5, t_lady1 - t_lady0))
            lady_alpha = 1.0
        else:
            lady_u = 1.0
            lady_alpha = 1.0

        if t_sec < t_mb0:
            glide_to_1300 = 0.0
            mb_u = 0.0
            mb_alpha = 0.0
        elif t_sec < t_mb1:
            glide_to_1300 = smootherstep((t_sec - t_mb0) / max(0.4, t_mb1 - t_mb0))
            mb_u = smootherstep((t_sec - t_mb0) / max(0.4, t_mb1 - t_mb0))
            mb_alpha = 1.0
        else:
            glide_to_1300 = 1.0
            mb_u = 1.0
            mb_alpha = 1.0

        lady_extra_dx = -240.0 * lady_u * (1.0 - glide_to_1300)
        return {
            "left": (mb_u, mb_alpha, 0.0, 0.0),
            "right": (lady_u, lady_alpha, 0.0, lady_extra_dx),
        }

    # Visual Scene 3: ACT II, SCENES I & II — Midnight at Inverness
    if t_sec < 541.80:
        mb_sol_state = (1.0, 1.0, 0.0, 0.0)
    elif t_sec < 544.00:
        u_exit_r = smootherstep((t_sec - 541.80) / (544.00 - 541.80))
        mb_sol_state = (1.0, 1.0, 0.0, 1260.0 * u_exit_r)
    else:
        mb_sol_state = (1.0, 0.0, 0.0, 1260.0)

    if t_sec < 461.50:
        dag_alpha = 0.0
    elif t_sec < 463.30:
        dag_alpha = 0.92 * smootherstep((t_sec - 461.50) / (463.30 - 461.50))
    elif t_sec < 539.80:
        dag_alpha = 0.92
    elif t_sec < 541.60:
        dag_alpha = 0.92 * (1.0 - smootherstep((t_sec - 539.80) / (541.60 - 539.80)))
    else:
        dag_alpha = 0.0
    dagger_state = (1.0, dag_alpha, 0.0, 0.0)

    t_l4_0 = cues["enter_lady_sc3_start"]
    t_l4_1 = cues["enter_lady_sc3_end"]
    if t_sec < t_l4_0:
        lady_s4_state = (0.0, 0.0, 0.0, 0.0)
    elif t_sec < t_l4_1:
        u_l4 = smootherstep((t_sec - t_l4_0) / max(0.4, t_l4_1 - t_l4_0))
        lady_s4_state = (u_l4, 1.0, 0.0, 0.0)
    else:
        lady_s4_state = (1.0, 1.0, 0.0, 0.0)

    t_mb4_0 = cues["reenter_macbeth_daggers_start"]
    t_mb4_1 = cues["reenter_macbeth_daggers_end"]
    if t_sec < t_mb4_0:
        mb_dag_state = (0.0, 0.0, 0.0, 0.0)
    elif t_sec < t_mb4_1:
        u_mb4 = smootherstep((t_sec - t_mb4_0) / max(0.4, t_mb4_1 - t_mb4_0))
        mb_dag_state = (u_mb4, 1.0, 0.0, 0.0)
    else:
        mb_dag_state = (1.0, 1.0, 0.0, 0.0)

    return {
        "macbeth_dagger_soliloquy": mb_sol_state,
        "floating_dagger": dagger_state,
        "lady_after_murder": lady_s4_state,
        "macbeth_bloody_daggers": mb_dag_state,
    }


def get_active_speaker_spotlights(t_sec: float, cues: dict) -> dict[str, float]:
    """Return smooth `[0.0, 1.0]` candle-footlight spotlight weights at `t_sec` for all speakers.
    Transitions smoothly over `0.35s` when the speaker changes and holds 100% constant during turns.
    """
    weights = {
        "first_witch": 0.0,
        "second_witch": 0.0,
        "third_witch": 0.0,
        "weird_sisters": 0.0,
        "macbeth": 0.0,
        "banquo": 0.0,
        "ross": 0.0,
        "lady_macbeth": 0.0,
    }
    trans = 0.35
    half_tr = trans * 0.5
    for seg in cues["speaker_segments"]:
        st = seg["start_sec"]
        en = seg["end_sec"]
        if (st - half_tr) <= t_sec <= (en + half_tr):
            w_in = smoothstep((t_sec - (st - half_tr)) / trans) if t_sec < (st + half_tr) else 1.0
            w_out = smoothstep(((en + half_tr) - t_sec) / trans) if t_sec > (en - half_tr) else 1.0
            w = w_in * w_out
            spk = seg["spk"]
            if spk in weights:
                weights[spk] = max(weights[spk], w)
    return weights


def render_toy_theatre_frame(
    t_sec: float,
    scene_packs: dict[int, dict],
    outer_proscenium_im: Image.Image,
    curtains: dict[str, np.ndarray],
    cues: dict,
) -> np.ndarray:
    """Composite all layers of the Full-Screen 1920x1080 Victorian Paper Toy Theatre at `t_sec`.
    Stationary dialogue frames are 100% temporally rock-steady (0 pixel delta between frames).
    """
    curtain_drop, curtain_mode, s_idx = get_curtain_state(t_sec, cues)
    pack = scene_packs[s_idx]

    if curtain_drop >= 0.999:
        curt_key = ("curtain_full", curtain_mode)
        if curt_key in pack["frame_cache"]:
            return pack["frame_cache"][curt_key]
        stage_plus_curt = composite_act_drop_curtain(
            pack["stage_bg_rgb"], curtains[curtain_mode], 1.0
        )
        comp_im = Image.fromarray(stage_plus_curt, mode="RGB").convert("RGBA")
        comp_im.alpha_composite(outer_proscenium_im)
        res_curt = np.array(comp_im.convert("RGB"), dtype=np.uint8)
        pack["frame_cache"][curt_key] = res_curt
        return res_curt

    layer_states = get_macbeth_stage_state(s_idx, t_sec, cues)
    spot_w = get_active_speaker_spotlights(t_sec, cues)

    # Check if all layers are in a cacheable stationary state (not mid-slide or mid-flip)
    is_cacheable = curtain_drop <= 0.001
    for st_tuple in layer_states.values():
        u_p, a_m, u_f, ex_dx = st_tuple
        if (0.002 < u_p < 0.998) or (0.002 < u_f < 0.998) or (0.005 < a_m < 0.915):
            is_cacheable = False
            break

    cache_key = (
        tuple(
            (
                col,
                round(layer_states[col][0], 3),
                round(layer_states[col][1], 2),
                round(layer_states[col][2], 2),
                round(layer_states[col][3], 0),
            )
            for col in sorted(layer_states.keys())
        ),
        tuple((k, round(spot_w[k], 2)) for k in sorted(spot_w.keys())),
    )

    if is_cacheable and cache_key in pack["frame_cache"]:
        return pack["frame_cache"][cache_key]

    stage_arr = pack["stage_bg_rgb"].astype(np.float32).copy()

    # --- Layer 2: Render Slider Push-Strips, Cast Shadows, and Large Die-Cut Characters ---
    for layer in pack["layers"]:
        col_name = layer["col_name"]
        u_pos, alpha_mul, u_flip, extra_dx = layer_states[col_name]
        if alpha_mul <= 0.003 or u_pos <= 0.001:
            continue

        is_floating = layer.get("is_floating", False)
        dx_px = layer["dx_off"] * (1.0 - u_pos) + extra_dx
        cur_x0 = int(round(layer["base_x"] + dx_px))
        cur_y0 = int(round(layer["base_y"]))
        tw, th = layer["tw"], layer["th"]
        cur_x1 = cur_x0 + tw
        cur_y1 = cur_y0 + th

        if cur_x1 <= 110 or cur_x0 >= W - 110:
            continue

        if is_floating:
            # Spectral Dagger in Scene 3: NO floor push-strip and NO dark floor/backdrop shadow!
            # Cast a steady ghostly golden-amber aura glow behind the hovering blade!
            gx0 = max(120, cur_x0 - 70)
            gx1 = min(W - 120, cur_x1 + 70)
            gy0 = max(100, cur_y0 - 70)
            gy1 = min(STAGE_FLOOR_Y, cur_y1 + 70)
            if gx1 > gx0 and gy1 > gy0:
                dag_cx = cur_x0 + tw * 0.5
                dag_cy = cur_y0 + th * 0.5
                gy_d = (np.arange(gy0, gy1, dtype=np.float32)[:, None] - dag_cy) / 115.0
                gx_d = (np.arange(gx0, gx1, dtype=np.float32)[None, :] - dag_cx) / 95.0
                aura = (
                    np.exp(-(gx_d * gx_d + gy_d * gy_d))
                    * (0.28 * alpha_mul)
                )
                amber_vec = np.array([255.0, 204.0, 98.0], dtype=np.float32)[
                    None, None, :
                ]
                stage_arr[gy0:gy1, gx0:gx1] = np.clip(
                    stage_arr[gy0:gy1, gx0:gx1] + amber_vec * aura[:, :, None],
                    0.0,
                    255.0,
                )

            st_arr = layer["st_arr"].copy()
            # Bright golden-amber self-illumination on the spectral dagger
            st_arr[:, :, 0] = np.clip(st_arr[:, :, 0] * 1.08, 0.0, 255.0)
            st_arr[:, :, 1] = np.clip(st_arr[:, :, 1] * 1.04, 0.0, 255.0)
            cx0, cy0 = max(0, cur_x0), max(0, cur_y0)
            cx1, cy1 = min(W, cur_x1), min(H, cur_y1)
            if cx1 > cx0 and cy1 > cy0:
                sub_st = st_arr[
                    cy0 - cur_y0 : cy1 - cur_y0, cx0 - cur_x0 : cx1 - cur_x0
                ]
                a_st = (sub_st[:, :, 3:4] / 255.0) * alpha_mul
                stage_arr[cy0:cy1, cx0:cx1] = (
                    stage_arr[cy0:cy1, cx0:cx1] * (1.0 - a_st)
                    + sub_st[:, :, :3] * a_st
                )
            continue

        # Determine speaker spotlight weight (`sp_val` in [0, 1]) for this figure
        spk = layer["speaker"]
        sub_spot_x_rel: float | None = None
        if spk == "weird_sisters":
            w_all = spot_w["weird_sisters"]
            w_1 = spot_w["first_witch"]
            w_2 = spot_w["second_witch"]
            w_3 = spot_w["third_witch"]
            sp_val = max(w_all, w_1, w_2, w_3)
            if sp_val > w_all and sp_val > 0.05:
                if w_1 >= w_2 and w_1 >= w_3:
                    sub_spot_x_rel = 0.20
                elif w_2 >= w_1 and w_2 >= w_3:
                    sub_spot_x_rel = 0.50
                else:
                    sub_spot_x_rel = 0.80
        else:
            sp_val = spot_w.get(spk, 0.0)

        # 2A. Draw the tarnished-brass & cardstock horizontal slider push-strip in the stage slot!
        track_y = layer["track_y"]
        tab_cx = cur_x0 + tw // 2
        # If Macbeth is exiting rightward into Duncan's chamber (extra_dx > 350), attach rod to right wing
        rod_wing = "right" if extra_dx > 350.0 else layer["home_wing"]
        if rod_wing == "left":
            rod_x0, rod_x1 = 130, min(W - 130, tab_cx + 36)
        else:
            rod_x0, rod_x1 = max(130, tab_cx - 36), W - 130

        if rod_x1 > rod_x0:
            stage_arr[track_y : track_y + 2, rod_x0:rod_x1] = np.array(
                [214.0, 182.0, 114.0], dtype=np.float32
            )
            stage_arr[track_y + 2 : track_y + 4, rod_x0:rod_x1] = np.array(
                [148.0, 118.0, 68.0], dtype=np.float32
            )
            stage_arr[track_y + 4 : track_y + 5, rod_x0:rod_x1] = np.array(
                [52.0, 38.0, 22.0], dtype=np.float32
            )

        c_x0 = max(120, tab_cx - 48)
        c_x1 = min(W - 120, tab_cx + 48)
        if c_x1 > c_x0:
            stage_arr[track_y - 2 : track_y + 1, c_x0:c_x1] = np.array(
                [228.0, 196.0, 128.0], dtype=np.float32
            )
            stage_arr[track_y + 1 : track_y + 5, c_x0:c_x1] = np.array(
                [164.0, 130.0, 74.0], dtype=np.float32
            )

        # 2B. Warm candle-footlight pool on the stage floor & backdrop around the active speaker
        if sp_val > 0.02:
            spot_cx = (
                cur_x0 + tw * sub_spot_x_rel
                if sub_spot_x_rel is not None
                else cur_x0 + tw * 0.5
            )
            sx0 = max(120, int(spot_cx - 290))
            sx1 = min(W - 120, int(spot_cx + 290))
            sy0 = max(180, cur_y0 - 40)
            sy1 = min(APRON_TOP_Y, cur_y1 + 45)
            if sx1 > sx0 and sy1 > sy0:
                gy_s = (
                    np.arange(sy0, sy1, dtype=np.float32)[:, None] - (cur_y1 - 60.0)
                ) / 340.0
                gx_s = (
                    np.arange(sx0, sx1, dtype=np.float32)[None, :] - spot_cx
                ) / 165.0
                pool = np.exp(-(gx_s * gx_s + gy_s * gy_s * 0.65)) * (
                    0.14 * sp_val * alpha_mul
                )
                candle_vec = np.array([255.0, 196.0, 108.0], dtype=np.float32)[
                    None, None, :
                ]
                stage_arr[sy0:sy1, sx0:sx1] = np.clip(
                    stage_arr[sy0:sy1, sx0:sx1] + candle_vec * pool[:, :, None],
                    0.0,
                    255.0,
                )

        # 2C. Cast looming backdrop shadow behind the standee (deepened when spotlighted!)
        sh_pad = layer["sh_pad"]
        sh_ox = int(round((cur_x0 + tw * 0.5 - W * 0.5) * 0.045))
        sh_oy = -int(round(8.0 + 10.0 * sp_val))
        sh_x0 = cur_x0 - sh_pad + sh_ox
        sh_y0 = cur_y0 - sh_pad + sh_oy
        sh_src = layer["sh_arr_f_flip"] if u_flip >= 0.5 else layer["sh_arr_f"]
        sh_h, sh_w = sh_src.shape
        sh_x1 = sh_x0 + sh_w
        sh_y1 = sh_y0 + sh_h

        ix0, iy0 = max(0, sh_x0), max(0, sh_y0)
        ix1, jy1 = min(W, sh_x1), min(STAGE_FLOOR_Y + 28, sh_y1)
        if ix1 > ix0 and jy1 > iy0:
            sub_sh = sh_src[
                iy0 - sh_y0 : jy1 - sh_y0, ix0 - sh_x0 : ix1 - sh_x0
            ]
            sh_strength = (0.34 + 0.18 * sp_val) * alpha_mul
            stage_arr[iy0:jy1, ix0:ix1] *= (1.0 - sub_sh * sh_strength)[:, :, None]

        # 2D. Composite the Die-Cut Cardstock Character Standee with Active Speaker Footlight Boost!
        if 0.002 < u_flip < 0.998:
            scale_x = max(0.18, abs(math.cos(u_flip * math.pi)))
            sw = max(12, int(round(tw * scale_x)))
            src_im = layer["st_im"] if u_flip < 0.5 else layer["st_im_flip"]
            sw_im = src_im.resize((sw, th), Image.Resampling.LANCZOS)
            canvas_im = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
            canvas_im.paste(sw_im, ((tw - sw) // 2, 0))
            st_arr = np.array(canvas_im, dtype=np.float32)
        elif u_flip >= 0.5:
            st_arr = layer["st_arr_flip"].copy()
        else:
            st_arr = layer["st_arr"].copy()

        if 0.005 < u_pos < 0.995:
            st_arr[:, :, :3] *= 0.97

        base_dim = 0.92
        yy_fig = np.linspace(0.0, 1.0, th, dtype=np.float32)[:, None]
        foot_vert = 0.85 + 0.30 * (yy_fig**0.8)

        if sub_spot_x_rel is not None:
            xx_fig = np.linspace(0.0, 1.0, tw, dtype=np.float32)[None, :]
            horiz_beam = np.exp(-(((xx_fig - sub_spot_x_rel) / 0.24) ** 2))
            local_sp = sp_val * (0.25 + 0.75 * horiz_beam)
        else:
            local_sp = np.full((1, tw), sp_val, dtype=np.float32)

        bright_map = base_dim + (1.08 - base_dim) * local_sp * foot_vert
        r_mult = bright_map * (1.0 + 0.05 * local_sp)
        g_mult = bright_map * (1.0 + 0.02 * local_sp)
        b_mult = bright_map * (1.0 - 0.04 * local_sp)

        st_arr[:, :, 0] = np.clip(st_arr[:, :, 0] * r_mult, 0.0, 255.0)
        st_arr[:, :, 1] = np.clip(st_arr[:, :, 1] * g_mult, 0.0, 255.0)
        st_arr[:, :, 2] = np.clip(st_arr[:, :, 2] * b_mult, 0.0, 255.0)

        cx0, cy0 = max(0, cur_x0), max(0, cur_y0)
        cx1, cy1 = min(W, cur_x1), min(H, cur_y1)
        if cx1 > cx0 and cy1 > cy0:
            sub_st = st_arr[cy0 - cur_y0 : cy1 - cur_y0, cx0 - cur_x0 : cx1 - cur_x0]
            a_st = (sub_st[:, :, 3:4] / 255.0) * alpha_mul
            stage_arr[cy0:cy1, cx0:cx1] = (
                stage_arr[cy0:cy1, cx0:cx1] * (1.0 - a_st) + sub_st[:, :, :3] * a_st
            )

        # Swirling moorland mist when the Witches vanish in Scene 1!
        if s_idx == 1 and col_name == "right_witches" and 0.02 < alpha_mul < 0.98:
            mist_w = 4.0 * alpha_mul * (1.0 - alpha_mul)
            mx0, mx1 = max(120, cur_x0 - 40), min(W - 120, cur_x1 + 40)
            my0, my1 = max(220, cur_y0 + 40), min(STAGE_FLOOR_Y + 35, cur_y1 + 10)
            if mx1 > mx0 and my1 > my0:
                my_g = np.linspace(-1.0, 1.0, my1 - my0, dtype=np.float32)[:, None]
                mx_g = np.linspace(-1.0, 1.0, mx1 - mx0, dtype=np.float32)[None, :]
                wisp = (
                    np.exp(-(mx_g * mx_g * 1.6 + my_g * my_g * 1.4))
                    * (
                        0.6
                        + 0.4
                        * np.sin(mx_g * 9.0 + t_sec * 4.0)
                        * np.cos(my_g * 7.0 - t_sec * 3.0)
                    )
                    * (0.38 * mist_w)
                )
                mist_col = np.array([188.0, 196.0, 192.0], dtype=np.float32)[
                    None, None, :
                ]
                stage_arr[my0:my1, mx0:mx1] = (
                    stage_arr[my0:my1, mx0:mx1] * (1.0 - wisp[:, :, None])
                    + mist_col * wisp[:, :, None]
                )

    # --- Layer 3A: Composite Foreground Cut-Paper Scenic Side-Wing Flats IN FRONT of Layer 2! ---
    comp_im = Image.fromarray(np.clip(stage_arr, 0, 255).astype(np.uint8), mode="RGB").convert(
        "RGBA"
    )
    comp_im.alpha_composite(pack["scenic_wings_im"])
    stage_with_wings_rgb = np.array(comp_im.convert("RGB"), dtype=np.uint8)

    # --- Layer 4: Composite Painted Crimson-and-Gold Act-Drop Curtain (if partially/fully lowered) ---
    if curtain_drop > 0.001:
        stage_with_wings_rgb = composite_act_drop_curtain(
            stage_with_wings_rgb, curtains[curtain_mode], curtain_drop
        )

    # --- Layer 3B: Composite Outer Proscenium Pilasters, Top Swagged Valance & Footlight Apron ---
    final_im = Image.fromarray(stage_with_wings_rgb, mode="RGB").convert("RGBA")
    final_im.alpha_composite(outer_proscenium_im)
    final_rgb = np.array(final_im.convert("RGB"), dtype=np.uint8)

    if is_cacheable and len(pack["frame_cache"]) < 400:
        pack["frame_cache"][cache_key] = final_rgb

    return final_rgb


def save_proscenium_wings_asset(
    scene_packs: dict[int, dict], outer_proscenium_im: Image.Image
) -> None:
    """Save the combined 3-layer cut-paper Victorian Toy Theatre Proscenium & Side Wings plate
    to `illustrations/popup/07_macbeth_proscenium_wings.jpg` for inspection and archival.
    """
    PROSCENIUM_ASSET_PATH.parent.mkdir(parents=True, exist_ok=True)
    bg = Image.new("RGBA", (W, H), (24, 20, 18, 255))
    bg.alpha_composite(scene_packs[0]["scenic_wings_im"])
    bg.alpha_composite(outer_proscenium_im)
    bg.convert("RGB").save(PROSCENIUM_ASSET_PATH, quality=95)
    print(f"[ASSET OK] Saved {PROSCENIUM_ASSET_PATH} ({W}x{H})")


def render_macbeth_preview_frames(
    book: dict,
    scene_packs: dict[int, dict],
    outer_proscenium_im: Image.Image,
    curtains: dict[str, np.ndarray],
    cues: dict,
) -> None:
    """Render static PNG keyframes to `video/previews/` showing the Opening Act-Drop Curtain
    and all 4 Toy Theatre visual scenes.
    """
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    book_id = book["id"]

    title_frame = render_toy_theatre_frame(
        1.2, scene_packs, outer_proscenium_im, curtains, cues
    )
    Image.fromarray(title_frame).save(PREVIEW_DIR / f"{book_id}_preview_title.png")

    preview_times = [
        25.0,   # Scene 0: Three Witches in coven circle, Second Witch steady
        230.0,  # Scene 1: Ross hailing Macbeth & Banquo on the heath near Forres
        415.0,  # Scene 2: Macbeth & Lady Macbeth face-to-face in the Great Hall of Inverness
        610.0,  # Scene 3: Lady Macbeth & Macbeth with two bloody daggers face-to-face at midnight
    ]
    for idx, t_sample in enumerate(preview_times, 1):
        frame = render_toy_theatre_frame(
            t_sample, scene_packs, outer_proscenium_im, curtains, cues
        )
        Image.fromarray(frame).save(
            PREVIEW_DIR / f"{book_id}_preview_scene_{idx}.png"
        )
    print(f"[PREVIEW] Saved 5 full-screen Toy Theatre preview PNGs in {PREVIEW_DIR}")


_MP_STATE: dict = {}


def _render_macbeth_rep_frame(frame_num: int) -> tuple[int, bytes]:
    t_sec = frame_num / float(FPS)
    frame = render_toy_theatre_frame(
        t_sec,
        _MP_STATE["scene_packs"],
        _MP_STATE["outer_proscenium_im"],
        _MP_STATE["curtains"],
        _MP_STATE["cues"],
    )
    fade_in_dur = 0.50
    outro_fade_dur = 0.55
    total_dur = _MP_STATE["total_dur"]
    theatre_dark = _MP_STATE["theatre_dark"]

    if t_sec < fade_in_dur:
        a = smoothstep(t_sec / fade_in_dur)
        frame = (
            theatre_dark * (1.0 - a) + frame.astype(np.float32) * a
        ).astype(np.uint8)
    elif (total_dur - t_sec) < outro_fade_dur:
        a = smoothstep(max(0.0, (total_dur - t_sec) / outro_fade_dur))
        frame = (
            theatre_dark * (1.0 - a) + frame.astype(np.float32) * a
        ).astype(np.uint8)

    return frame_num, frame.tobytes()


def _frame_dedup_key(frame_num: int, cues: dict, total_dur: float) -> tuple:
    t_sec = frame_num / float(FPS)
    fade_in_dur = 0.50
    outro_fade_dur = 0.55
    if t_sec < fade_in_dur or (total_dur - t_sec) < outro_fade_dur:
        return ("uncached", frame_num)

    curtain_drop, curtain_mode, s_idx = get_curtain_state(t_sec, cues)
    if curtain_drop >= 0.999:
        return ("curtain_full", s_idx, curtain_mode)

    layer_states = get_macbeth_stage_state(s_idx, t_sec, cues)
    spot_w = get_active_speaker_spotlights(t_sec, cues)

    is_cacheable = curtain_drop <= 0.001
    for st_tuple in layer_states.values():
        u_p, a_m, u_f, _ = st_tuple
        if (0.002 < u_p < 0.998) or (0.002 < u_f < 0.998) or (0.005 < a_m < 0.915):
            is_cacheable = False
            break

    if not is_cacheable:
        return ("uncached", frame_num)

    cache_key = (
        tuple(
            (
                col,
                round(layer_states[col][0], 3),
                round(layer_states[col][1], 2),
                round(layer_states[col][2], 2),
                round(layer_states[col][3], 0),
            )
            for col in sorted(layer_states.keys())
        ),
        tuple((k, round(spot_w[k], 2)) for k in sorted(spot_w.keys())),
    )
    return ("stage", s_idx, cache_key)


def render_macbeth_video(
    book: dict,
    scene_packs: dict[int, dict],
    outer_proscenium_im: Image.Image,
    curtains: dict[str, np.ndarray],
    cues: dict,
    out_mp4_override: Path | None = None,
) -> Path:
    """Render the full 1920x1080 24fps MP4 for Book VII: The Tragedy of Macbeth (`< 24.5 MB`)."""
    import multiprocessing as mp

    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    book_id = book["id"]
    out_mp4 = (
        out_mp4_override
        if out_mp4_override is not None
        else (VIDEO_DIR / f"{book_id}.mp4")
    )
    master_wav = ROOT / book["master_wav"]

    total_dur = cues["total_dur"]
    total_frames = int(round(total_dur * FPS))

    frame_rep_map: list[int] = [0] * total_frames
    key_to_rep: dict[tuple, int] = {}
    for fn in range(total_frames):
        k = _frame_dedup_key(fn, cues, total_dur)
        rep = key_to_rep.get(k)
        if rep is None:
            rep = fn
            key_to_rep[k] = rep
        frame_rep_map[fn] = rep

    unique_reps = sorted(set(frame_rep_map))
    print(
        f"[RENDER] Pre-computing {len(unique_reps)} unique frames out of {total_frames} total frames across 16 workers..."
    )

    _MP_STATE.update(
        {
            "scene_packs": scene_packs,
            "outer_proscenium_im": outer_proscenium_im,
            "curtains": curtains,
            "cues": cues,
            "total_dur": total_dur,
            "theatre_dark": np.full((H, W, 3), (14, 10, 9), dtype=np.float32),
        }
    )

    rep_bytes: dict[int, bytes] = {}
    ctx = mp.get_context("fork")
    with ctx.Pool(processes=16) as pool:
        for done_idx, (rep_fn, raw_b) in enumerate(
            pool.imap_unordered(_render_macbeth_rep_frame, unique_reps, chunksize=4), 1
        ):
            rep_bytes[rep_fn] = raw_b
            if done_idx % 200 == 0 or done_idx == len(unique_reps):
                print(f"  [POOL] Rendered {done_idx}/{len(unique_reps)} unique frames")

    cmd = [
        "ffmpeg",
        "-y",
        "-loglevel",
        "info",
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
        "fast",
        "-crf",
        "25.5",
        "-g",
        "2400",
        "-bf",
        "8",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "136k",
        "-ar",
        "48000",
        "-shortest",
        "-movflags",
        "+faststart",
        str(out_mp4),
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    assert proc.stdin is not None
    for fn in range(total_frames):
        proc.stdin.write(rep_bytes[frame_rep_map[fn]])

    proc.stdin.close()
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg failed for {book_id} with exit code {rc}")
    size_mb = out_mp4.stat().st_size / (1024 * 1024)
    print(f"[VIDEO OK] {out_mp4.name} ({size_mb:.2f} MB, {total_dur:.2f}s)")
    return out_mp4


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--preview-only",
        action="store_true",
        help="Only render static PNG preview frames",
    )
    args = parser.parse_args()

    manifest = json.loads(MANIFEST_PATH.read_text())
    book = manifest["books"][0] if "books" in manifest else manifest

    pal = book["palette"]
    paper_rgb = hex_to_rgb(pal["paper"])
    ink_rgb = hex_to_rgb(pal["ink"])
    accent_rgb = hex_to_rgb(pal["accent"])
    rule_rgb = hex_to_rgb(pal["rule"])

    scene_packs = {
        s_idx: prepare_scene_theatre_pack(book, s_idx)
        for s_idx in range(len(book["scenes"]))
    }
    outer_proscenium_im = build_outer_proscenium_and_footlights(
        paper_rgb, ink_rgb, accent_rgb
    )
    save_proscenium_wings_asset(scene_packs, outer_proscenium_im)

    curtains = {
        mode: build_act_drop_curtain(
            book, mode, paper_rgb, ink_rgb, accent_rgb, rule_rgb
        )
        for mode in (
            "opening",
            "scene_change_1",
            "scene_change_2",
            "scene_change_3",
            "finale",
        )
    }
    cues = build_timeline_cues(book)

    render_macbeth_preview_frames(
        book, scene_packs, outer_proscenium_im, curtains, cues
    )
    if not args.preview_only:
        render_macbeth_video(
            book, scene_packs, outer_proscenium_im, curtains, cues
        )


if __name__ == "__main__":
    main()
