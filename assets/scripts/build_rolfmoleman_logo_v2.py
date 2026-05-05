#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from heavy_metal_icons import apply_metal_ramp, apply_vignette, rgb_to_luminance

SCRIPT_DIR = Path(__file__).resolve().parent
ASSETS = SCRIPT_DIR.parent

SOURCE = ASSETS / "rolfmoleman_source_v5a.png"
OUT_1024 = ASSETS / "rolfmoleman_logo.png"
OUT_512 = ASSETS / "rolfmoleman_logo_512.png"
OUT_128 = ASSETS / "rolfmoleman_logo_128.png"

FONT_PATHS = [
    "/System/Library/Fonts/Supplemental/Herculanum.ttf",
    "/System/Library/Fonts/Supplemental/Copperplate.ttc",
    "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf",
]

GOLD = (240, 208, 112)
DARK = (22, 16, 10)


def metal_tint(rgb: np.ndarray, gamma: float = 0.8) -> np.ndarray:
    lum = rgb_to_luminance(rgb)
    lo, hi = np.percentile(lum, [2, 98])
    if hi <= lo:
        stretched = np.full_like(lum, 0.5)
    else:
        stretched = np.clip((lum - lo) / (hi - lo), 0, 1)
    stretched = np.power(stretched, gamma)
    return apply_metal_ramp(stretched)


def circular_alpha(size: int, feather: int = 18) -> np.ndarray:
    yy, xx = np.ogrid[:size, :size]
    c = size / 2
    radius = size / 2 - 4
    dist = np.sqrt((xx - c) ** 2 + (yy - c) ** 2)
    alpha = np.clip((radius - dist) / feather, 0, 1)
    return (alpha * 255).astype(np.uint8)


def pick_font(max_w: int, max_h: int, text: str) -> ImageFont.FreeTypeFont:
    for path in FONT_PATHS:
        try:
            size = max_h
            while size > 12:
                font = ImageFont.truetype(path, size)
                l, t, r, b = font.getbbox(text)
                w, h = r - l, b - t
                if w <= max_w and h <= max_h:
                    return font
                size -= 2
        except OSError:
            continue
    return ImageFont.load_default()


def overlay_text(img: Image.Image, text: str = "ROLFMOLEMAN") -> Image.Image:
    img = img.convert("RGBA")
    w, h = img.size

    # Banner location tuned to v5a curved scroll.
    left = int(w * 0.22)
    right = int(w * 0.78)
    top = int(h * 0.78)
    bottom = int(h * 0.90)

    font = pick_font(int((right - left) * 0.96), int((bottom - top) * 0.70), text)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    l, t, r, b = font.getbbox(text)
    tw, th = r - l, b - t
    x = (left + right - tw) // 2 - l
    y = (top + bottom - th) // 2 - t

    # Shadow + subtle stroke for legibility on noisy parchment.
    offs = max(1, w // 420)
    for dx, dy in [(-offs, 0), (offs, 0), (0, -offs), (0, offs)]:
        draw.text((x + dx, y + dy), text, font=font, fill=DARK + (200,))
    draw.text((x + offs, y + offs), text, font=font, fill=DARK + (180,))
    draw.text((x, y), text, font=font, fill=GOLD + (255,))

    overlay = overlay.filter(ImageFilter.GaussianBlur(0.35))
    return Image.alpha_composite(img, overlay)


def build() -> Image.Image:
    src = Image.open(SOURCE).convert("RGB")
    if src.size[0] != src.size[1]:
        side = min(src.size)
        x0 = (src.size[0] - side) // 2
        y0 = (src.size[1] - side) // 2
        src = src.crop((x0, y0, x0 + side, y0 + side))

    rgb = np.array(src)
    metal = metal_tint(rgb, gamma=0.78)
    metal = apply_vignette(metal, strength=0.28)

    img = Image.fromarray(metal).convert("RGBA")
    img = overlay_text(img)

    alpha = circular_alpha(img.size[0], feather=16)
    arr = np.array(img)
    arr[..., 3] = alpha
    return Image.fromarray(arr, "RGBA")


def main() -> None:
    logo = build()
    for out_path, size in ((OUT_1024, 1024), (OUT_512, 512), (OUT_128, 128)):
        out = logo if logo.size[0] == size else logo.resize((size, size), Image.Resampling.LANCZOS)
        out.save(out_path)
        print(f"wrote {out_path.name}")


if __name__ == "__main__":
    main()
