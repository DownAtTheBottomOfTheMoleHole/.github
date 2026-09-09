"""Check AI asset metadata, local Markdown links, and discovery drift offline."""

import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml
from sync_ai_assets import sync


class UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate metadata keys rather than silently taking the last."""


def unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if key in result:
            raise ValueError(f"duplicate frontmatter key: {key}")
        result[key] = loader.construct_object(value_node)
    return result


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping
)

INLINE_LINK_RE = re.compile(
    r"""(?<!!)\[[^\]\n]+\]\((<[^>\n]+>|[^\s)]+)"""
    r"""(\s+(?:"[^"\n]*"|'[^'\n]*'|\([^()\n]*\)))?\)"""
)
REFERENCE_LINK_RE = re.compile(
    r"""^ {0,3}\[[^\]\n]+\]:\s*(<[^>\n]+>|[^\s]+)"""
    r"""(\s+(?:"[^"\n]*"|'[^'\n]*'|\([^()\n]*\)))?(?=\s*$)""",
    re.MULTILINE,
)


def strip_fenced_code(content: str) -> str:
    """Remove fenced Markdown code blocks from content."""

    body = []
    fence = None
    for line in content.splitlines(keepends=True):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            if (
                marker
                and marker.group(1)[0] == fence[0]
                and len(marker.group(1)) >= len(fence)
                and not marker.group(2).strip()
            ):
                fence = None
            continue
        if marker:
            fence = marker.group(1)
            continue
        body.append(line)
    return "".join(body)


def inspect_asset(path: Path, root: Path) -> list[str]:
    errors = []
    content = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", content, re.DOTALL)
    if not match:
        return [f"{path.relative_to(root)}: missing YAML frontmatter"]
    try:
        metadata = yaml.load(match.group(1), Loader=UniqueKeyLoader)
        if not isinstance(metadata, dict):
            raise TypeError("frontmatter must be a mapping")
        if (
            not isinstance(metadata.get("description"), str)
            or not metadata["description"].strip()
        ):
            raise ValueError("a nonempty description is required")
        if path.name == "SKILL.md":
            name = metadata.get("name", "")
            if not isinstance(name, str) or not re.fullmatch(
                r"[a-z0-9]+(?:-[a-z0-9]+)*", name
            ):
                raise ValueError(
                    "skill name must use lowercase words separated by hyphens"
                )
            if name != path.parent.name or len(name) > 64:
                raise ValueError(
                    "skill name must match its directory and fit 64 characters"
                )
            if len(metadata["description"]) > 1024:
                raise ValueError("skill description exceeds 1024 characters")
        if "tools" in metadata and not isinstance(metadata["tools"], (list, str)):
            raise ValueError("tools must be a list or string")
        if "applyTo" in metadata and not isinstance(metadata["applyTo"], str):
            raise ValueError("applyTo must be a glob string")
        if path.name.endswith(".agent.md") and len(content[match.end() :]) > 30000:
            raise ValueError("agent body exceeds GitHub 30000-character limit")
    except (ValueError, TypeError, yaml.YAMLError) as exc:
        errors.append(f"{path.relative_to(root)}: {exc}")
    # Ignore code examples; validate explicit relative Markdown links, not external URLs.
    body = strip_fenced_code(content[match.end() :])
    for link in INLINE_LINK_RE.finditer(body):
        target = link.group(1)
        parts = urlsplit(target.strip("<>"))
        if parts.scheme or parts.netloc or not parts.path or parts.path.startswith("/"):
            continue
        local = (path.parent / unquote(parts.path)).resolve()
        if not local.is_relative_to(root.resolve()) or not local.exists():
            errors.append(
                f"{path.relative_to(root)}: missing or outside-repository link {target}"
            )
    for link in REFERENCE_LINK_RE.finditer(body):
        target = link.group(1)
        parts = urlsplit(target.strip("<>"))
        if parts.scheme or parts.netloc or not parts.path or parts.path.startswith("/"):
            continue
        local = (path.parent / unquote(parts.path)).resolve()
        if not local.is_relative_to(root.resolve()) or not local.exists():
            errors.append(
                f"{path.relative_to(root)}: missing or outside-repository link {target}"
            )
    return errors


def validate(root: Path) -> list[str]:
    patterns = (
        "agents/*.agent.md",
        "prompts/*.prompt.md",
        "instructions/*.instructions.md",
        "skills/*/SKILL.md",
    )
    assets = sorted(
        {path for pattern in patterns for path in (root / ".github").glob(pattern)}
    )
    if not assets:
        return ["No canonical AI assets found under .github/"]
    assets += sorted((root / "agents").glob("*.agent.md"))
    return [error for path in assets for error in inspect_asset(path, root)] + sync(
        root, check=True
    )


if __name__ == "__main__":
    findings = validate(Path(__file__).resolve().parents[1])
    print(
        "\n".join(findings)
        if findings
        else "AI asset metadata, links, and discovery checks passed."
    )
    raise SystemExit(bool(findings))
