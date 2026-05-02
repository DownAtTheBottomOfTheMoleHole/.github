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


def _edge_mask(h: int, w: int, thickness: int = 1) -> np.ndarray:
    mask = np.zeros((h, w), dtype=bool)
    mask[:thickness, :] = True
    mask[-thickness:, :] = True
    mask[:, :thickness] = True
    mask[:, -thickness:] = True
    return mask


def _adaptive_tolerance_from_edges(img_array: np.ndarray, fallback: float | None) -> float:
    """Estimate a flood-fill tolerance from border colour variation.

    Uses edge pixels to infer the background colour spread, then adds a margin
    so JPEG artifacts and mild gradients are included.
    """
    h, w = img_array.shape[:2]
    thickness = max(1, min(h, w) // 64)
    edge = _edge_mask(h, w, thickness=thickness)
    edge_pixels = img_array[edge, :3].astype(float)

    if edge_pixels.size == 0:
        return fallback if fallback is not None else 35.0

    bg_color = np.median(edge_pixels, axis=0)
    dists = np.linalg.norm(edge_pixels - bg_color, axis=1)
    base = float(np.percentile(dists, 95) + 8.0)

    if fallback is None:
        return max(25.0, min(base, 120.0))

    return max(float(fallback), min(base, 120.0))


def flood_fill_background(img_array: np.ndarray, tolerance: float | None) -> np.ndarray:
    """Return a boolean foreground mask from adaptive edge-seeded flood fill.

    Seeds flood fill from all border pixels that are within *tolerance* of
    the inferred border background colour. This is more robust than corner-only
    seeding for JPEG artifacts, anti-aliased edges, and non-uniform corners.

    Returns a boolean array of shape (H, W): True = foreground.
    """
    h, w = img_array.shape[:2]
    bg_mask = np.zeros((h, w), dtype=bool)  # True = background

    effective_tolerance = _adaptive_tolerance_from_edges(img_array, tolerance)

    thickness = max(1, min(h, w) // 64)
    edge = _edge_mask(h, w, thickness=thickness)
    edge_pixels = img_array[edge, :3].astype(float)
    bg_color = np.median(edge_pixels, axis=0)

    seeds = np.argwhere(edge)
    queue = deque()
    for sy, sx in seeds:
        dist_bg = np.linalg.norm(img_array[sy, sx, :3].astype(float) - bg_color)
        if dist_bg <= effective_tolerance:
            bg_mask[sy, sx] = True
            queue.append((sy, sx))

    while queue:
        y, x = queue.popleft()
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not bg_mask[ny, nx]:
                neighbor = img_array[ny, nx, :3].astype(float)
                dist_bg = np.linalg.norm(neighbor - bg_color)
                if dist_bg <= effective_tolerance:
                    bg_mask[ny, nx] = True
                    queue.append((ny, nx))

    return ~bg_mask


def remove_small_components(mask: np.ndarray, min_pixels: int) -> np.ndarray:
    """Remove tiny disconnected foreground islands from a boolean mask."""
    h, w = mask.shape
    visited = np.zeros((h, w), dtype=bool)
    out = np.zeros((h, w), dtype=bool)
    largest_component = []

    for y in range(h):
        for x in range(w):
            if not mask[y, x] or visited[y, x]:
                continue

            queue = deque([(y, x)])
            visited[y, x] = True
            component = []

            while queue:
                cy, cx = queue.popleft()
                component.append((cy, cx))
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w:
                        if mask[ny, nx] and not visited[ny, nx]:
                            visited[ny, nx] = True
                            queue.append((ny, nx))

            if len(component) >= min_pixels:
                for py, px in component:
                    out[py, px] = True

            if len(component) > len(largest_component):
                largest_component = component

    if not np.any(out) and largest_component:
        for py, px in largest_component:
            out[py, px] = True

    return out


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


def process_image(src_path: str, tolerance: float | None):
    """Load source image and compute stretched luminance + fg mask.

    The image is NOT padded here — flood-fill must seed from the original
    image corners so it correctly identifies the background colour.
    Letterboxing happens after compositing, in main().
    """
    img_rgba = Image.open(src_path).convert("RGBA")
    rgba_array = np.array(img_rgba)
    img_array = rgba_array[..., :3]

    alpha = rgba_array[..., 3].astype(np.float32) / 255.0
    use_alpha_mask = 0.01 < np.mean(alpha > 0.02) < 0.995 and np.std(alpha) > 0.02

    if use_alpha_mask:
        fg_mask = alpha > 0.08
    else:
        fg_mask = flood_fill_background(img_array, tolerance)

    min_pixels = max(8, int(img_array.shape[0] * img_array.shape[1] * 0.0005))
    fg_mask = remove_small_components(fg_mask, min_pixels=min_pixels)
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
        tolerance = TOLERANCES[key] if key else None

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
        print("  ✓ saved")

    print("Done.")


if __name__ == "__main__":
    main()
