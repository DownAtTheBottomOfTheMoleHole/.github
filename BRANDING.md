# Down At The Bottom Of The Mole Hole branding

This repository is the canonical source for organisation branding used across GitHub.
The visual system combines a dark underground setting with bronze, gold and a small electric-blue
accent. Repository banners use the same source artwork and exact Stonehenge display typeface.

## Canonical assets

| Role | Asset |
| --- | --- |
| Source banner | [`assets/banners/downatthebottomofthemolehole_banner_20.png`](assets/banners/downatthebottomofthemolehole_banner_20.png) |
| Organisation avatar | [`assets/avatars/downatthebottomofthemolehole_avatar_20.png`](assets/avatars/downatthebottomofthemolehole_avatar_20.png) |
| Organisation logo | [`assets/logos/downatthebottomofthemolehole_logo_20.png`](assets/logos/downatthebottomofthemolehole_logo_20.png) |
| Organisation profile banner | [`assets/banners/repositories/downatthebottomofthemolehole.png`](assets/banners/repositories/downatthebottomofthemolehole.png) |
| Repository banners | [`assets/banners/repositories/`](assets/banners/repositories/) |

The candidate-20 medallion is the canonical logo. It shares the mole, cave, keyboard, circuitry,
black and bronze motifs used by the avatar and banner.

## Repository banner standard

- Use a generated banner from `assets/banners/repositories/` at the top of each repository README.
- Link to the central raw asset rather than copying the PNG into every repository.
- Use the repository name as the main display text and a short purpose statement beneath it.
- Keep the banner as the single hero; do not place a redundant logo block immediately below it.
- Product-specific branding may follow the organisation banner. Rachel's Bakes keeps its own logo,
  fonts, palette and customer-facing assets unchanged.

## Typography

All rendered banner text uses the exact Stonehenge typeface. The approved font file has SHA-256:

```text
ce21460833ed97837924bdaaa1455530ad330562dd73e80f0242fa0d4b879810
```

The font file is not committed. Obtain `stonehen.ttf`, then pass it explicitly to the renderer.
The renderer validates both the family name and digest and does not fall back to another font.

## Regenerating banners

```sh
python3 -m pip install -r tools/requirements-dev.txt
python3 tools/render_brand_assets.py --font /path/to/stonehen.ttf
python3 -m unittest discover -s tests -v
```

Edit the banner registry in `tools/render_brand_assets.py` when a repository is added or renamed.

## Asset rights

All images in this repository are proprietary and copyright © 2026
DownAtTheBottomOfTheMoleHole. They may not be reproduced, modified, distributed or used in
derivative works without prior written permission.
