"""Publish the canonical AI assets into client discovery locations."""

import argparse
import os
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


def render_agent(source: Path, target: Path) -> bytes:
    """Keep companion links valid when publishing, preserving fenced examples."""

    def relocate(match):
        destination = match.group(2)
        angled = destination.startswith("<") and destination.endswith(">")
        parts = urlsplit(destination[1:-1] if angled else destination)
        if parts.scheme or parts.netloc or not parts.path or parts.path.startswith("/"):
            return match.group(0)
        relative = Path(os.path.relpath(source.parent / parts.path, target.parent)).as_posix()
        destination = urlunsplit(parts._replace(path=relative))
        if angled:
            destination = "<" + destination + ">"
        return match.group(1) + destination + ")"

    rendered = []
    fence = None
    for line in source.read_text(encoding="utf-8").splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            rendered.append(line)
            if (
                marker
                and marker.group(1)[0] == fence[0]
                and len(marker.group(1)) >= len(fence)
                and not marker.group(2).strip()
            ):
                fence = None
        elif marker:
            fence = marker.group(1)
            rendered.append(line)
        else:
            rendered.append(
                re.sub(r"(\[[^\]\n]+\]\()(<[^>\n]+>|[^\s)]+)\)", relocate, line)
            )
    return "".join(rendered).encode("utf-8")


def sync(root: Path, check: bool = False) -> list[str]:
    """Return drift/errors; never replace an unexpected user-owned symlink/directory."""
    errors = []
    canonical = root / ".github"
    for directory in (root / "agents", root / ".agents", root / ".agents/skills"):
        if directory.is_symlink():
            return [
                f"Refusing symlinked discovery directory: {directory.relative_to(root)}"
            ]
    for source in sorted((canonical / "agents").glob("*.agent.md")):
        target = root / "agents" / source.name
        if target.is_symlink() or (target.exists() and not target.is_file()):
            errors.append(
                f"Refusing unexpected discovery path: {target.relative_to(root)}"
            )
        elif not target.exists() or target.read_bytes() != render_agent(source, target):
            if check:
                errors.append(f"Stale organisation agent: {target.relative_to(root)}")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(render_agent(source, target))
    for target in sorted((root / "agents").glob("*.agent.md")):
        if not (canonical / "agents" / target.name).exists():
            errors.append(
                f"Orphan organisation agent; remove explicitly: {target.relative_to(root)}"
            )
    for source in sorted((canonical / "skills").glob("*/SKILL.md")):
        target = root / ".agents" / "skills" / source.parent.name
        expected = Path("../../.github/skills") / source.parent.name
        if target.is_symlink():
            if target.readlink() != expected or not target.is_dir():
                errors.append(f"Unexpected skill link: {target.relative_to(root)}")
        elif target.exists():
            errors.append(
                f"Refusing existing skill directory: {target.relative_to(root)}"
            )
        elif check:
            errors.append(f"Missing Codex skill: {target.relative_to(root)}")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(expected, target_is_directory=True)
    for target in sorted((root / ".agents" / "skills").glob("*")):
        if not (canonical / "skills" / target.name / "SKILL.md").is_file():
            errors.append(f"Orphan skill discovery path: {target.relative_to(root)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="Check without changing files"
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    errors = sync(root, args.check)
    if errors:
        print("\n".join(errors))
        return 1
    print("AI discovery assets are in sync.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
