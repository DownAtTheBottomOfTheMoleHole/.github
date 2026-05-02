#!/usr/bin/env python3
"""
Heavy Metal Icon Generator
==========================
Applies the DownAtTheBottomOfTheMoleHole "heavy metal mole" brand treatment
to source PNG icons.

Algorithm
---------
1. BFS flood-fill from all four corners to isolate the connected background
   region without touching light-coloured foreground content (e.g. an alpaca
   body that is also light/white).
2. Gaussian-blur the mask edges for a soft compositing transition.
3. Stretch foreground luminance across the full brand colour ramp
   (near-black → warm gold) with per-source gamma control.
4. Composite the metal-tinted foreground over the brand near-black background.
5. Apply a subtle radial vignette.
6. Resize to each target size with Lanczos resampling.

Requirements
------------
    pip install Pillow numpy

Usage
-----
Place source PNGs at the paths listed in JOBS (or update the paths), then:

    python3 assets/scripts/heavy_metal_icons.py

Brand palette
-------------
Sampled from snagglemole_logo_white_square.png — 8-stop ramp, near-black warm
(#0a0604) through bronze/aged metal to cream-gold highlight (#f0d070).
"""

from PIL import Image, ImageFilter
import numpy as np
from collections import deque

# ---------------------------------------------------------------------------
# Brand constants
# ---------------------------------------------------------------------------

NEAR_BLACK = (10, 6, 4)  # background fill — #0a0604

METAL_RAMP = [
    (0.00, (10,   6,   4)),   # near-black warm
    (0.18, (22,  16,  10)),   # very dark earth
    (0.35, (46,  28,   6)),   # dark earth
    (0.52, (90,  52,   8)),   # dark bronze
    (0.68, (158,  96,  16)),  # bronze / aged metal
    (0.82, (200, 138,  24)),  # warm gold
    (0.92, (224, 176,  64)),  # bright gold
    (1.00, (240, 208, 112)),  # cream-gold highlight
]

# ---------------------------------------------------------------------------
# Jobs — (source_path, destination_path, target_size, gamma)
#
# gamma < 1.0 pushes midtones brighter (toward gold).
# Adjust per source image:
#   - megalinter alpaca source (light-grey bg, tolerance 30): gamma 0.85
#   - yarn source (white bg, tolerance 25):                   gamma 0.50
# ---------------------------------------------------------------------------

JOBS = [
    (
        "/tmp/megalinter_source.png",
        "/Users/carldawson/repos/downatthebottomofthemolehole/megalinter-ado/.assets/extension-icon.png",
        (512, 512),
        0.85,
    ),
    (
        "/tmp/megalinter_source.png",
        "/Users/carldawson/repos/downatthebottomofthemolehole/megalinter-ado/megalinter/icon.png",
        (128, 128),
        0.85,
    ),
    (
        "/tmp/yarn_source_v2.jpg",
        "/Users/carldawson/repos/downatthebottomofthemolehole/yarn-ado/Extension/extension-icon.png",
        (512, 512),
        0.70,
    ),
    (
        "/tmp/yarn_source_v2.jpg",
        "/Users/carldawson/repos/downatthebottomofthemolehole/yarn-ado/Tasks/Yarn/icon.png",
        (128, 128),
        0.70,
    ),
    (
        "/tmp/yarn_source_v2.jpg",
        "/Users/carldawson/repos/downatthebottomofthemolehole/yarn-ado/Tasks/YarnInstaller/icon.png",
        (128, 128),
        0.70,
    ),
]

# Flood-fill tolerance per source filename substring
TOLERANCES = {
    "megalinter": 30,
    "yarn_source_v2": 70,  # blue circular bg — JPEG corners vary from 221→255 (dist ~59), blue is ~220 away so 70 is safe
    "yarn": 25,
}


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


def flood_fill_background(img_array: np.ndarray, tolerance: float) -> np.ndarray:
    """Return a boolean foreground mask.

    BFS from all four corners removes the connected background region.
    The seed colour is taken from each corner pixel. Pixels within
    *tolerance* (Euclidean RGB distance from the seed) that are reachable
    from a corner without crossing a foreground boundary are marked as
    background.

    Returns a boolean array of shape (H, W): True = foreground.
    """
    h, w = img_array.shape[:2]
    mask = np.zeros((h, w), dtype=bool)  # True = background (will be inverted)
    corners = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]

    for cy, cx in corners:
        if mask[cy, cx]:
            continue
        seed_color = img_array[cy, cx, :3].astype(float)
        queue = deque([(cy, cx)])
        mask[cy, cx] = True

        while queue:
            y, x = queue.popleft()
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny, nx = y + dy, x + dx
                if 0 <= ny < h and 0 <= nx < w and not mask[ny, nx]:
                    dist = np.linalg.norm(
                        img_array[ny, nx, :3].astype(float) - seed_color
                    )
                    if dist <= tolerance:
                        mask[ny, nx] = True
                        queue.append((ny, nx))

    return ~mask  # invert: True = foreground


