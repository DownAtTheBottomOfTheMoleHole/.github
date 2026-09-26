#!/usr/bin/env python3
"""Render the canonical organisation and repository README banners."""

from __future__ import annotations

import argparse
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "banners" / "downatthebottomofthemolehole_banner_20.png"
OUTPUT_DIR = ROOT / "assets" / "banners" / "repositories"
LOCAL_FONT = ROOT / "assets" / "fonts" / "stonehen.ttf"

PARCHMENT = (232, 215, 181, 255)
GOLD = (209, 164, 94, 255)
GOLD_DARK = (111, 71, 40, 255)
INK = (11, 9, 7, 255)
BLUE = (102, 210, 255, 255)
STONEHENGE_SHA256 = "ce21460833ed97837924bdaaa1455530ad330562dd73e80f0242fa0d4b879810"


@dataclass(frozen=True)
class Banner:
    title: str
    subtitle: str
    footer: str
    eyebrow: str = "DOWN AT THE BOTTOM OF THE MOLE HOLE"


BANNERS = {
    "downatthebottomofthemolehole": Banner(
        "DOWN AT THE BOTTOM",
        "OF THE MOLE HOLE",
        "TERRAFORM / AUTOMATION / PLATFORM TOOLING",
        eyebrow="ENGINEERING BELOW THE SURFACE",
    ),
    "github-private": Banner(
        "ORGANISATION BRANDING",
        "PRIVATE WORKSPACE",
        "DESIGN / GOVERNANCE / AUTOMATION",
    ),
    "terraform-latest": Banner(
        "TERRAFORM LATEST",
        "AUTOMATED TERRAFORM FOR CHOCOLATEY",
        "TERRAFORM / RELEASE AUTOMATION",
    ),
    "terraform-module-template": Banner(
        "TERRAFORM MODULE TEMPLATE",
        "CONSISTENT MODULES. REPEATABLE DELIVERY.",
        "TERRAFORM / MODULE DELIVERY",
    ),
    "terraform-azuredevops-naming": Banner(
        "AZURE DEVOPS NAMING",
        "STANDARDISED NAMES FOR EVERY RESOURCE",
        "TERRAFORM / AZURE DEVOPS",
    ),
    "megalinter-ado": Banner(
        "MEGALINTER ADO",
        "LINT 50+ LANGUAGES IN AZURE PIPELINES",
        "AZURE PIPELINES / QUALITY",
    ),
    "megalinter-mcp": Banner(
        "MEGALINTER MCP",
        "LINT / SECURE / REPORT",
        "MODEL CONTEXT PROTOCOL",
    ),
    "infracost-mcp": Banner(
        "INFRACOST MCP",
        "ESTIMATE / COMPARE / PUBLISH",
        "INFRASTRUCTURE / COSTS / MCP",
    ),
    "terraform-best-practices-mcp": Banner(
        "TERRAFORM BEST PRACTICES",
        "ANALYSE / SECURE / OPTIMISE",
        "TERRAFORM / MODEL CONTEXT PROTOCOL",
    ),
    "yarn-ado": Banner(
        "YARN ADO",
        "MODERN YARN FOR AZURE PIPELINES",
        "AZURE PIPELINES / TOOLING",
    ),
    "process-migrator": Banner(
        "PROCESS MIGRATOR",
        "MOVE INHERITED AZURE DEVOPS PROCESSES",
        "AZURE DEVOPS / MIGRATION",
    ),
    "ollama-tokeniser": Banner(
        "OLLAMA TOKENISER",
        "LOCAL MODEL-AWARE TOKEN CONTROL",
        "OLLAMA / VS CODE CHAT / LOCAL AI",
    ),
    "shared-copilot-orchestrator": Banner(
        "SHARED COPILOT ORCHESTRATOR",
        "REVIEW FINDINGS TO CODING AGENT",
        "GITHUB ACTIONS / COPILOT / AUTOMATION",
    ),
    "demo-repository": Banner(
        "DEMO REPOSITORY",
        "A SMALL SHOWCASE OF GITHUB WORKFLOWS",
        "GITHUB / AUTOMATION / EXAMPLES",
    ),
    "rachels-bakes": Banner(
        "RACHEL'S BAKES",
        "STOREFRONT",
        "ORGANISATION REPOSITORY",
    ),
    "rachels-bakes-terraform": Banner(
        "RACHEL'S BAKES",
        "AZURE INFRASTRUCTURE",
        "ORGANISATION REPOSITORY",
    ),
    "rachels-bakes-brand": Banner(
        "RACHEL'S BAKES",
        "BRAND ASSETS",
        "ORGANISATION REPOSITORY",
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--font",
        type=Path,
        default=Path(os.environ.get("STONEHENGE_FONT", LOCAL_FONT)),
        help="Path to the approved stonehen.ttf file (or set STONEHENGE_FONT).",
    )
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    return parser.parse_args()


def validate_font(font_path: Path) -> None:
    if not font_path.is_file():
        raise SystemExit(
            f"Stonehenge font not found at {font_path}. "
            "Download stonehen.ttf and pass it with --font."
        )

    try:
        family, style = ImageFont.truetype(font_path, 32).getname()
    except OSError as error:
        raise SystemExit(f"Unable to load font at {font_path}: {error}") from error

    if family.casefold() != "stonehenge":
        raise SystemExit(
            f"Expected the Stonehenge typeface, received {family} {style}. "
            "No fallback font will be used."
        )

    digest = hashlib.sha256(font_path.read_bytes()).hexdigest()
    if digest != STONEHENGE_SHA256:
        raise SystemExit(
            "The supplied Stonehenge file does not match the approved render "
            f"dependency (received SHA-256 {digest})."
        )


def cover_crop(source: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_width, target_height = size
    target_ratio = target_width / target_height
    source_width, source_height = source.size
    crop_height = source_width / target_ratio
    centre_y = source_height * 0.43
    top = max(0.0, min(source_height - crop_height, centre_y - crop_height / 2))
    box = (0.0, top, float(source_width), top + crop_height)
    return source.crop(box).resize(size, Image.Resampling.LANCZOS).convert("RGBA")


def fit_font(
    font_path: Path,
    text: str,
    max_width: int,
    max_height: int,
    maximum_size: int,
    stroke_width: int,
) -> ImageFont.FreeTypeFont:
    for size in range(maximum_size, 9, -1):
        font = ImageFont.truetype(font_path, size)
        left, top, right, bottom = font.getbbox(text, stroke_width=stroke_width)
        if right - left <= max_width and bottom - top <= max_height:
            return font
    raise ValueError(f"Unable to fit display text: {text}")


def draw_display_text(
    image: Image.Image,
    font_path: Path,
    text: str,
    box: tuple[int, int, int, int],
    maximum_size: int,
    *,
    fill: tuple[int, int, int, int] = PARCHMENT,
    stroke_width: int = 3,
) -> None:
    x0, y0, x1, y1 = box
    font = fit_font(
        font_path,
        text,
        x1 - x0,
        y1 - y0,
        maximum_size,
        stroke_width,
    )
    left, top, right, bottom = font.getbbox(text, stroke_width=stroke_width)
    width = right - left
    height = bottom - top
    x = x0 + ((x1 - x0) - width) / 2 - left
    y = y0 + ((y1 - y0) - height) / 2 - top

    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.text(
        (x + 5, y + 7),
        text,
        font=font,
        fill=(0, 0, 0, 220),
        stroke_width=stroke_width + 3,
        stroke_fill=(0, 0, 0, 210),
    )
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(2.2)))

    draw = ImageDraw.Draw(image)
    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill=INK,
    )
    draw.text((x, y - 1), text, font=font, fill=(248, 232, 198, 105))


