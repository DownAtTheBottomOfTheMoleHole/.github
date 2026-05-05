#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from heavy_metal_icons import apply_metal_ramp, apply_vignette, rgb_to_luminance

SCRIPT_DIR = Path(__file__).resolve().parent
ASSETS = SCRIPT_DIR.parent

SOURCE = ASSETS / "rolfmoleman_source_v7a.png"
OUT_1024 = ASSETS / "rolfmoleman_logo_try3.png"
OUT_512 = ASSETS / "rolfmoleman_logo_try3_512.png"
OUT_128 = ASSETS / "rolfmoleman_logo_try3_128.png"

FONT_CANDIDATES = [
    str(SCRIPT_DIR.parent / "fonts" / "MetalMania-Regular.ttf"),
    str(SCRIPT_DIR.parent / "fonts" / "Cinzel-Bold.ttf"),
    "/System/Library/Fonts/Supplemental/Herculanum.ttf",
    "/System/Library/Fonts/Supplemental/Copperplate.ttc",
]

GOLD = (240, 208, 112)
BRONZE = (158, 96, 16)
DARK = (22, 16, 10)


def remap_brand_tones(rgb: np.ndarray, gamma: float = 0.84) -> np.ndarray:
    lum = rgb_to_luminance(rgb)
    lo, hi = np.percentile(lum, [2, 98])
    stretched = np.clip((lum - lo) / max(1e-6, hi - lo), 0, 1)
    stretched = np.power(stretched, gamma)
    mapped = apply_metal_ramp(stretched)
    return apply_vignette(mapped, strength=0.24)


def circular_alpha(size: int, feather: int = 14) -> np.ndarray:
    yy, xx = np.ogrid[:size, :size]
    c = size / 2.0
    radius = size / 2.0 - 3
    dist = np.sqrt((xx - c) ** 2 + (yy - c) ** 2)
    alpha = np.clip((radius - dist) / feather, 0, 1)
    return (alpha * 255).astype(np.uint8)


def choose_font(text: str, width: int, height: int) -> ImageFont.FreeTypeFont:
    for font_path in FONT_CANDIDATES:
        try:
            size = height
            while size >= 12:
                font = ImageFont.truetype(font_path, size)
                l, t, r, b = font.getbbox(text)
                if (r - l) <= width and (b - t) <= height:
                    return font
                size -= 2
        except OSError:
            continue
    return ImageFont.load_default()


def draw_nameplate(img: Image.Image, text: str = "ROLFMOLEMAN") -> Image.Image:
    out = img.convert("RGBA")
    w, h = out.size

    plate = Image.new("RGBA", out.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(plate)

    x0 = int(w * 0.16)
    x1 = int(w * 0.84)
    y0 = int(h * 0.80)
    y1 = int(h * 0.94)
    r = int((y1 - y0) * 0.35)

    # Build a curved plaque shape.
    d.rounded_rectangle((x0, y0, x1, y1), radius=r, fill=BRONZE + (235,), outline=DARK + (255,), width=max(2, w // 300))

    # Simple metal highlight band.
    hl_y0 = y0 + max(2, (y1 - y0) // 10)
    hl_y1 = y0 + max(6, (y1 - y0) // 3)
    d.rounded_rectangle((x0 + 4, hl_y0, x1 - 4, hl_y1), radius=max(2, r // 2), fill=GOLD + (60,))

    font = choose_font(text, int((x1 - x0) * 0.88), int((y1 - y0) * 0.55))
    l, t, rtxt, b = font.getbbox(text)
    tw, th = rtxt - l, b - t
    tx = (x0 + x1 - tw) // 2 - l
    ty = (y0 + y1 - th) // 2 - t

    s = max(1, w // 420)
    for dx, dy in [(-s, 0), (s, 0), (0, -s), (0, s), (s, s)]:
        d.text((tx + dx, ty + dy), text, font=font, fill=DARK + (220,))
    d.text((tx, ty), text, font=font, fill=GOLD + (255,))

    plate = plate.filter(ImageFilter.GaussianBlur(radius=0.4))
    return Image.alpha_composite(out, plate)


def build() -> Image.Image:
    src = Image.open(SOURCE).convert("RGB")
    if src.size[0] != src.size[1]:
        side = min(src.size)
        ox = (src.size[0] - side) // 2
        oy = (src.size[1] - side) // 2
        src = src.crop((ox, oy, ox + side, oy + side))

    rgb = np.array(src)
    brand = remap_brand_tones(rgb, gamma=0.82)

    base = Image.fromarray(brand, "RGB").convert("RGBA")
    base = draw_nameplate(base)

    arr = np.array(base)
    arr[..., 3] = circular_alpha(base.size[0], feather=16)
    return Image.fromarray(arr, "RGBA")


def main() -> None:
    logo = build()
    targets = [
        (OUT_1024, 1024),
        (OUT_512, 512),
        (OUT_128, 128),
    ]
    for out_path, size in targets:
        out = logo if logo.size[0] == size else logo.resize((size, size), Image.Resampling.LANCZOS)
        out.save(out_path)
        print(f"wrote {out_path.name}")


if __name__ == "__main__":
    main()
