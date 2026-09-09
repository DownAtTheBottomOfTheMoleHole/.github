"""Offline regression checks for the AI asset quality gate."""

import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS_DIR))
from sync_ai_assets import sync
from validate_ai_assets import inspect_asset
sys.path.pop(0)

class AssetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.skill = self.root / ".github/skills/example/SKILL.md"
        self.skill.parent.mkdir(parents=True)
        self.skill.write_text(
            "---\nname: example\ndescription: An example skill\n---\n\n# Example\n"
        )
        self.agent = self.root / ".github/agents/example.agent.md"
        self.agent.parent.mkdir(parents=True)
        self.agent.write_text(
            "---\nname: example\ndescription: An example agent\n---\n\n# Example\n"
        )

    def test_discovery_sync_detects_drift_and_preserves_canonical_content(self):
        self.assertEqual(len(sync(self.root, check=True)), 2)
        self.assertFalse((self.root / "agents").exists())
        self.assertEqual(sync(self.root), [])
        self.assertEqual(sync(self.root, check=True), [])
        link = self.root / ".agents/skills/example"
        self.assertTrue(link.is_symlink())
        self.assertEqual((link / "SKILL.md").read_bytes(), self.skill.read_bytes())
        self.agent.write_text(self.agent.read_text() + "\nChanged instructions.\n")
        self.assertIn("Stale organisation agent", sync(self.root, check=True)[0])
        self.assertEqual(sync(self.root), [])
        self.assertEqual(
            (self.root / "agents/example.agent.md").read_bytes(),
            self.agent.read_bytes(),
        )

    def test_generated_agent_links_resolve_after_relocation(self):
        with self.agent.open("a") as stream:
            stream.write(
                "\n[Skill](../skills/example/SKILL.md)\n"
                '[Titled](../skills/example/SKILL.md "details")\n'
                "[Angled](<../skills/example/SKILL.md>)\n"
                '[Angled titled](<../skills/example/SKILL.md> "details")\n'
                "[Reference][skill-ref]\n"
                "[skill-ref]: ../skills/example/SKILL.md\n"
                "[Titled reference][skill-ref-titled]\n"
                '[skill-ref-titled]: <../skills/example/SKILL.md> "details"\n'
                "```md\n[Example](../skills/example/SKILL.md)\n```\n"
            )
        self.assertEqual(sync(self.root), [])
        published = self.root / "agents/example.agent.md"
        self.assertIn(
            "[Skill](../.github/skills/example/SKILL.md)", published.read_text()
        )
        self.assertIn(
            '[Titled](../.github/skills/example/SKILL.md "details")',
            published.read_text(),
        )
        self.assertIn(
            "[Angled](<../.github/skills/example/SKILL.md>)", published.read_text()
        )
        self.assertIn(
            '[Angled titled](<../.github/skills/example/SKILL.md> "details")',
            published.read_text(),
        )
        self.assertIn(
            "[skill-ref]: ../.github/skills/example/SKILL.md", published.read_text()
        )
        self.assertIn(
            '[skill-ref-titled]: <../.github/skills/example/SKILL.md> "details"',
            published.read_text(),
        )
        self.assertIn(
            "```md\n[Example](../skills/example/SKILL.md)\n```", published.read_text()
        )
        self.assertEqual(inspect_asset(published, self.root), [])

    def test_symlinked_discovery_parent_is_not_followed(self):
        outside = self.root / "unrelated"
        outside.mkdir()
        (self.root / ".agents").symlink_to(outside, target_is_directory=True)
        self.assertTrue(
            any("symlinked discovery directory" in e for e in sync(self.root))
        )
        self.assertEqual(list(outside.iterdir()), [])

    def test_non_directory_discovery_parent_is_rejected(self):
        (self.root / ".agents").write_text("not a directory")
        self.assertTrue(
            any("unexpected discovery directory" in e for e in sync(self.root))
        )

    def test_unexpected_skill_is_not_overwritten(self):
        target = self.root / ".agents/skills/example"
        target.mkdir(parents=True)
        personal = target / "SKILL.md"
        personal.write_text("Existing local skill")
        self.assertTrue(any("Refusing existing" in e for e in sync(self.root)))
        self.assertEqual(personal.read_text(), "Existing local skill")

    def test_wrong_and_dangling_links_fail(self):
        target = self.root / ".agents/skills/example"
        target.parent.mkdir(parents=True)
        target.symlink_to("missing")
        self.assertTrue(
            any("Unexpected skill link" in e for e in sync(self.root, check=True))
        )

    def test_orphan_assets_are_reported_without_deletion(self):
        sync(self.root)
        self.agent.unlink()
        self.skill.unlink()
        result = sync(self.root, check=True)
        self.assertTrue(any("Orphan organisation agent" in e for e in result))
        self.assertTrue(any("Orphan skill discovery path" in e for e in result))
        self.assertTrue((self.root / "agents/example.agent.md").exists())

    def test_valid_relative_link_and_code_example(self):
        (self.skill.parent / "reference.md").write_text("# Reference\n")
        (self.skill.parent / "user guide.md").write_text("# Guide\n")
        (self.skill.parent / "guide(v2).md").write_text("# Versioned guide\n")
        (self.skill.parent / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        with self.skill.open("a") as stream:
            stream.write(
                "\n[Reference](reference.md)\n"
                '[Titled](reference.md "details")\n'
                "[Spaced](<user guide.md>)\n"
                "\n[Parenthesized](guide(v2).md)\n"
                "\n![Diagram](image.png)\n"
                '\n   ```md\n[Example](not-a-real-file.md)\n````\n'
            )
        self.assertEqual(inspect_asset(self.skill, self.root), [])

    def test_broken_link_is_reported(self):
        with self.skill.open("a") as stream:
            stream.write(
                '\n[Missing prompt](../../prompts/missing.prompt.md "details")\n'
                "\n[Missing spaced](<../../prompts/missing prompt.prompt.md>)\n"
                "\n![Missing image](missing-image.png)\n"
                "\n[Missing ref][missing-ref]\n"
                "[missing-ref]: ../../prompts/missing.prompt.md\n"
            )
        self.assertTrue(
            any(
                "missing or outside-repository link" in e
                for e in inspect_asset(self.skill, self.root)
            )
        )

    def test_invalid_metadata_is_reported(self):
        for header in (
            "name: wrong\ndescription: Example",
            "name: example\nname: duplicate\ndescription: Example",
            "name: example\ndescription: [not, text]",
            "name: example\ndescription: Example\ntools: 4",
        ):
            with self.subTest(header=header):
                self.skill.write_text("---\n" + header + "\n---\n# Example\n")
                self.assertTrue(inspect_asset(self.skill, self.root))


if __name__ == "__main__":
    unittest.main()
