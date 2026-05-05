#!/usr/bin/env python3
"""Finalize v7 batch by adding clean typography and avatar cameo banners."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

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
    arr[..., 0] *= 1.05
    arr[..., 1] *= 1.00
    arr[..., 2] *= 0.92
    arr = ((arr - 128.0) * 1.08) + 128.0
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def mask_ribbon(img: Image.Image, cx: int, cy: int, w: int, h: int) -> None:
    d = ImageDraw.Draw(img, "RGBA")
    arr = np.array(img.convert("RGB"))
    y0 = max(0, cy - h // 2 - 6)
    y1 = min(img.height, cy + h // 2 + 6)
    x0 = max(0, cx - w // 2 - 6)
    x1 = min(img.width, cx + w // 2 + 6)
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


def draw_text(img: Image.Image, text: str, cx: int, cy: int, w: int, h: int, *, two_lines: bool = False) -> None:
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
        f1 = fit_font(top, int(w * 0.9), int(h * 0.33))
        f2 = fit_font(bottom, int(w * 0.9), int(h * 0.33))
        for line, f, yy in ((top, f1, cy - h // 4), (bottom, f2, cy + h // 5)):
            l, t, r, b = f.getbbox(line)
            tx = cx - (r - l) // 2 - l
            ty = yy - (b - t) // 2 - t
            draw_line(line, f, tx, ty)
        return

    f = fit_font(text, int(w * 0.9), int(h * 0.62))
    l, t, r, b = f.getbbox(text)
    tx = cx - (r - l) // 2 - l
    ty = cy - (b - t) // 2 - t
    draw_line(text, f, tx, ty)


def add_avatar_cameo(banner: Image.Image, avatar_path: Path, *, x_frac: float = 0.21, y_frac: float = 0.49, size_frac: float = 0.40) -> None:
    avatar = Image.open(avatar_path).convert("RGB")
    bw, bh = banner.size
    size = int(min(bw, bh) * size_frac)

    # Crop center square then circular mask.
    a_w, a_h = avatar.size
    crop = min(a_w, a_h)
    left = (a_w - crop) // 2
    top = (a_h - crop) // 2
    avatar_sq = avatar.crop((left, top, left + crop, top + crop)).resize((size, size), Image.Resampling.LANCZOS)

    circle_mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(circle_mask)
    md.ellipse((0, 0, size - 1, size - 1), fill=255)

    cameo = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cameo.paste(avatar_sq, (0, 0), circle_mask)

    # Border ring + soft shadow to blend into banner.
    ring = Image.new("RGBA", (size + 24, size + 24), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    rd.ellipse((2, 2, size + 21, size + 21), fill=(0, 0, 0, 120))
    ring = ring.filter(ImageFilter.GaussianBlur(6))

    frame = Image.new("RGBA", (size + 16, size + 16), (0, 0, 0, 0))
    fd = ImageDraw.Draw(frame)
    fd.ellipse((0, 0, size + 15, size + 15), fill=(58, 35, 18, 245), outline=GOLD_DARK + (240,), width=4)
    frame.paste(cameo, (8, 8), cameo)

    cx = int(bw * x_frac)
    cy = int(bh * y_frac)
    rx = cx - ring.width // 2
    ry = cy - ring.height // 2
    fx = cx - frame.width // 2
    fy = cy - frame.height // 2

    rgba = banner.convert("RGBA")
    rgba.alpha_composite(ring, (rx, ry))
    rgba.alpha_composite(frame, (fx, fy))
    banner.paste(rgba.convert("RGB"))


def build_avatar(base_name: str, out_name: str, text: str) -> None:
    src = ASSETS / base_name
    out = ASSETS / out_name
    img = grade(Image.open(src).convert("RGB"))
    w, h = img.size
    cx, cy = w // 2, int(h * 0.88)
    rw, rh = int(w * 0.56), int(h * 0.14)
    mask_ribbon(img, cx, cy, rw, rh)
    draw_text(img, text, cx, cy, rw, rh, two_lines=True)
    img.save(out, optimize=True)
    print(f"wrote {out.name}")


def center_crop_banner(img: Image.Image, target_w: int = 1536, target_h: int = 640) -> Image.Image:
    """Center-crop an image to target dimensions (used for 1536x1024 → 1536x640)."""
    src_w, src_h = img.size
    if src_w == target_w and src_h == target_h:
        return img
    left = (src_w - target_w) // 2
    top = (src_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def build_banner(base_name: str, avatar_name: str, out_name: str, text: str) -> None:
    src = ASSETS / base_name
    out = ASSETS / out_name
    img = grade(Image.open(src).convert("RGB"))
    img = center_crop_banner(img)

    add_avatar_cameo(img, ASSETS / avatar_name)

    w, h = img.size
    cx, cy = w // 2, int(h * 0.88)
    rw, rh = int(w * 0.62), int(h * 0.18)
    mask_ribbon(img, cx, cy, rw, rh)
    draw_text(img, text, cx, cy, rw, rh, two_lines=True)
    img.save(out, optimize=True)
    print(f"wrote {out.name}")


def build_banner_scene(
    base_name: str,
    out_name: str,
    text: str,
    *,
    plaque_cx_frac: float = 0.50,
    plaque_cy_frac: float = 0.90,
    plaque_w_frac: float = 0.62,
    plaque_h_frac: float = 0.16,
) -> None:
    """Render text directly onto an existing in-scene plaque with no extra cameo."""
    src = ASSETS / base_name
    out = ASSETS / out_name
    img = grade(Image.open(src).convert("RGB"))
    img = center_crop_banner(img)

    w, h = img.size
    cx = int(w * plaque_cx_frac)
    cy = int(h * plaque_cy_frac)
    rw = int(w * plaque_w_frac)
    rh = int(h * plaque_h_frac)
    draw_text(img, text, cx, cy, rw, rh, two_lines=True)
    img.save(out, optimize=True)
    print(f"wrote {out.name}")


def main() -> None:
    # DownAtTheBottomOfTheMoleHole
    build_avatar(
        "downatthebottomofthemolehole_avatar_v7_c1_base.png",
        "downatthebottomofthemolehole_avatar_v7_c1.png",
        "DOWNATTHEBOTTOM|OFTHEMOLEHOLE",
    )
    build_avatar(
        "downatthebottomofthemolehole_avatar_v7_c2_base.png",
        "downatthebottomofthemolehole_avatar_v7_c2.png",
        "DOWNATTHEBOTTOM|OFTHEMOLEHOLE",
    )
    build_banner(
        "downatthebottomofthemolehole_banner_v7_c1_base.png",
        "downatthebottomofthemolehole_avatar_v7_c1_base.png",
        "downatthebottomofthemolehole_banner_v7_c1.png",
        "DOWNATTHEBOTTOMOFTHEMOLEHOLE|MOTORHEAD COFFEE AND CODE",
    )
    build_banner(
        "downatthebottomofthemolehole_banner_v7_c2_base.png",
        "downatthebottomofthemolehole_avatar_v7_c2_base.png",
        "downatthebottomofthemolehole_banner_v7_c2.png",
        "DOWNATTHEBOTTOMOFTHEMOLEHOLE|GITHUB COFFEE MOLE POWER",
    )

    # RolfMoleman
    build_avatar(
        "rolfmoleman_avatar_v7_c1_base.png",
        "rolfmoleman_avatar_v7_c1.png",
        "ROLFMOLEMAN|CODE FUELLED BY COFFEE",
    )
    build_avatar(
        "rolfmoleman_avatar_v7_c2_base.png",
        "rolfmoleman_avatar_v7_c2.png",
        "ROLFMOLEMAN|MOTORHEAD DEV MOLE",
    )
    build_banner(
        "rolfmoleman_banner_v7_c1_base.png",
        "rolfmoleman_avatar_v7_c1_base.png",
        "rolfmoleman_banner_v7_c1.png",
        "ROLFMOLEMAN|METAL CODE COFFEE GRIT",
    )
    build_banner(
        "rolfmoleman_banner_v7_c2_base.png",
        "rolfmoleman_avatar_v7_c2_base.png",
        "rolfmoleman_banner_v7_c2.png",
        "ROLFMOLEMAN|GITHUB TUNNELS AND RIFFS",
    )


def main_openai() -> None:
    """Finalize c3/c4 variants generated by OpenAI gpt-image-2."""
    # DownAtTheBottomOfTheMoleHole — OpenAI variants
    build_avatar(
        "downatthebottomofthemolehole_avatar_v7_c3_base.png",
        "downatthebottomofthemolehole_avatar_v7_c3.png",
        "DOWNATTHEBOTTOM|OFTHEMOLEHOLE",
    )
    build_avatar(
        "downatthebottomofthemolehole_avatar_v7_c4_base.png",
        "downatthebottomofthemolehole_avatar_v7_c4.png",
        "DOWNATTHEBOTTOM|OFTHEMOLEHOLE",
    )
    build_banner(
        "downatthebottomofthemolehole_banner_v7_c3_base.png",
        "downatthebottomofthemolehole_avatar_v7_c3_base.png",
        "downatthebottomofthemolehole_banner_v7_c3.png",
        "DOWNATTHEBOTTOMOFTHEMOLEHOLE|MOTORHEAD COFFEE AND CODE",
    )
    build_banner(
        "downatthebottomofthemolehole_banner_v7_c4_base.png",
        "downatthebottomofthemolehole_avatar_v7_c4_base.png",
        "downatthebottomofthemolehole_banner_v7_c4.png",
        "DOWNATTHEBOTTOMOFTHEMOLEHOLE|GITHUB COFFEE MOLE POWER",
    )

    # RolfMoleman — OpenAI variants
    build_avatar(
        "rolfmoleman_avatar_v7_c3_base.png",
        "rolfmoleman_avatar_v7_c3.png",
        "ROLFMOLEMAN|BURROWING THROUGH THE CODE",
    )
    build_avatar(
        "rolfmoleman_avatar_v7_c4_base.png",
        "rolfmoleman_avatar_v7_c4.png",
        "ROLFMOLEMAN|MOTORHEAD DEV MOLE",
    )
    build_banner(
        "rolfmoleman_banner_v7_c3_base.png",
        "rolfmoleman_avatar_v7_c3_base.png",
        "rolfmoleman_banner_v7_c3.png",
        "ROLFMOLEMAN|MOTORHEAD COFFEE AND CODE",
    )
    build_banner(
        "rolfmoleman_banner_v7_c4_base.png",
        "rolfmoleman_avatar_v7_c4_base.png",
        "rolfmoleman_banner_v7_c4.png",
        "ROLFMOLEMAN|GITHUB MOLE UNDERGROUND",
    )

    # DownAtTheBottomOfTheMoleHole — OpenAI c5/c6 variants
    build_avatar(
        "downatthebottomofthemolehole_avatar_v7_c5_base.png",
        "downatthebottomofthemolehole_avatar_v7_c5.png",
        "DOWNATTHEBOTTOM|OFTHEMOLEHOLE",
    )
    build_avatar(
        "downatthebottomofthemolehole_avatar_v7_c6_base.png",
        "downatthebottomofthemolehole_avatar_v7_c6.png",
        "DOWNATTHEBOTTOM|OFTHEMOLEHOLE",
    )
    build_banner(
        "downatthebottomofthemolehole_banner_v7_c5_base.png",
        "downatthebottomofthemolehole_avatar_v7_c5_base.png",
        "downatthebottomofthemolehole_banner_v7_c5.png",
        "DOWNATTHEBOTTOMOFTHEMOLEHOLE|FORGE ROAST RIFFS AND CODE",
    )
    build_banner(
        "downatthebottomofthemolehole_banner_v7_c6_base.png",
        "downatthebottomofthemolehole_avatar_v7_c6_base.png",
        "downatthebottomofthemolehole_banner_v7_c6.png",
        "DOWNATTHEBOTTOMOFTHEMOLEHOLE|GITHUB MOLE CATHEDRAL",
    )

    # RolfMoleman — OpenAI c5/c6 variants
    build_avatar(
        "rolfmoleman_avatar_v7_c5_base.png",
        "rolfmoleman_avatar_v7_c5.png",
        "ROLFMOLEMAN|COFFEE LANTERNS AND CODE",
    )
    build_avatar(
        "rolfmoleman_avatar_v7_c6_base.png",
        "rolfmoleman_avatar_v7_c6.png",
        "ROLFMOLEMAN|MOTORHEAD CAVERN ENGINEER",
    )
    build_banner(
        "rolfmoleman_banner_v7_c5_base.png",
        "rolfmoleman_avatar_v7_c5_base.png",
        "rolfmoleman_banner_v7_c5.png",
        "ROLFMOLEMAN|COFFEE CODE UNDERGROUND",
    )
    build_banner(
        "rolfmoleman_banner_v7_c6_base.png",
        "rolfmoleman_avatar_v7_c6_base.png",
        "rolfmoleman_banner_v7_c6.png",
        "ROLFMOLEMAN|GITHUB TUNNEL BASECAMP",
    )

    # DownAtTheBottomOfTheMoleHole — OpenAI c7/c8 variants (scene-native plaques)
    build_avatar(
        "downatthebottomofthemolehole_avatar_v7_c7_base.png",
        "downatthebottomofthemolehole_avatar_v7_c7.png",
        "DOWNATTHEBOTTOM|OFTHEMOLEHOLE",
    )
    build_avatar(
        "downatthebottomofthemolehole_avatar_v7_c8_base.png",
        "downatthebottomofthemolehole_avatar_v7_c8.png",
        "DOWNATTHEBOTTOM|OFTHEMOLEHOLE",
    )
    build_banner_scene(
        "downatthebottomofthemolehole_banner_v7_c7_base.png",
        "downatthebottomofthemolehole_banner_v7_c7.png",
        "DOWNATTHEBOTTOMOFTHEMOLEHOLE|FORGE COFFEE METAL CODE",
        plaque_cx_frac=0.50,
        plaque_cy_frac=0.89,
        plaque_w_frac=0.72,
        plaque_h_frac=0.19,
    )
    build_banner_scene(
        "downatthebottomofthemolehole_banner_v7_c8_base.png",
        "downatthebottomofthemolehole_banner_v7_c8.png",
        "DOWNATTHEBOTTOMOFTHEMOLEHOLE|GITHUB MOLE THRONE",
        plaque_cx_frac=0.50,
        plaque_cy_frac=0.88,
        plaque_w_frac=0.66,
        plaque_h_frac=0.18,
    )

    # RolfMoleman — OpenAI c7/c8 variants (scene-native plaques)
    build_avatar(
        "rolfmoleman_avatar_v7_c7_base.png",
        "rolfmoleman_avatar_v7_c7.png",
        "ROLFMOLEMAN|COFFEE MAPS AND CODE",
    )
    build_avatar(
        "rolfmoleman_avatar_v7_c8_base.png",
        "rolfmoleman_avatar_v7_c8.png",
        "ROLFMOLEMAN|UNDERGROUND CODE CARTOGRAPHER",
    )
    build_banner_scene(
        "rolfmoleman_banner_v7_c7_base.png",
        "rolfmoleman_banner_v7_c7.png",
        "ROLFMOLEMAN|COFFEE CODE UNDERGROUND",
        plaque_cx_frac=0.50,
        plaque_cy_frac=0.88,
        plaque_w_frac=0.68,
        plaque_h_frac=0.19,
    )
    build_banner_scene(
        "rolfmoleman_banner_v7_c8_base.png",
        "rolfmoleman_banner_v7_c8.png",
        "ROLFMOLEMAN|GITHUB CAVERN BASECAMP",
        plaque_cx_frac=0.50,
        plaque_cy_frac=0.90,
        plaque_w_frac=0.68,
        plaque_h_frac=0.17,
    )


if __name__ == "__main__":
    main()
    main_openai()