def gaussian_blur_mask(mask: np.ndarray, sigma: float = 1.5) -> np.ndarray:
    """Return a soft float mask [0, 1] by Gaussian-blurring a boolean mask."""
    mask_img = Image.fromarray((mask.astype(np.uint8) * 255))
    blurred = mask_img.filter(ImageFilter.GaussianBlur(radius=sigma))
    return np.array(blurred).astype(float) / 255.0


def rgb_to_luminance(rgb: np.ndarray) -> np.ndarray:
    return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]


def apply_metal_ramp(luminance: np.ndarray) -> np.ndarray:
    """Map a [0, 1] luminance array to RGB using METAL_RAMP."""
    result = np.zeros((*luminance.shape, 3))
    for i in range(len(METAL_RAMP) - 1):
        t0, c0 = METAL_RAMP[i]
        t1, c1 = METAL_RAMP[i + 1]
        band = (luminance >= t0) & (luminance < t1)
        if np.any(band):
            local_t = (luminance[band] - t0) / (t1 - t0)
            for ch in range(3):
                result[band, ch] = c0[ch] + local_t * (c1[ch] - c0[ch])

    top = luminance >= METAL_RAMP[-1][0]
    if np.any(top):
        result[top] = METAL_RAMP[-1][1]

    return result.astype(np.uint8)


def apply_vignette(img_array: np.ndarray, strength: float = 0.3) -> np.ndarray:
    """Darken corners with a radial vignette."""
    h, w = img_array.shape[:2]
    y, x = np.ogrid[:h, :w]
    cy, cx = h / 2, w / 2
    max_dist = np.sqrt(cy**2 + cx**2)
    dist = np.sqrt((y - cy) ** 2 + (x - cx) ** 2)
    vignette = 1 - strength * (dist / max_dist) ** 2
    vignette = np.clip(vignette, 0, 1)
    return (img_array * vignette[..., np.newaxis]).astype(np.uint8)


def letterbox_to_square(img: Image.Image, bg_color: tuple = NEAR_BLACK) -> Image.Image:
    """Pad *img* to a square canvas filled with *bg_color*.

    The original image is centred; aspect ratio is preserved.
    """
    w, h = img.size
    side = max(w, h)
    square = Image.new("RGB", (side, side), bg_color)
    offset_x = (side - w) // 2
    offset_y = (side - h) // 2
    square.paste(img, (offset_x, offset_y))
    return square


def process_image(src_path: str, tolerance: float):
    """Load source image and compute stretched luminance + fg mask.

    The image is NOT padded here — flood-fill must seed from the original
    image corners so it correctly identifies the background colour.
    Letterboxing happens after compositing, in main().
    """
    img = Image.open(src_path).convert("RGB")
    img_array = np.array(img)

    fg_mask = flood_fill_background(img_array, tolerance)
    fg_mask_smooth = gaussian_blur_mask(fg_mask, sigma=1.5)

    fg_pixels = img_array[fg_mask]
    if len(fg_pixels) == 0:
        return None

    fg_lum = rgb_to_luminance(fg_pixels)
    lum_min, lum_max = fg_lum.min(), fg_lum.max()

    full_lum = rgb_to_luminance(img_array)
    if lum_max > lum_min:
        stretched = (full_lum - lum_min) / (lum_max - lum_min) * 0.95 + 0.05
    else:
        stretched = np.full_like(full_lum, 0.5)
    stretched = np.clip(stretched, 0, 1)

    return stretched, fg_mask_smooth, img_array.shape[:2]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    import os

    for src_path, dst_path, target_size, gamma in JOBS:
        key = next(
            (k for k in TOLERANCES if k in src_path.lower()),
            None,
        )
        tolerance = TOLERANCES[key] if key else 25

        label = f"{src_path.split('/')[-1]} → .../{'/'.join(dst_path.split('/')[-3:])}"
        print(f"  Processing {label} {target_size}")

        result = process_image(src_path, tolerance)
        if result is None:
            print(f"  FAILED: no foreground pixels found in {src_path}")
            continue

        stretched_lum, fg_mask, orig_size = result

        if gamma != 1.0:
            stretched_lum = np.power(stretched_lum, gamma)

        metal_colored = apply_metal_ramp(stretched_lum)

        background = np.full((*orig_size, 3), NEAR_BLACK, dtype=np.uint8)
        alpha_3d = fg_mask[..., np.newaxis]
        composited = (
            metal_colored * alpha_3d + background * (1 - alpha_3d)
        ).astype(np.uint8)

        vignetted = apply_vignette(composited, strength=0.3)

        final_img = Image.fromarray(vignetted)
        # Pad to square preserving aspect ratio, then resize to target.
        final_img = letterbox_to_square(final_img)
        if final_img.size != target_size:
            final_img = final_img.resize(target_size, Image.Resampling.LANCZOS)

        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        final_img.save(dst_path)
        print(f"  ✓ saved")

    print("Done.")


if __name__ == "__main__":
    main()
