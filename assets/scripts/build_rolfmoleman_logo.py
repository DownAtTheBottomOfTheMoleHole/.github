#!/usr/bin/env python3
"""
Build the rolfmoleman crest logo from a generated source illustration.

Pipeline
--------
1. Load source PNG (square, painted mole emblem from Pollinations/Flux).
2. Apply METAL_RAMP brand tinting from heavy_metal_icons (luminance-stretched).
3. Mask out the rectangular dark background, keeping only the circular crest +
   chains + skulls + scroll banner via a soft circular alpha mask, producing a
   transparent PNG.
4. Wipe any gibberish text on the scroll banner with a brand-tinted rectangle.
5. Overlay clean "ROLFMOLEMAN" text in Herculanum (Trajan-ish heavy serif) in
   cream-gold #f0d070 with a near-black drop shadow.
6. Save 1024 / 512 / 128 px versions.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SCRIPT_DIR = Path(__file__).resolve().parent
ASSETS = SCRIPT_DIR.parent
ROOT = ASSETS.parent

sys.path.insert(0, str(SCRIPT_DIR))
from heavy_metal_icons import (  # noqa: E402
    METAL_RAMP,
    apply_metal_ramp,
    apply_vignette,
    rgb_to_luminance,
)

SOURCE = ASSETS / "rolfmoleman_source_v3.png"
OUT_1024 = ASSETS / "rolfmoleman_logo.png"
OUT_512 = ASSETS / "rolfmoleman_logo_512.png"
OUT_128 = ASSETS / "rolfmoleman_logo_128.png"

CREAM_GOLD = (240, 208, 112)
DEEP_SHADOW = (10, 6, 4)
FONT_PATH = "/System/Library/Fonts/Supplemental/Herculanum.ttf"


def metal_tint(rgb: np.ndarray, gamma: float = 0.85) -> np.ndarray:
    """Stretch luminance and remap through METAL_RAMP."""
    lum = rgb_to_luminance(rgb)
    lo, hi = np.percentile(lum, [2, 98])
    if hi <= lo:
        stretched = np.full_like(lum, 0.5)
    else:
        stretched = np.clip((lum - lo) / (hi - lo), 0, 1) * 0.95 + 0.025
    if gamma != 1.0:
        stretched = np.power(stretched, gamma)
    return apply_metal_ramp(stretched)


def circular_alpha(size: int, feather_px: int = 14) -> np.ndarray:
    """Soft-edged circular alpha mask, white inside, transparent outside."""
    yy, xx = np.ogrid[:size, :size]
    cx = cy = size / 2.0
    radius = size / 2.0 - 4
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    alpha = np.clip((radius - dist) / feather_px, 0, 1)
    return (alpha * 255).astype(np.uint8)


def find_banner_box(size: int) -> tuple[int, int, int, int]:
    """Approximate scroll-banner rectangle in source coordinates."""
    w = size
    left = int(w * 0.16)
    right = int(w * 0.84)
    top = int(w * 0.78)
    bottom = int(w * 0.92)
    return left, top, right, bottom


def paint_banner(img: Image.Image) -> Image.Image:
    """Paint a clean weathered parchment band over the gibberish."""
    arr = np.array(img.convert("RGBA"))
    h, w = arr.shape[:2]
    left, top, right, bottom = find_banner_box(w)

    band_h = bottom - top
    band_w = right - left

    # Vertical gradient: lighter top, darker bottom — like a curling scroll.
    grad = np.linspace(0.92, 0.55, band_h)[:, None]
    base = np.array([[200, 138, 24]], dtype=np.float32)  # warm gold base
    band_rgb = (grad[..., None] * base).astype(np.uint8)
    band_rgb = np.repeat(band_rgb, band_w, axis=1)

    # Subtle noise for parchment texture.
    rng = np.random.default_rng(7)
    noise = rng.normal(0, 8, band_rgb.shape).astype(np.int16)
    band_rgb = np.clip(band_rgb.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    arr[top:bottom, left:right, :3] = band_rgb
    return Image.fromarray(arr)


def fit_font(text: str, max_width: int, max_height: int) -> ImageFont.FreeTypeFont:
    size = max_height
    while size > 8:
        font = ImageFont.truetype(FONT_PATH, size=size)
        bbox = font.getbbox(text)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        if tw <= max_width and th <= max_height:
            return font
        size -= 2
    return ImageFont.truetype(FONT_PATH, size=12)


def overlay_text(img: Image.Image, text: str = "ROLFMOLEMAN") -> Image.Image:
    img = img.convert("RGBA")
    w, _ = img.size
    left, top, right, bottom = find_banner_box(w)
    band_w = right - left
    band_h = bottom - top

    target_w = int(band_w * 0.86)
    target_h = int(band_h * 0.62)
    font = fit_font(text, target_w, target_h)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    cx = (left + right) // 2
    cy = (top + bottom) // 2
    x = cx - tw // 2 - bbox[0]
    y = cy - th // 2 - bbox[1]

    shadow_offset = max(2, w // 400)
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=DEEP_SHADOW + (220,))
    draw.text((x, y), text, font=font, fill=CREAM_GOLD + (255,))

    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=0.4))
    return Image.alpha_composite(img, overlay)


def build() -> Image.Image:
    if not SOURCE.exists():
        raise FileNotFoundError(f"missing source: {SOURCE}")

    src = Image.open(SOURCE).convert("RGB")
    if src.size[0] != src.size[1]:
        side = min(src.size)
        left = (src.size[0] - side) // 2
        top = (src.size[1] - side) // 2
        src = src.crop((left, top, left + side, top + side))

    rgb = np.array(src)
    tinted = metal_tint(rgb, gamma=0.82)
    vignetted = apply_vignette(tinted, strength=0.35)

    img = Image.fromarray(vignetted).convert("RGBA")
    img = paint_banner(img)
    img = overlay_text(img, "ROLFMOLEMAN")

    # Apply soft circular crest mask -> transparent background outside.
    alpha = circular_alpha(img.size[0], feather_px=18)
    arr = np.array(img)
    arr[..., 3] = alpha
    return Image.fromarray(arr, mode="RGBA")


def main() -> None:
    img = build()
    for path, size in [(OUT_1024, 1024), (OUT_512, 512), (OUT_128, 128)]:
        out = img if img.size[0] == size else img.resize((size, size), Image.Resampling.LANCZOS)
        out.save(path)
        print(f"  ✓ {path.relative_to(ROOT)} ({size}x{size})")


if __name__ == "__main__":
    main()
