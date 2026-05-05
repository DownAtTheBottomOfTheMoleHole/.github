#!/usr/bin/env python3
"""
Generate v7 c10 batch — both DownAtTheBottomOfTheMoleHole org and RolfMoleman.

Key improvements over previous batches:
- Banners generated natively at 1536x640 — NO post-crop needed, characters intact.
- Prompts explicitly ask for text already rendered inside the scene (arch / ribbon arc).
- Likeness anchored: bearded man with rectangular glasses merged into mole identity.
- Slogans: motorhead, coffee, github, sensible tone.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
import random
import time

SCRIPT_DIR = Path(__file__).resolve().parent
ASSETS = SCRIPT_DIR.parent

COMMON_NEGATIVE = (
    "no extra text, no watermark, no logo artifacts, "
    "no extra limbs, no distorted anatomy, no severed heads, no cropped faces, "
    "full head and shoulders visible, cohesive composition"
)

# Shared likeness phrase kept consistent
LIKENESS = (
    "character inspired by a real middle-aged bearded man with thick rectangular dark-rimmed glasses "
    "and a warm but intense expression, merged seamlessly into mole anatomy"
)


@dataclass(frozen=True)
class Job:
    file_name: str
    width: int
    height: int
    seed: int
    prompt: str


JOBS: list[Job] = [
    # ─────────────────────────────────────────────────────────────────────────
    # DownAtTheBottomOfTheMoleHole — AVATARS (1024x1024)
    # ─────────────────────────────────────────────────────────────────────────
    Job(
        "downatthebottomofthemolehole_avatar_v7_c10a_base.png",
        1024,
        1024,
        810201,
        f"Heroic heavy-metal anthropomorphic mole avatar, {LIKENESS}, "
        "spiked miner helmet, round spectacles fused to mole snout, thick chest-length fur beard, "
        "black metal studded jacket with github octocat embossed badge, coffee-steam halo motif, "
        "dramatic underground cavern backlight, bronze-black-gold colour palette, "
        "arc of forged letters 'DOWNATTHEBOTTOMOFTHEMOLEHOLE' carved into circular frame border at top, "
        "second arc of smaller text 'MOTORHEAD · COFFEE · CODE' at bottom of frame, "
        "text is part of the metalwork not floating, highly detailed portrait, "
        f"{COMMON_NEGATIVE}",
    ),
    Job(
        "downatthebottomofthemolehole_avatar_v7_c10b_base.png",
        1024,
        1024,
        810202,
        f"Dark-fantasy mole emblem portrait, {LIKENESS}, "
        "heraldic oval chain border with skull bosses, mole wearing motorhead-style studded vest, "
        "github octocat medallion on chest, coffee lantern in one claw, "
        "glowing amber tunnel backdrop, "
        "text 'DOWN AT THE BOTTOM OF THE MOLE HOLE' engraved into the stone arch above head, "
        "text 'CODE · COFFEE · GRIT' etched into ribbon cartouche below, "
        "text feels sculpted into scene, cinematic oil-painting style, bronze-black palette, "
        f"{COMMON_NEGATIVE}",
    ),

    # ─────────────────────────────────────────────────────────────────────────
    # DownAtTheBottomOfTheMoleHole — BANNERS (1536x640, native — no crop)
    # ─────────────────────────────────────────────────────────────────────────
    Job(
        "downatthebottomofthemolehole_banner_v7_c10a_base.png",
        1536,
        640,
        810203,
        f"Ultra-wide cinematic underground heavy-metal banner, {LIKENESS} as main subject filling left-centre, "
        "full head and torso visible, mole in motorhead-inspired studded jacket, github badge, "
        "dramatic chain-and-forge architecture spanning full width, "
        "stone-carved banner plaque along bottom third reading 'DOWN AT THE BOTTOM OF THE MOLE HOLE' "
        "with sub-line 'FORGE · COFFEE · METAL · CODE', text chiselled into stone, part of the scene, "
        "right side has tunnel depth and ember glow, "
        "bronze-black-gold palette, no floating text overlays, "
        f"{COMMON_NEGATIVE}",
    ),
    Job(
        "downatthebottomofthemolehole_banner_v7_c10b_base.png",
        1536,
        640,
        810204,
        f"Wide heavy-metal org banner, bearded mole character ({LIKENESS}) centre-left in heroic pose, "
        "full head and torso always in frame, chains and forged steel environment, "
        "coffee-steam wisps and github octocat runes etched into cave walls, "
        "lower ribbon reads 'DOWN AT THE BOTTOM OF THE MOLE HOLE · BURROWING THROUGH THE CODE', "
        "text carved in relief into the stone ribbon, not floating, "
        "wide panoramic composition, painterly detail, amber underground lighting, "
        f"{COMMON_NEGATIVE}",
    ),

    # ─────────────────────────────────────────────────────────────────────────
    # RolfMoleman — AVATARS (1024x1024)
    # ─────────────────────────────────────────────────────────────────────────
    Job(
        "rolfmoleman_avatar_v7_c10a_base.png",
        1024,
        1024,
        810205,
        f"Steampunk-heavy-metal mole explorer avatar, {LIKENESS}, "
        "round brass goggles over rectangular glasses, long white fur beard, "
        "leather tool-vest with coffee flask and github USB-drive fob, "
        "motorhead patch on shoulder, glowing lantern in hand, "
        "circular crest frame with text 'ROLFMOLEMAN' arced along top in raised metal letters, "
        "'CODE · COFFEE · GRIT' in smaller arc at bottom of frame, "
        "underground mine backdrop, bronze-black palette, text integral to metalwork border, "
        f"{COMMON_NEGATIVE}",
    ),
    Job(
        "rolfmoleman_avatar_v7_c10b_base.png",
        1024,
        1024,
        810206,
        f"Heroic mole hacker portrait crest, {LIKENESS}, "
        "chain medallion frame with skull corner bosses, mole in studded jacket, "
        "github terminal screen reflected in glasses, coffee mug motif, motorhead horns hat pin, "
        "warm amber cavern light, "
        "text 'ROLFMOLEMAN' inscribed in stone arch above, "
        "'BURROWING THROUGH THE CODE' on ribbon cartouche below chin, "
        "text feels part of the carved stonework, cinematic detail, "
        f"{COMMON_NEGATIVE}",
    ),

    # ─────────────────────────────────────────────────────────────────────────
    # RolfMoleman — BANNERS (1536x640, native — no crop)
    # ─────────────────────────────────────────────────────────────────────────
    Job(
        "rolfmoleman_banner_v7_c10a_base.png",
        1536,
        640,
        810207,
        f"Cinematic wide banner featuring RolfMoleman, bearded bespectacled mole ({LIKENESS}), "
        "full head and shoulders visible, left-of-centre, wearing motorhead-inspired leather and chains, "
        "tunnel forge environment, chains and lanterns spanning full width, "
        "lower stone plaque reads 'ROLFMOLEMAN' on first line, 'COFFEE · GITHUB · METAL · CODE' below, "
        "text chiselled into stone plaque, part of the scene, not overlaid, "
        "warm bronze underground lighting, github rune etchings in cave walls, "
        f"{COMMON_NEGATIVE}",
    ),
    Job(
        "rolfmoleman_banner_v7_c10b_base.png",
        1536,
        640,
        810208,
        f"Epic wide heavy-metal mole banner, {LIKENESS} mole character right-of-centre in full portrait, "
        "complete head and torso visible, no cropping, chains and forge architecture, "
        "coffee steam rising, github octocat carved into stonework, "
        "stone banner ribbon at bottom carved with 'ROLFMOLEMAN · UNDERGROUND CODE CARTOGRAPHER', "
        "text integral to stone surface relief, dramatic side lighting, "
        "high-detail oil painting style, bronze-black-gold, "
        f"{COMMON_NEGATIVE}",
    ),
]


def build_url(job: Job) -> str:
    encoded = quote(job.prompt, safe="")
    return (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?model=flux&seed={job.seed}&width={job.width}&height={job.height}"
        "&enhance=true&nologo=true&private=true&safe=false"
    )


def download_job(job: Job) -> None:
    out_path = ASSETS / job.file_name
    url = build_url(job)

    for attempt in range(1, 7):
        try:
            req = Request(url, headers={"User-Agent": "molehole-v7-c10/1.0"})
            with urlopen(req, timeout=180) as resp:
                blob = resp.read()

            if len(blob) < 12_000:
                raise RuntimeError(f"response too small: {len(blob)} bytes")

            out_path.write_bytes(blob)
            print(f"ok   {job.file_name} ({len(blob):,} bytes)")
            return
        except Exception as exc:  # noqa: BLE001
            if attempt == 6:
                raise RuntimeError(f"failed {job.file_name}: {exc}") from exc
            sleep_for = (1.8 ** attempt) + random.uniform(0.2, 0.9)
            print(f"retry {attempt} {job.file_name}: {exc} (sleep {sleep_for:.1f}s)")
            time.sleep(sleep_for)


def main() -> None:
    print(f"Generating {len(JOBS)} images for v7 c10 batch...")
    for idx, job in enumerate(JOBS, start=1):
        print(f"[{idx}/{len(JOBS)}] {job.file_name} ({job.width}x{job.height})")
        download_job(job)
        if idx != len(JOBS):
            time.sleep(random.uniform(1.5, 2.8))
    print("Done.")


if __name__ == "__main__":
    main()
