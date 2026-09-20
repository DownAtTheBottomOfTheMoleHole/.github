"""Regression checks for canonical branding assets."""

from pathlib import Path
import unittest

from PIL import Image

from tools.render_brand_assets import BANNERS


ROOT = Path(__file__).resolve().parents[1]


class BrandAssetTests(unittest.TestCase):
    def assert_png(self, relative_path: str, size: tuple[int, int]) -> None:
        path = ROOT / relative_path
        self.assertTrue(path.is_file(), f"Missing asset: {relative_path}")
        with Image.open(path) as image:
            self.assertEqual(image.size, size)
            self.assertEqual(image.format, "PNG")

    def test_candidate_20_source_set(self) -> None:
        self.assert_png(
            "assets/banners/downatthebottomofthemolehole_banner_20.png",
            (1536, 1024),
        )
        self.assert_png(
            "assets/avatars/downatthebottomofthemolehole_avatar_20.png",
            (1024, 1024),
        )
        github_avatar = "assets/avatars/downatthebottomofthemolehole_avatar_20_github.png"
        self.assert_png(github_avatar, (512, 512))
        self.assertLess((ROOT / github_avatar).stat().st_size, 1024 * 1024)
        self.assert_png(
            "assets/logos/downatthebottomofthemolehole_logo_20.png",
            (1024, 1024),
        )

    def test_every_registered_banner_exists(self) -> None:
        for slug in BANNERS:
            with self.subTest(slug=slug):
                self.assert_png(
                    f"assets/banners/repositories/{slug}.png",
                    (1983, 793),
                )


if __name__ == "__main__":
    unittest.main()
