#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = Path(__file__).resolve().parent
ASSETS = SCRIPT_DIR.parent

IN_SNAGGLE_BANNER = ASSETS / "snagglemole_banner_v5_strict.png"
IN_ROLF_BANNER = ASSETS / "rolfmoleman_banner_v5_strict.png"
IN_SNAGGLE_LOGO = ASSETS / "snagglemole_logo_2_v5_strict.png"

OUT_SNAGGLE_BANNER = ASSETS / "snagglemole_banner_v5.png"
OUT_ROLF_BANNER = ASSETS / "rolfmoleman_banner_v5.png"
OUT_SNAGGLE_LOGO = ASSETS / "snagglemole_logo_2_v5.png"

OUT_BW, OUT_BH = 1983, 793
OUT_LW, OUT_LH = 1024, 1536

GOLD = (236, 205, 122)
GOLD_DARK = (130, 84, 24)
NEAR_BLACK = (12, 8, 6)

FONT_CANDIDATES = [
    str(ASSETS / "fonts" / "MetalMania-Regular.ttf"),
    str(ASSETS / "fonts" / "Cinzel-Bold.ttf"),
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
]


def fit_font(text: str, max_w: int, max_h: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        try:
            size = max_h
            while size >= 10:
                f = ImageFont.truetype(path, size)
                l, t, r, b = f.getbbox(text)
                if (r - l) <= max_w and (b - t) <= max_h:
                    return f
                size -= 2
        except OSError:
            continue
    return ImageFont.load_default()


def resize_cover(img: Image.Image, out_w: int, out_h: int) -> Image.Image:
    iw, ih = img.size
    scale = max(out_w / iw, out_h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    x = (nw - out_w) // 2
    y = (nh - out_h) // 2
    return img.crop((x, y, x + out_w, y + out_h))


def grade(img: Image.Image) -> Image.Image:
    arr = np.array(img.convert("RGB")).astype(np.float32)
    arr[..., 0] *= 1.03
    arr[..., 1] *= 1.00
    arr[..., 2] *= 0.93
    arr = ((arr - 128.0) * 1.07) + 128.0
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def draw_clean_plaque_text(img: Image.Image, text: str, cx: int, cy: int, w: int, h: int, two_lines: bool = False) -> None:
    draw = ImageDraw.Draw(img, "RGBA")
    x1, y1 = cx - w // 2, cy - h // 2
    x2, y2 = cx + w // 2, cy + h // 2

    arr = np.array(img.convert("RGB"))
    region = arr[max(0, y1 - 8):max(1, y1 + 8), max(0, x1):min(img.width, x2)].reshape(-1, 3)
    base = tuple(int(np.median(region[:, i])) for i in range(3)) if len(region) else (90, 65, 35)
    fill = (max(0, int(base[0] * 0.90)), max(0, int(base[1] * 0.90)), max(0, int(base[2] * 0.90)), 235)

    draw.rounded_rectangle([x1, y1, x2, y2], radius=max(8, h // 5), fill=fill, outline=GOLD_DARK + (220,), width=max(2, h // 14))
    draw.line([(x1 + 8, y1 + 6), (x2 - 8, y1 + 6)], fill=GOLD + (130,), width=2)
    draw.line([(x1 + 8, y2 - 6), (x2 - 8, y2 - 6)], fill=GOLD + (130,), width=2)

    if two_lines:
        top, bottom = text.split("|", 1)
        f1 = fit_font(top, int(w * 0.86), int(h * 0.32))
        f2 = fit_font(bottom, int(w * 0.86), int(h * 0.32))
        for i, (line, f, yy) in enumerate(((top, f1, cy - h // 4), (bottom, f2, cy + h // 5))):
            l, t, r, b = f.getbbox(line)
            tx = cx - (r - l) // 2 - l
            ty = yy - (b - t) // 2 - t
            for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                draw.text((tx + dx, ty + dy), line, font=f, fill=NEAR_BLACK + (220,))
            draw.text((tx, ty), line, font=f, fill=GOLD + (255,))
        return

    f = fit_font(text, int(w * 0.86), int(h * 0.60))
    l, t, r, b = f.getbbox(text)
    tx = cx - (r - l) // 2 - l
    ty = cy - (b - t) // 2 - t
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (2, 2)]:
        draw.text((tx + dx, ty + dy), text, font=f, fill=NEAR_BLACK + (220,))
    draw.text((tx, ty), text, font=f, fill=GOLD + (255,))


def build_snaggle_banner() -> None:
    img = Image.open(IN_SNAGGLE_BANNER).convert("RGB")
    img = resize_cover(img, OUT_BW, OUT_BH)
    img = grade(img)
    draw_clean_plaque_text(
        img,
        "DOWN AT THE BOTTOM OF THE MOLE HOLE",
        cx=OUT_BW // 2,
        cy=int(OUT_BH * 0.86),
        w=int(OUT_BW * 0.48),
        h=int(OUT_BH * 0.13),
    )
    img.save(OUT_SNAGGLE_BANNER, optimize=True)
    print(f"wrote {OUT_SNAGGLE_BANNER.name}")


def build_rolf_banner() -> None:
    img = Image.open(IN_ROLF_BANNER).convert("RGBA")
    img = resize_cover(img, OUT_BW, OUT_BH)

    # Remove shirt text artefact with a broad soft chest shadow.
    d = ImageDraw.Draw(img, "RGBA")
    cx, cy = OUT_BW // 2, int(OUT_BH * 0.71)
    ew, eh = int(OUT_BW * 0.34), int(OUT_BH * 0.20)
    d.ellipse([cx - ew // 2, cy - eh // 2, cx + ew // 2, cy + eh // 2], fill=(32, 22, 14, 205))

    img = grade(img.convert("RGB"))
    draw_clean_plaque_text(
        img,
        "ROLFMOLEMAN",
        cx=OUT_BW // 2,
        cy=int(OUT_BH * 0.80),
        w=int(OUT_BW * 0.42),
        h=int(OUT_BH * 0.15),
    )
    img.save(OUT_ROLF_BANNER, optimize=True)
    print(f"wrote {OUT_ROLF_BANNER.name}")


def build_snaggle_logo() -> None:
    img = Image.open(IN_SNAGGLE_LOGO).convert("RGB")
    img = resize_cover(img, OUT_LW, OUT_LH)
    img = grade(img)
    draw_clean_plaque_text(
        img,
        "DOWN AT THE BOTTOM|OF THE MOLE HOLE",
        cx=OUT_LW // 2,
        cy=int(OUT_LH * 0.86),
        w=int(OUT_LW * 0.56),
        h=int(OUT_LH * 0.12),
        two_lines=True,
    )
    img.save(OUT_SNAGGLE_LOGO, optimize=True)
    print(f"wrote {OUT_SNAGGLE_LOGO.name}")


if __name__ == "__main__":
    build_snaggle_banner()
    build_rolf_banner()
    build_snaggle_logo()
    print("done")
