#!/usr/bin/env python3
"""Generate a new v7 image batch for both entities with rate-limit-aware retries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
import random
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


COMMON_NEGATIVE = (
    "NO TEXT, NO LETTERS, NO GLYPHS, NO WATERMARK, NO LOGO artifacts, "
    "no extra limbs, no distorted eyes, no deformed face, cohesive anatomy"
)

JOBS = [
    Job(
        "downatthebottomofthemolehole_avatar_v7_c1_base.png",
        1024,
        1024,
        470101,
        "heroic heavy-metal anthropomorphic mole portrait inspired by a real bearded man with rectangular glasses, "
        "kind but intense expression, thick beard texture, motorhead energy, bronze-black-gold palette, "
        "subtle coffee steam motifs and github-style code glyph ornaments in the frame, lower plaque area left blank, "
        f"{COMMON_NEGATIVE}",
    ),
    Job(
        "downatthebottomofthemolehole_avatar_v7_c2_base.png",
        1024,
        1024,
        470102,
        "dark fantasy mole avatar with metal jacket and chain details, bearded glasses-wearing mole-human hybrid look, "
        "coffee cup emblem and coding badge accents, dramatic cave backlight, painterly detail, blank lower ribbon plaque, "
        f"{COMMON_NEGATIVE}",
    ),
    Job(
        "downatthebottomofthemolehole_banner_v7_c1_base.png",
        1536,
        640,
        470103,
        "cinematic wide banner background for a heavy-metal mole brand, tunnel scene with chains and forged steel ornaments, "
        "left-center circular medallion area intentionally clear for portrait cameo, lower-third stone-bronze plaque blank for title, "
        "motorhead mood, coffee aura, github-dev relics, high detail, "
        f"{COMMON_NEGATIVE}",
    ),
    Job(
        "downatthebottomofthemolehole_banner_v7_c2_base.png",
        1536,
        640,
        470104,
        "wide heavy-metal brand banner in underground cavern, ember lighting, chain frame architecture, "
        "clear circular cameo pocket near left-center and blank lower plaque for typography, "
        "subtle coffee and coding motifs, cohesive bronze-black art style, "
        f"{COMMON_NEGATIVE}",
    ),
    Job(
        "rolfmoleman_avatar_v7_c1_base.png",
        1024,
        1024,
        470105,
        "stylized anthropomorphic mole explorer avatar inspired by a bearded man with glasses, "
        "warm expression, thick detailed beard, coffee-forward personality, github hacker aesthetic, "
        "motorhead-inspired gritty metal art direction, blank lower cartouche, "
        f"{COMMON_NEGATIVE}",
    ),
    Job(
        "rolfmoleman_avatar_v7_c2_base.png",
        1024,
        1024,
        470106,
        "steampunk mole inventor avatar, bearded and bespectacled, old mine workshop, brass and iron details, "
        "coffee iconography and repository sigils, strong symmetry, blank lower plaque, "
        f"{COMMON_NEGATIVE}",
    ),
    Job(
        "rolfmoleman_banner_v7_c1_base.png",
        1536,
        640,
        470107,
        "wide cinematic banner for RolfMoleman, moody mine tunnel and chain architecture, "
        "clean circular cameo zone at left-center and blank lower plaque for title, "
        "motorhead grit, coffee-and-code atmosphere, bronze-black-gold lighting, "
        f"{COMMON_NEGATIVE}",
    ),
    Job(
        "rolfmoleman_banner_v7_c2_base.png",
        1536,
        640,
        470108,
        "wide heroic mole banner with forged metal ornaments, explorer vibe, dramatic rim light, "
        "clear cameo pocket at left-center and blank bottom ribbon for text, no embedded lettering, "
        "github engineering and coffee ritual motifs, "
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

    # Retry aggressively and back off when upstream throttles.
    for attempt in range(1, 7):
        try:
            req = Request(url, headers={"User-Agent": "molehole-v7-batch/1.0"})
            with urlopen(req, timeout=150) as resp:
                blob = resp.read()

            if len(blob) < 12_000:
                raise RuntimeError(f"response too small: {len(blob)} bytes")

            out_path.write_bytes(blob)
            print(f"ok   {job.file_name} ({len(blob)} bytes)")
            return
        except Exception as exc:  # noqa: BLE001
            if attempt == 6:
                raise RuntimeError(f"failed {job.file_name}: {exc}") from exc
            sleep_for = (1.8 ** attempt) + random.uniform(0.2, 0.9)
            print(f"retry {attempt} {job.file_name}: {exc} (sleep {sleep_for:.1f}s)")
            time.sleep(sleep_for)


def main() -> None:
    for idx, job in enumerate(JOBS, start=1):
        download_job(job)
        # Request pacing to reduce burst-triggered limiting.
        if idx != len(JOBS):
            time.sleep(random.uniform(1.2, 2.3))


if __name__ == "__main__":
    main()