def add_text_panel(image: Image.Image, start_x: int = 760) -> None:
    width, height = image.size
    fade_width = width - start_x
    mask_row = Image.new("L", (fade_width, 1))
    for x in range(fade_width):
        progress = x / max(1, fade_width - 1)
        alpha = int(195 * (0.18 + 0.82 * progress))
        mask_row.putpixel((x, 0), alpha)
    mask = mask_row.resize((fade_width, height))
    panel = Image.new("RGBA", (fade_width, height), INK)
    panel.putalpha(mask)
    image.alpha_composite(panel, (start_x, 0))


def draw_rule(image: Image.Image, x0: int, x1: int, y: int) -> None:
    draw = ImageDraw.Draw(image)
    draw.line((x0, y + 2, x1, y + 2), fill=(0, 0, 0, 190), width=5)
    draw.line((x0, y, x1, y), fill=GOLD_DARK, width=4)
    draw.line((x0, y - 1, x1, y - 1), fill=BLUE, width=2)


def render_banner(source: Image.Image, font_path: Path, spec: Banner) -> Image.Image:
    image = cover_crop(source, (1983, 793))
    add_text_panel(image)

    draw_display_text(
        image,
        font_path,
        spec.eyebrow,
        (940, 92, 1900, 150),
        maximum_size=34,
        fill=GOLD,
        stroke_width=2,
    )
    draw_display_text(
        image,
        font_path,
        spec.title,
        (870, 185, 1930, 338),
        maximum_size=112,
        stroke_width=4,
    )
    draw_rule(image, 975, 1830, 385)
    draw_display_text(
        image,
        font_path,
        spec.subtitle,
        (900, 425, 1900, 520),
        maximum_size=58,
        stroke_width=2,
    )
    draw_display_text(
        image,
        font_path,
        spec.footer,
        (980, 618, 1825, 676),
        maximum_size=34,
        fill=GOLD,
        stroke_width=2,
    )
    return image


def save_png(image: Image.Image, path: Path) -> None:
    image.convert("RGB").save(path, format="PNG", optimize=True)


def main() -> None:
    args = parse_args()
    validate_font(args.font)
    if not args.source.is_file():
        raise SystemExit(f"Source artwork not found at {args.source}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(args.source) as source_file:
        source = source_file.convert("RGB")
        for slug, spec in BANNERS.items():
            output = args.output_dir / f"{slug}.png"
            image = render_banner(source, args.font, spec)
            save_png(image, output)
            print(f"Rendered {output} ({image.size[0]}x{image.size[1]})")


if __name__ == "__main__":
    main()
