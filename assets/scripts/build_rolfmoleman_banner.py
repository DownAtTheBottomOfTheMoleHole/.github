#!/usr/bin/env python3
"""Build rolfmoleman_banner.png by compositing the logo onto the tunnel background."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

SCRIPT_DIR = Path(__file__).resolve().parent
ASSETS = SCRIPT_DIR.parent

BG_SRC   = ASSETS / "rolfmoleman_banner_bg.png"
LOGO_SRC = ASSETS / "rolfmoleman_logo.png"
OUT      = ASSETS / "rolfmoleman_banner.png"

# Final output size (matches snagglemole_banner.png)
OUT_W, OUT_H = 1983, 793

# Brand colours
GOLD        = (240, 208, 112)
GOLD_DARK   = (158, 96, 16)
DARK        = (22, 16, 10)
NEAR_BLACK  = (10, 6, 4)

FONT_CANDIDATES = [
    str(ASSETS / "fonts" / "MetalMania-Regular.ttf"),
    str(ASSETS / "fonts" / "Cinzel-Bold.ttf"),
    "/System/Library/Fonts/Supplemental/Herculanum.ttf",
]

TEXT = "rolfmoleman"


# ── helpers ───────────────────────────────────────────────────────────────────

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


def draw_scroll_ribbon(draw: ImageDraw.ImageDraw,
                       cx: int, cy: int, w: int, h: int) -> None:
    """Draw a curved banner ribbon centred at (cx, cy) with given width/height."""
    half_w = w // 2
    half_h = h // 2
    fold = h // 3

    # Main ribbon body (slightly trapezoidal – wider in middle)
    body = [
        (cx - half_w,          cy - half_h + fold // 2),
        (cx + half_w,          cy - half_h + fold // 2),
        (cx + half_w,          cy + half_h),
        (cx - half_w,          cy + half_h),
    ]

    # Left fold tab
    left_tab = [
        (cx - half_w,          cy - half_h + fold // 2),
        (cx - half_w - fold,   cy - half_h + fold),
        (cx - half_w - fold,   cy + half_h - fold // 4),
        (cx - half_w,          cy + half_h),
    ]
    # Right fold tab
    right_tab = [
        (cx + half_w,          cy - half_h + fold // 2),
        (cx + half_w + fold,   cy - half_h + fold),
        (cx + half_w + fold,   cy + half_h - fold // 4),
        (cx + half_w,          cy + half_h),
    ]

    fill       = GOLD_DARK + (230,)
    fold_fill  = DARK + (230,)
    outline    = NEAR_BLACK + (255,)
    lw         = max(2, w // 200)

    draw.polygon(left_tab,  fill=fold_fill, outline=outline)
    draw.polygon(right_tab, fill=fold_fill, outline=outline)
    draw.polygon(body,      fill=fill,      outline=outline)

    # Highlight stripe across top of body
    hl_h = max(4, h // 6)
    hl = [
        (cx - half_w + lw,     cy - half_h + fold // 2 + lw),
        (cx + half_w - lw,     cy - half_h + fold // 2 + lw),
        (cx + half_w - lw,     cy - half_h + fold // 2 + hl_h),
        (cx - half_w + lw,     cy - half_h + fold // 2 + hl_h),
    ]
    draw.polygon(hl, fill=GOLD + (45,))

    # Outer border on main body
    draw.polygon(body, fill=None, outline=GOLD + (160,), width=lw)


def apply_vignette(img: Image.Image, strength: float = 0.55) -> Image.Image:
    arr = np.array(img).astype(np.float32)
    h, w = arr.shape[:2]
    yy = np.linspace(-1, 1, h)[:, None]
    xx = np.linspace(-1, 1, w)[None, :]
    mask = 1.0 - strength * np.clip(xx**2 + yy**2, 0, 1)
    arr[..., :3] *= mask[..., None]
    return Image.fromarray(arr.clip(0, 255).astype(np.uint8), img.mode)


# ── main composite ─────────────────────────────────────────────────────────────

def build() -> None:
    # 1. Background ─────────────────────────────────────────────────────────────
    bg = Image.open(BG_SRC).convert("RGB")
    bg = bg.resize((OUT_W, OUT_H), Image.Resampling.LANCZOS)

    canvas = bg.copy().convert("RGBA")

    # 2. Logo (circular PNG) ────────────────────────────────────────────────────
    logo = Image.open(LOGO_SRC).convert("RGBA")

    # Scale so the logo occupies ~58% of banner height, centred horizontally,
    # upper-centre – positioned so the bottom of the circle sits at ~70% of
    # banner height (character appears to emerge from the tunnel opening)
    logo_h = int(OUT_H * 0.72)
    logo_w = logo_h  # square/circle
    logo = logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)

    lx = (OUT_W - logo_w) // 2
    ly = int(OUT_H * 0.03)   # sits near the top, overlapping the tunnel hole

    canvas.paste(logo, (lx, ly), logo)

    # 3. Scroll ribbon + text ───────────────────────────────────────────────────
    overlay = Image.new("RGBA", (OUT_W, OUT_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    ribbon_w = int(OUT_W * 0.52)
    ribbon_h = int(OUT_H * 0.165)
    cx = OUT_W // 2
    cy = int(OUT_H * 0.845)

    draw_scroll_ribbon(d, cx, cy, ribbon_w, ribbon_h)

    # Text
    text_max_w = int(ribbon_w * 0.78)
    text_max_h = int(ribbon_h * 0.52)
    font = load_font(TEXT, text_max_w, text_max_h)
    l, t, r, b = font.getbbox(TEXT)
    tw, th = r - l, b - t
    tx = cx - tw // 2 - l
    ty = cy - th // 2 - t + int(ribbon_h * 0.08)

    shadow_off = max(2, OUT_W // 500)
    for dx, dy in [(-shadow_off, 0), (shadow_off, 0),
                   (0, -shadow_off), (0, shadow_off), (shadow_off, shadow_off)]:
        d.text((tx + dx, ty + dy), TEXT, font=font, fill=DARK + (210,))
    d.text((tx, ty), TEXT, font=font, fill=GOLD + (255,))

    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=0.5))
    canvas = Image.alpha_composite(canvas, overlay)

    # 4. Vignette ───────────────────────────────────────────────────────────────
    canvas = apply_vignette(canvas, strength=0.45)

    # 5. Save as RGB (banner doesn't need transparency) ─────────────────────────
    final = canvas.convert("RGB")
    final.save(OUT, optimize=True)
    print(f"wrote {OUT.name}  ({OUT_W}×{OUT_H})")


if __name__ == "__main__":
    build()
