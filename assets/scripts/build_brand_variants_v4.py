#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SCRIPT_DIR = Path(__file__).resolve().parent
ASSETS = SCRIPT_DIR.parent

# Inputs
ROLF_SRC = ASSETS / "rolfmoleman_banner_v2.png"
SNAGGLE_BANNER_SRC = ASSETS / "snagglemole_banner.png"
SNAGGLE_LOGO2_SRC = ASSETS / "snagglemole_logo_2.png"

# Outputs (new versions only)
ROLF_OUT = ASSETS / "rolfmoleman_banner_v4.png"
SNAGGLE_BANNER_OUT = ASSETS / "snagglemole_banner_v4.png"
SNAGGLE_LOGO2_OUT = ASSETS / "snagglemole_logo_2_v4.png"

OUT_BANNER_W, OUT_BANNER_H = 1983, 793

GOLD = (236, 205, 122)
GOLD_DARK = (128, 83, 22)
NEAR_BLACK = (12, 8, 6)

FONT_CANDIDATES = [
    str(ASSETS / "fonts" / "Cinzel-Bold.ttf"),
    str(ASSETS / "fonts" / "MetalMania-Regular.ttf"),
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
]


def load_font(text: str, max_w: int, max_h: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        try:
            size = max_h
            while size >= 12:
                font = ImageFont.truetype(path, size)
                l, t, r, b = font.getbbox(text)
                if (r - l) <= max_w and (b - t) <= max_h:
                    return font
                size -= 2
        except OSError:
            continue
    return ImageFont.load_default()


def apply_brand_grade(img: Image.Image, vignette_strength: float = 0.25) -> Image.Image:
    arr = np.array(img.convert("RGB")).astype(np.float32)

    # Warm bronze/gold grade for consistency across assets
    arr[..., 0] *= 1.04
    arr[..., 1] *= 0.99
    arr[..., 2] *= 0.92

    # Contrast lift with slight toe protection in shadows
    arr = ((arr - 128.0) * 1.08) + 128.0
    arr = np.clip(arr, 0, 255)

    h, w = arr.shape[:2]
    yy = np.linspace(-1, 1, h)[:, None]
    xx = np.linspace(-1, 1, w)[None, :]
    mask = 1.0 - vignette_strength * np.clip(xx**2 + yy**2, 0, 1)
    arr[..., :3] *= mask[..., None]

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def draw_clean_rolf_text(img: Image.Image) -> Image.Image:
    # Works on resized rolf source where the original ribbon sits near the lower third.
    work = img.convert("RGBA")
    draw = ImageDraw.Draw(work, "RGBA")
    iw, ih = work.size

    cx = iw // 2
    cy = int(ih * 0.835)
    rw = int(iw * 0.43)
    rh = int(ih * 0.11)

    x1 = cx - rw // 2
    x2 = cx + rw // 2
    y1 = cy - rh // 2
    y2 = cy + rh // 2

    # Sample nearby ribbon color, then darken slightly
    arr = np.array(work.convert("RGB"))
    sy1 = max(0, y1 - rh // 2)
    sy2 = max(sy1 + 1, y1)
    region = arr[sy1:sy2, max(0, x1):min(iw, x2)].reshape(-1, 3)
    if len(region):
        base = tuple(int(np.median(region[:, i])) for i in range(3))
    else:
        base = (72, 44, 16)
    fill = (max(0, int(base[0] * 0.85)), max(0, int(base[1] * 0.85)), max(0, int(base[2] * 0.85)), 235)

    # Keep the geometry close to the native curved ribbon.
    draw.rounded_rectangle([x1, y1, x2, y2], radius=max(10, rh // 4), fill=fill, outline=GOLD_DARK + (220,), width=max(2, rh // 14))
    draw.line([(x1 + 8, y1 + 6), (x2 - 8, y1 + 6)], fill=GOLD + (150,), width=2)
    draw.line([(x1 + 8, y2 - 6), (x2 - 8, y2 - 6)], fill=GOLD + (150,), width=2)

    text = "ROLFMOLEMAN"
    font = load_font(text, int(rw * 0.82), int(rh * 0.62))
    l, t, r, b = font.getbbox(text)
    tw, th = r - l, b - t
    tx = cx - tw // 2 - l
    ty = cy - th // 2 - t

    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (2, 2)]:
        draw.text((tx + dx, ty + dy), text, font=font, fill=NEAR_BLACK + (220,))
    draw.text((tx, ty), text, font=font, fill=GOLD + (255,))

    return work.convert("RGB")


def build_rolf_banner() -> None:
    img = Image.open(ROLF_SRC).convert("RGB")
    img = img.resize((OUT_BANNER_W, OUT_BANNER_H), Image.Resampling.LANCZOS)
    img = apply_brand_grade(img, vignette_strength=0.28)
    img = draw_clean_rolf_text(img)
    img.save(ROLF_OUT, optimize=True)
    print(f"wrote {ROLF_OUT.name} ({OUT_BANNER_W}x{OUT_BANNER_H})")


def build_snaggle_banner() -> None:
    img = Image.open(SNAGGLE_BANNER_SRC).convert("RGB")
    img = img.resize((OUT_BANNER_W, OUT_BANNER_H), Image.Resampling.LANCZOS)
    img = apply_brand_grade(img, vignette_strength=0.22)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.1, percent=120, threshold=3))
    img.save(SNAGGLE_BANNER_OUT, optimize=True)
    print(f"wrote {SNAGGLE_BANNER_OUT.name} ({OUT_BANNER_W}x{OUT_BANNER_H})")


def build_snaggle_logo2() -> None:
    img = Image.open(SNAGGLE_LOGO2_SRC).convert("RGB")
    iw, ih = img.size
    img = apply_brand_grade(img, vignette_strength=0.18)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.0, percent=115, threshold=2))
    img.save(SNAGGLE_LOGO2_OUT, optimize=True)
    print(f"wrote {SNAGGLE_LOGO2_OUT.name} ({iw}x{ih})")


if __name__ == "__main__":
    build_rolf_banner()
    build_snaggle_banner()
    build_snaggle_logo2()
    print("done")
