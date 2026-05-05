#!/usr/bin/env python3
"""Freshly regenerate v6 variant source images with stricter prompts.

This script updates the 13 newer v6 source images (org and rolf variants)
in place so finalize_v6.py can produce cleaner finals.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen, Request
import time

SCRIPT_DIR = Path(__file__).resolve().parent
ASSETS = SCRIPT_DIR.parent


@dataclass(frozen=True)
class Job:
    file_name: str
    width: int
    height: int
    seed: int
    prompt: str


COMMON = (
    "ultra-detailed cohesive composition, correct anatomy, no duplicated face parts, "
    "no warped eyes, no stretched snout, no extra limbs, no deformed hands, "
    "NO TEXT, NO LETTERS, NO GLYPHS, NO WATERMARK, NO LOGO, "
    "blank clean plaque/cartouche reserved for later typography"
)

JOBS = [
    Job(
        "org_avatar_metal_v6.png",
        1024,
        1024,
        310101,
        "front-facing heavy-metal anthropomorphic mole warlord avatar, spiked iron helmet, "
        "red ember eyes, bronze-black palette, chain ring frame, cinematic tunnel backlight, "
        f"{COMMON}",
    ),
    Job(
        "org_avatar_cyber_v6.png",
        1024,
        1024,
        310102,
        "front-facing cyberpunk anthropomorphic mole avatar, tactical goggles with subtle neon rim, "
        "bronze-black with controlled magenta accents, cables and chain frame, moody tunnel ambience, "
        f"{COMMON}",
    ),
    Job(
        "org_avatar_fantasy_v6.png",
        1024,
        1024,
        310103,
        "front-facing fantasy mole king avatar, crown and ornate armor, gemstones and forged filigree, "
        "bronze-black-gold palette, heraldic framing, dramatic cave light, "
        f"{COMMON}",
    ),
    Job(
        "org_logo_metal_v6.png",
        1024,
        1536,
        310104,
        "tall heraldic heavy-metal mole crest logo, oval chain frame, skull ornaments, "
        "centered mole bust with clear whiskers and snout, parchment scroll region clean and blank, "
        "engraved dark-fantasy bronze style, "
        f"{COMMON}",
    ),
    Job(
        "org_logo_fantasy_v6.png",
        1024,
        1536,
        310105,
        "tall fantasy heraldic mole crest logo, ornate royal frame, glowing cave atmosphere, "
        "centered anthropomorphic mole with crown and armor, clean lower scroll with no markings, "
        f"{COMMON}",
    ),
    Job(
        "org_banner_metal_v6.png",
        1536,
        640,
        310106,
        "wide cinematic heavy-metal mole banner, aggressive armored mole centered, chains and tunnel depth, "
        "lower-third wide stone-bronze ribbon plaque completely blank, dramatic rim light, "
        f"{COMMON}",
    ),
    Job(
        "org_banner_fantasy_v6.png",
        1536,
        640,
        310107,
        "wide fantasy-metal mole banner, regal armored mole centered in cavern throne setting, "
        "lower-third broad blank carved plaque for title, cohesive bronze-black-gold lighting, "
        f"{COMMON}",
    ),
    Job(
        "rolfmoleman_avatar_explorer_v6.png",
        1024,
        1024,
        310108,
        "stylized elderly anthropomorphic mole explorer avatar inspired by friendly bearded man with round glasses, "
        "kind eyes, white beard-like fur, miner cap, leathery coat, warm cave lantern light, "
        f"{COMMON}",
    ),
    Job(
        "rolfmoleman_avatar_entrepreneur_v6.png",
        1024,
        1024,
        310109,
        "stylized elderly anthropomorphic mole entrepreneur avatar, round spectacles, neatly groomed white beard-like fur, "
        "tweed-inspired jacket and brass details, confident friendly expression, "
        f"{COMMON}",
    ),
    Job(
        "rolfmoleman_logo_explorer_v6.png",
        1024,
        1536,
        310110,
        "tall explorer heraldic mole crest for rolfmoleman, oval chain frame, mining tools motifs, "
        "elderly mole with round glasses and white beard-like fur centered, clean blank scroll cartouche, "
        f"{COMMON}",
    ),
    Job(
        "rolfmoleman_logo_steampunk_v6.png",
        1024,
        1536,
        310111,
        "tall steampunk mole crest for rolfmoleman, brass gears and chain ornaments, "
        "elderly mole with spectacles and beard-like fur, strong centered symmetry, blank lower cartouche, "
        f"{COMMON}",
    ),
    Job(
        "rolfmoleman_banner_explorer_v6.png",
        1536,
        640,
        310112,
        "wide explorer-themed mole banner for rolfmoleman, elderly mole with round glasses and white beard-like fur, "
        "mine tunnel and relics, cohesive heavy-metal painterly style, blank ribbon plaque at bottom, "
        f"{COMMON}",
    ),
    Job(
        "rolfmoleman_banner_steampunk_v6.png",
        1536,
        640,
        310113,
        "wide steampunk mole banner for rolfmoleman, brass machinery, chain motifs, warm bronze lighting, "
        "elderly mole explorer with spectacles centered, blank lower plaque no text, "
        f"{COMMON}",
    ),
]


def build_url(job: Job) -> str:
    encoded = quote(job.prompt, safe="")
    return (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?model=flux&seed={job.seed}&width={job.width}&height={job.height}"
        "&enhance=true&nologo=true&private=true&safe=false"
    )


def download(job: Job) -> None:
    url = build_url(job)
    target = ASSETS / job.file_name
    headers = {"User-Agent": "molehole-v6-refresh/1.0"}

    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=120) as resp:
                content = resp.read()
            if len(content) < 10_000:
                raise RuntimeError(f"response too small ({len(content)} bytes)")
            target.write_bytes(content)
            print(f"ok  {job.file_name} ({len(content)} bytes)")
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            print(f"retry {attempt} for {job.file_name}: {exc}")
            time.sleep(1.0 * attempt)

    raise RuntimeError(f"failed {job.file_name}: {last_error}")


def main() -> None:
    for job in JOBS:
        download(job)


if __name__ == "__main__":
    main()
