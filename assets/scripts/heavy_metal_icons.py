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

YARN_CIRCLE_BLACK = (8, 5, 4)
YARN_CAT_BROWN = (90, 52, 8)
YARN_OUTLINE_GOLD = (224, 176, 64)

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


def largest_component(mask: np.ndarray) -> np.ndarray:
    """Return only the largest connected component from a boolean mask."""
    h, w = mask.shape
    visited = np.zeros((h, w), dtype=bool)
    best = []

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
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        queue.append((ny, nx))

            if len(component) > len(best):
                best = component

    out = np.zeros((h, w), dtype=bool)
    for y, x in best:
        out[y, x] = True
    return out


def dilate_mask(mask: np.ndarray, radius: int = 2) -> np.ndarray:
    """Dilate a boolean mask using PIL MaxFilter."""
    if radius <= 0:
        return mask.copy()

    size = radius * 2 + 1
    mask_img = Image.fromarray((mask.astype(np.uint8) * 255))
    dilated = mask_img.filter(ImageFilter.MaxFilter(size=size))
    return np.array(dilated) > 0


def flood_within_mask(fill_allowed: np.ndarray, seed_mask: np.ndarray) -> np.ndarray:
    """Flood-fill inside fill_allowed starting from seed_mask pixels."""
    h, w = fill_allowed.shape
    out = np.zeros((h, w), dtype=bool)
    queue = deque()

    ys, xs = np.where(seed_mask & fill_allowed)
    for y, x in zip(ys, xs):
        out[y, x] = True
        queue.append((y, x))

    while queue:
        y, x = queue.popleft()
        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and fill_allowed[ny, nx] and not out[ny, nx]:
                out[ny, nx] = True
                queue.append((ny, nx))

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
    if img.mode == "RGBA":
        fill = bg_color if len(bg_color) == 4 else (bg_color[0], bg_color[1], bg_color[2], 255)
    else:
        fill = bg_color[:3]

    square = Image.new(img.mode, (side, side), fill)
    offset_x = (side - w) // 2
    offset_y = (side - h) // 2
    square.paste(img, (offset_x, offset_y))
    return square


def stylize_yarn_transparent(source_rgb: np.ndarray, fg_mask_soft: np.ndarray) -> Image.Image:
    """Create transparent Yarn icon: black circle, gold outline, brown cat fill."""
    rgb = source_rgb.astype(np.float32) / 255.0
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]

    # The Yarn source has a blue circle and near-white cat outline.
    blue_score = b - (0.55 * r + 0.45 * g)
    circle_candidates = (blue_score > 0.10) & (b > 0.35)
    circle_mask = largest_component(circle_candidates)

    ys, xs = np.where(circle_mask)
    if len(xs) == 0:
        h, w = source_rgb.shape[:2]
        return Image.new("RGBA", (w, h), (0, 0, 0, 0))

    cx = float(np.mean(xs))
    cy = float(np.mean(ys))
    area = float(len(xs))
    radius = max(12.0, np.sqrt(area / np.pi))

    h, w = source_rgb.shape[:2]
    yy, xx = np.ogrid[:h, :w]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)

    # Geometric circle cleans JPEG stair-steps while preserving the original size.
    circle_geom = dist <= (radius * 1.01)
    ring_mask = (dist >= (radius - 2.2)) & (dist <= (radius + 1.0))

    lum = 0.299 * r + 0.587 * g + 0.114 * b
    chroma = np.max(rgb, axis=2) - np.min(rgb, axis=2)
    white_mask = (lum > 0.72) & (chroma < 0.28)

    # Keep cat outline detection away from the outer circle border artifacts.
    center_region = dist <= (radius * 0.88)
    cat_outline = white_mask & center_region
    cat_outline = dilate_mask(cat_outline, radius=1)
    cat_outline = remove_small_components(cat_outline, min_pixels=max(20, (h * w) // 700))

    barrier = dilate_mask(cat_outline, radius=2)
    fillable = (dist <= (radius - 3.0)) & ~barrier

    # Start from ring-adjacent pixels to get the "outside of cat" region.
    near_edge = (dist >= (radius - 8.0)) & fillable
    outside_region = flood_within_mask(fillable, near_edge)
    cat_fill_mask = fillable & ~outside_region

    # Fallback in case outline gaps make cat fill disappear.
    if np.count_nonzero(cat_fill_mask) < max(20, circle_mask.size // 2000):
        cat_fill_mask = fillable & (lum < 0.56)

    outline_mask = ring_mask | cat_outline

    out = np.zeros((h, w, 4), dtype=np.uint8)

    out[circle_geom, :3] = np.array(YARN_CIRCLE_BLACK, dtype=np.uint8)
    out[cat_fill_mask, :3] = np.array(YARN_CAT_BROWN, dtype=np.uint8)
    out[outline_mask, :3] = np.array(YARN_OUTLINE_GOLD, dtype=np.uint8)

    edge_soft = np.clip(radius + 0.75 - dist, 0.0, 1.0)
    alpha = np.maximum(edge_soft, (cat_fill_mask | outline_mask).astype(np.float32))
    alpha = np.maximum(alpha, 0.2 * fg_mask_soft.astype(np.float32) * circle_geom.astype(np.float32))
    out[..., 3] = (np.clip(alpha, 0.0, 1.0) * 255.0).astype(np.uint8)

    return Image.fromarray(out, mode="RGBA")


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

    return stretched, fg_mask_smooth, img_array.shape[:2], img_array


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

        stretched_lum, fg_mask, orig_size, source_rgb = result

        if gamma != 1.0:
            stretched_lum = np.power(stretched_lum, gamma)

        is_yarn_v2 = "yarn_source_v2" in src_path.lower()
        if is_yarn_v2:
            final_img = stylize_yarn_transparent(source_rgb, fg_mask)
            final_img = letterbox_to_square(final_img, bg_color=(0, 0, 0, 0))
        else:
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
