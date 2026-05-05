#!/usr/bin/env python3
"""v6: takes the freshly generated *_v6_base.png assets, masks any AI-garbled
ribbon text and renders clean Metal Mania typography. Never overwrites tracked
originals — outputs are *_v6.png siblings."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SCRIPT_DIR = Path(__file__).resolve().parent
ASSETS = SCRIPT_DIR.parent

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


def grade(img: Image.Image) -> Image.Image:
    arr = np.array(img.convert("RGB")).astype(np.float32)
    arr[..., 0] *= 1.04
    arr[..., 1] *= 1.00
    arr[..., 2] *= 0.92
    arr = ((arr - 128.0) * 1.08) + 128.0
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def mask_ribbon(img: Image.Image, cx: int, cy: int, w: int, h: int, *,
                        solid: bool = False) -> None:
      """Paint a bronze plaque over AI ribbon text before adding clean typography.
      Use solid=True for inner masks that must fully hide AI glyphs."""
      d = ImageDraw.Draw(img, "RGBA")
      arr = np.array(img.convert("RGB"))
      y0 = max(0, cy - h // 2 - 6)
      y1 = min(img.height, cy + h // 2 + 6)
      x0 = max(0, cx - w // 2 - 6)
      x1 = min(img.width, cx + w // 2 + 6)

      if solid:
            strip = max(6, h // 6)
            region_top = arr[y0:y0 + strip, x0:x1].reshape(-1, 3)
            region_bot = arr[max(y0, y1 - strip):y1, x0:x1].reshape(-1, 3)
            region_left = arr[y0:y1, x0:x0 + strip].reshape(-1, 3)
            region_right = arr[y0:y1, max(x0, x1 - strip):x1].reshape(-1, 3)
            region = np.concatenate([region_top, region_bot, region_left, region_right])
            base = tuple(int(np.percentile(region[:, i], 70)) for i in range(3)) if len(region) else (90, 65, 35)
            fill = (base[0], base[1], base[2], 255)
            d.rounded_rectangle(
                  [cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2],
                  radius=max(6, h // 6),
                  fill=fill,
            )
            return

      region = arr[y0:y1, x0:x1].reshape(-1, 3)
      base = tuple(int(np.median(region[:, i])) for i in range(3)) if len(region) else (90, 65, 35)
      r = max(10, h // 5)
      x_left, y_top = cx - w // 2, cy - h // 2
      x_right, y_bottom = cx + w // 2, cy + h // 2

      fill = (
            max(0, int(base[0] * 0.80)),
            max(0, int(base[1] * 0.80)),
            max(0, int(base[2] * 0.80)),
            248,
      )
      d.rounded_rectangle(
            [x_left, y_top, x_right, y_bottom],
            radius=r,
            fill=fill,
            outline=GOLD_DARK + (220,),
            width=max(2, h // 14),
      )

      # Vertical tonal ramp gives a carved plaque look instead of a flat block.
      y_span = max(1, y_bottom - y_top)
      for i in range(y_span):
            t = i / y_span
            if t < 0.35:
                  alpha = int(72 * (1.0 - (t / 0.35)))
                  col = (245, 220, 158, alpha)
            else:
                  alpha = int(54 * ((t - 0.35) / 0.65))
                  col = (36, 22, 10, alpha)
            d.line([(x_left + 8, y_top + i), (x_right - 8, y_top + i)], fill=col, width=1)

      inset = max(6, h // 9)
      d.rounded_rectangle(
            [x_left + inset, y_top + inset, x_right - inset, y_bottom - inset],
            radius=max(6, r - inset // 2),
            outline=(250, 230, 175, 70),
            width=1,
      )


def draw_text(img: Image.Image, text: str, cx: int, cy: int, w: int, h: int,
                    two_lines: bool = False) -> None:
      d = ImageDraw.Draw(img, "RGBA")

      def draw_line(line: str, f: ImageFont.FreeTypeFont, tx: int, ty: int) -> None:
            for dx, dy, a in [(-3, 1, 175), (3, 1, 175), (0, 3, 190), (1, 4, 150)]:
                  d.text((tx + dx, ty + dy), line, font=f, fill=NEAR_BLACK + (a,))
            for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                  d.text((tx + dx, ty + dy), line, font=f, fill=GOLD_DARK + (230,))
            d.text((tx, ty), line, font=f, fill=(212, 166, 74, 255))
            d.text((tx, ty - 1), line, font=f, fill=(248, 228, 160, 150))

      if two_lines:
            top, bottom = text.split("|", 1)
            f1 = fit_font(top, int(w * 0.88), int(h * 0.34))
            f2 = fit_font(bottom, int(w * 0.88), int(h * 0.34))
            for line, f, yy in ((top, f1, cy - h // 4), (bottom, f2, cy + h // 5)):
                  l, t, r, b = f.getbbox(line)
                  tx = cx - (r - l) // 2 - l
                  ty = yy - (b - t) // 2 - t
                  draw_line(line, f, tx, ty)
            return

      f = fit_font(text, int(w * 0.88), int(h * 0.62))
      l, t, r, b = f.getbbox(text)
      tx = cx - (r - l) // 2 - l
      ty = cy - (b - t) // 2 - t
      draw_line(text, f, tx, ty)


# ---------- per-asset builders ----------

def build(base_name: str, out_name: str, text: str, *, ribbon_y: float,
          ribbon_w: float, ribbon_h: float, two_lines: bool = False,
          extra_mask: tuple[float, float, float, float] | None = None,
          inner_masks: list[tuple[float, float, float]] | None = None) -> None:
    """inner_masks: list of (cy_frac, w_frac, h_frac) applied as mask_ribbon after grade."""
    src = ASSETS / base_name
    out = ASSETS / out_name
    img = Image.open(src).convert("RGB")
    W, H = img.size
    if extra_mask is not None:
        # extra rectangular soft mask before grading (e.g. shirt text scrubs)
        ex, ey, ew, eh = extra_mask
        d = ImageDraw.Draw(img.convert("RGBA"))
        cx, cy = int(W * ex), int(H * ey)
        ww, hh = int(W * ew), int(H * eh)
        rgba = img.convert("RGBA")
        d2 = ImageDraw.Draw(rgba, "RGBA")
        d2.ellipse([cx - ww // 2, cy - hh // 2, cx + ww // 2, cy + hh // 2],
                   fill=(28, 20, 12, 210))
        img = rgba.convert("RGB")
    img = grade(img)
    if inner_masks:
        for im_cy, im_w, im_h in inner_masks:
            mask_ribbon(img, W // 2, int(H * im_cy), int(W * im_w), int(H * im_h),
                        solid=True)
    cx = W // 2
    cy = int(H * ribbon_y)
    w = int(W * ribbon_w)
    h = int(H * ribbon_h)
    mask_ribbon(img, cx, cy, w, h)
    draw_text(img, text, cx, cy, w, h, two_lines=two_lines)
    img.save(out, optimize=True)
    print(f"wrote {out.name}")


if __name__ == "__main__":
    # Snagglemole banner — ribbon already across the bottom
    build("snagglemole_banner_v6_base.png", "snagglemole_banner_v6.png",
          "DOWN AT THE BOTTOM OF THE MOLE HOLE",
          ribbon_y=0.88, ribbon_w=0.62, ribbon_h=0.16)

    # Rolfmoleman banner — ribbon at bottom of the cave
    build("rolfmoleman_banner_v6_base.png", "rolfmoleman_banner_v6.png",
          "ROLFMOLEMAN",
          ribbon_y=0.86, ribbon_w=0.42, ribbon_h=0.18)

    # Rolfmoleman square logo — ribbon under bust
    build("rolfmoleman_logo_v6_base.png", "rolfmoleman_logo_v6.png",
          "ROLFMOLEMAN",
          ribbon_y=0.89, ribbon_w=0.58, ribbon_h=0.10)

    # Snagglemole tall logo — ribbon at very bottom, two lines
    build("snagglemole_logo_2_v6_base.png", "snagglemole_logo_2_v6.png",
          "DOWN AT THE BOTTOM|OF THE MOLE HOLE",
          ribbon_y=0.91, ribbon_w=0.66, ribbon_h=0.09, two_lines=True)

    # ── New org variations ──────────────────────────────────────────────────

    # Org avatar — metal demon mole warrior
    build("org_avatar_metal_v6.png", "org_avatar_metal_v6_final.png",
          "DOWNATTHEBOTTOM|OFTHEMOLEHOLE",
          ribbon_y=0.88, ribbon_w=0.55, ribbon_h=0.14, two_lines=True)

    # Org avatar — cyberpunk neon mole
    build("org_avatar_cyber_v6.png", "org_avatar_cyber_v6_final.png",
          "DOWNATTHEBOTTOM|OFTHEMOLEHOLE",
          ribbon_y=0.88, ribbon_w=0.55, ribbon_h=0.14, two_lines=True)

    # Org avatar — crowned fantasy mole
    build("org_avatar_fantasy_v6.png", "org_avatar_fantasy_v6_final.png",
          "DOWNATTHEBOTTOM|OFTHEMOLEHOLE",
          ribbon_y=0.88, ribbon_w=0.55, ribbon_h=0.14, two_lines=True)

    # Org tall logo — heavy metal mole crest
    build("org_logo_metal_v6.png", "org_logo_metal_v6_final.png",
          "DOWN AT THE BOTTOM|OF THE MOLE HOLE",
          ribbon_y=0.91, ribbon_w=0.68, ribbon_h=0.09, two_lines=True)

    # Org tall logo — fantasy heraldic mole (garbled "Fúntial" plaque)
    build("org_logo_fantasy_v6.png", "org_logo_fantasy_v6_final.png",
          "DOWN AT THE BOTTOM|OF THE MOLE HOLE",
          ribbon_y=0.87, ribbon_w=0.68, ribbon_h=0.09, two_lines=True)

    # Org banner — armored mole warrior with runic plaque
    build("org_banner_metal_v6.png", "org_banner_metal_v6_final.png",
          "DOWN AT THE BOTTOM OF THE MOLE HOLE",
          ribbon_y=0.88, ribbon_w=0.62, ribbon_h=0.18)

    # Org banner — fantasy mole royalty with clean scroll
    build("org_banner_fantasy_v6.png", "org_banner_fantasy_v6_final.png",
          "DOWN AT THE BOTTOM OF THE MOLE HOLE",
          ribbon_y=0.88, ribbon_w=0.62, ribbon_h=0.18)

    # ── New Rolf variations ─────────────────────────────────────────────────

    # Rolf avatar — explorer mole (round glasses, mining attire)
    build("rolfmoleman_avatar_explorer_v6.png", "rolfmoleman_avatar_explorer_v6_final.png",
          "ROLFMOLEMAN",
          ribbon_y=0.88, ribbon_w=0.55, ribbon_h=0.14)

    # Rolf avatar — entrepreneur mole (professorial, bearded)
    build("rolfmoleman_avatar_entrepreneur_v6.png", "rolfmoleman_avatar_entrepreneur_v6_final.png",
          "ROLFMOLEMAN",
          ribbon_y=0.88, ribbon_w=0.55, ribbon_h=0.14)

    # Rolf logo — explorer crest (heraldic oval, garbled plaque)
    build("rolfmoleman_logo_explorer_v6.png", "rolfmoleman_logo_explorer_v6_final.png",
          "ROLFMOLEMAN",
          ribbon_y=0.85, ribbon_w=0.62, ribbon_h=0.16)

    # Rolf logo — steampunk crest (gears, bronze palette)
    build("rolfmoleman_logo_steampunk_v6.png", "rolfmoleman_logo_steampunk_v6_final.png",
          "ROLFMOLEMAN",
          ribbon_y=0.88, ribbon_w=0.62, ribbon_h=0.16)

    # Rolf banner — explorer mole with pickaxe and gems
    build("rolfmoleman_banner_explorer_v6.png", "rolfmoleman_banner_explorer_v6_final.png",
          "ROLFMOLEMAN",
          ribbon_y=0.87, ribbon_w=0.42, ribbon_h=0.18)

    # Rolf banner — steampunk mole explorer
    build("rolfmoleman_banner_steampunk_v6.png", "rolfmoleman_banner_steampunk_v6_final.png",
          "ROLFMOLEMAN",
          ribbon_y=0.87, ribbon_w=0.42, ribbon_h=0.18)

    print("done")
