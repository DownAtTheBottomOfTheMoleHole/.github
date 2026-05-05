#!/usr/bin/env python3
"""
Post-process the three generated images:
  1. rolfmoleman_banner_v2.png  → rolfmoleman_banner.png  (1983×793)
  2. snagglemole_banner_v2.png  → snagglemole_banner.png  (1983×793)
  3. snagglemole_logo_2_v2.png  → snagglemole_logo_2.png  (768×1024)

For each: erase garbled AI scroll text, render clean Metal Mania text.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SCRIPT_DIR = Path(__file__).resolve().parent
ASSETS = SCRIPT_DIR.parent

FONT_CANDIDATES = [
    str(ASSETS / "fonts" / "MetalMania-Regular.ttf"),
    str(ASSETS / "fonts" / "Cinzel-Bold.ttf"),
    "/System/Library/Fonts/Supplemental/Herculanum.ttf",
]

GOLD       = (240, 208, 112)
GOLD_DARK  = (158, 96,  16)
DARK       = (22,  16,  10)
NEAR_BLACK = (10,  6,   4)


def load_font(text: str, max_w: int, max_h: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        try:
            size = max_h
            while size >= 10:
                font = ImageFont.truetype(path, size)
                l, t, r, b = font.getbbox(text)
                if (r - l) <= max_w and (b - t) <= max_h:
                    return font
                size -= 2
        except OSError:
            continue
    return ImageFont.load_default()


def sample_ribbon_colour(img: Image.Image,
                          cx: int, cy: int,
                          w: int, h: int) -> tuple[int, int, int]:
    """Sample median colour of the scroll ribbon region."""
    arr = np.array(img.convert("RGB"))
    ih, iw = arr.shape[:2]
    x1 = max(0, cx - w // 2)
    x2 = min(iw, cx + w // 2)
    y1 = max(0, cy - h // 2)
    y2 = min(ih, cy + h // 2)
    region = arr[y1:y2, x1:x2].reshape(-1, 3)
    med = tuple(int(np.median(region[:, i])) for i in range(3))
    return med  # type: ignore[return-value]


def darken(c: tuple[int, int, int], factor: float = 0.6) -> tuple[int, int, int]:
    return tuple(max(0, int(v * factor)) for v in c)  # type: ignore[return-value]


def apply_vignette(img: Image.Image, strength: float = 0.45) -> Image.Image:
    arr = np.array(img).astype(np.float32)
    h, w = arr.shape[:2]
    yy = np.linspace(-1, 1, h)[:, None]
    xx = np.linspace(-1, 1, w)[None, :]
    mask = 1.0 - strength * np.clip(xx**2 + yy**2, 0, 1)
    arr[..., :3] *= mask[..., None]
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8), img.mode)


def render_text_on_ribbon(img: Image.Image,
                           text: str,
                           cx: int, cy: int,
                           ribbon_w: int, ribbon_h: int) -> None:
    """
    In-place: fully paint the scroll ribbon zone, then render clean text.
    Also clears any AI artefacts below the ribbon to the image edge.
    """
    draw = ImageDraw.Draw(img)
    iw, ih = img.size

    x1 = max(0, cx - ribbon_w // 2)
    x2 = min(iw, cx + ribbon_w // 2)
    y1 = max(0, cy - ribbon_h // 2)
    y2 = min(ih, cy + ribbon_h // 2)

    # Sample background colour just above the ribbon
    arr = np.array(img.convert("RGB"))
    sample_y1 = max(0, y1 - ribbon_h)
    sample_y2 = max(1, y1)
    region = arr[sample_y1:sample_y2, x1:x2].reshape(-1, 3)
    bg_colour = tuple(int(np.median(region[:, i])) for i in range(3)) if len(region) else (30, 20, 10)
    dark_bg = darken(bg_colour, 0.55)

    # Wipe everything from y1 to bottom edge (removes all AI scroll artefacts)
    draw.rectangle([0, y1, iw, ih], fill=dark_bg)

    # Scroll ribbon body (slightly lighter than bg, bronze/gold tones)
    ribbon_fill = (
        min(255, dark_bg[0] + 40),
        min(255, dark_bg[1] + 25),
        min(255, dark_bg[2] + 8),
    )
    fold = ribbon_h // 3

    # Left and right fold tabs (darker)
    fold_fill = darken(ribbon_fill, 0.72)
    draw.polygon([
        (x1,        y1),
        (x1 - fold, y1 + fold),
        (x1 - fold, y2 - fold // 4),
        (x1,        y2),
    ], fill=fold_fill)
    draw.polygon([
        (x2,        y1),
        (x2 + fold, y1 + fold),
        (x2 + fold, y2 - fold // 4),
        (x2,        y2),
    ], fill=fold_fill)

    # Main ribbon body
    draw.rectangle([x1, y1, x2, y2], fill=ribbon_fill)

    # Gold highlight stripe near top
    hl_h = max(3, ribbon_h // 7)
    draw.rectangle([x1 + 2, y1 + 2, x2 - 2, y1 + hl_h], fill=(*GOLD, 40))

    # Gold border lines
    lw = max(2, ribbon_h // 16)
    draw.rectangle([x1, y1, x2, y2], outline=GOLD_DARK, width=lw)
    draw.line([(x1 + lw, y1 + lw * 2), (x2 - lw, y1 + lw * 2)],
              fill=GOLD + (180,), width=max(1, lw // 2))
    draw.line([(x1 + lw, y2 - lw * 2), (x2 - lw, y2 - lw * 2)],
              fill=GOLD + (180,), width=max(1, lw // 2))

    # Text
    text_max_w = int(ribbon_w * 0.88)
    text_max_h = int(ribbon_h * 0.58)
    font = load_font(text, text_max_w, text_max_h)
    l, t, r, b = font.getbbox(text)
    tw, th = r - l, b - t
    tx = cx - tw // 2 - l
    ty = cy - th // 2 - t

    shadow = max(2, ribbon_h // 24)
    for dx, dy in [(-shadow, 0), (shadow, 0), (0, -shadow), (0, shadow),
                   (shadow, shadow), (-shadow, shadow)]:
        draw.text((tx + dx, ty + dy), text, font=font, fill=NEAR_BLACK + (220,))
    draw.text((tx, ty), text, font=font, fill=GOLD)


# ── individual build functions ─────────────────────────────────────────────────

def build_rolfmoleman_banner() -> None:
    src = ASSETS / "rolfmoleman_banner_v2.png"
    out = ASSETS / "rolfmoleman_banner.png"
    OUT_W, OUT_H = 1983, 793

    img = Image.open(src).convert("RGB")
    img = img.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS)
    img = apply_vignette(img, strength=0.40)

    # Ribbon sits in the bottom 18% of the final image, 50% wide
    cx = OUT_W // 2
    rw = int(OUT_W * 0.50)
    rh = int(OUT_H * 0.155)
    # cy is the centre of the ribbon; place it so the ribbon top is at ~81%
    cy = int(OUT_H * 0.81) + rh // 2

    render_text_on_ribbon(img, "rolfmoleman", cx, cy, rw, rh)

    img.save(out, optimize=True)
    print(f"wrote {out.name}  ({OUT_W}×{OUT_H})")


def build_snagglemole_banner() -> None:
    src = ASSETS / "snagglemole_banner_v2.png"
    out = ASSETS / "snagglemole_banner.png"
    OUT_W, OUT_H = 1983, 793

    img = Image.open(src).convert("RGB")
    img = img.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS)
    img = apply_vignette(img, strength=0.40)

    # Ribbon in the bottom 18%, centred (AI scroll was left-biased but we centre cleanly)
    cx = OUT_W // 2
    rw = int(OUT_W * 0.58)
    rh = int(OUT_H * 0.155)
    cy = int(OUT_H * 0.81) + rh // 2

    render_text_on_ribbon(img, "Down At The Bottom of The Mole Hole",
                          cx, cy, rw, rh)

    img.save(out, optimize=True)
    print(f"wrote {out.name}  ({OUT_W}×{OUT_H})")


def build_snagglemole_logo_2() -> None:
    src = ASSETS / "snagglemole_logo_2_v2.png"
    out = ASSETS / "snagglemole_logo_2.png"

    img = Image.open(src).convert("RGB")
    iw, ih = img.size
    # Keep original size.
    # The AI logo has a scroll area starting at ~58% of height; wipe from there down
    cx = iw // 2
    rw = int(iw * 0.75)
    rh = int(ih * 0.155)
    # Place ribbon so its top is at ~60% of height
    cy = int(ih * 0.60) + rh // 2

    render_text_on_ribbon(img, "Down At The Bottom of The Mole Hole",
                          cx, cy, rw, rh)

    # Crop away dead black below the ribbon
    crop_bottom = min(ih, cy + rh // 2 + 24)
    img = img.crop((0, 0, iw, crop_bottom))
    iw2, ih2 = img.size

    img.save(out, optimize=True)
    print(f"wrote {out.name}  ({iw2}×{ih2})")


if __name__ == "__main__":
    build_rolfmoleman_banner()
    build_snagglemole_banner()
    build_snagglemole_logo_2()
    print("done.")
