"""Shared helpers for Arceus scripts.

All scripts operate on the vault the caller is standing in: paths are
resolved from the current working directory, never from the location of
the scripts themselves. This lets the same scripts work both inside
arceus-core during development and inside a vault, where the core lives
at `_arceus/`.

Stdlib only — a vault must never need a virtualenv or `pip install`.
"""

import re
import unicodedata
from pathlib import Path

# Directories that never contain knowledge notes: engine internals,
# transient areas (_inbox, _artifacts), raw sources, and authoring
# support (templates carry frontmatter that would otherwise be scanned
# as if it were a real note).
SKIP_DIRS = {
    "_arceus",
    "_inbox",
    "_artifacts",
    "sources",
    "templates",
    "prompts",
    "scripts",
    "tests",
    ".git",
    ".github",
    ".claude",
    ".obsidian",
}


def slugify(text: str) -> str:
    """Turn free text into a filesystem-safe lowercase slug."""
    # NFKD + ASCII round-trip strips accents ("Cerinéia" -> "cerineia")
    # so canonical filenames stay portable across filesystems.
    ascii_text = (
        unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    )
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


def parse_frontmatter(text: str):
    """Parse the YAML frontmatter block of a note into a dict.

    Returns None when the file has no frontmatter (README, CLAUDE.md,
    plain indexes), which is how callers tell notes apart from other
    markdown files.

    Deliberately not a full YAML parser: Arceus frontmatter is flat
    `key: value` pairs and inline lists only (see templates/note.md),
    and requiring PyYAML would force every vault to manage Python
    dependencies. Nested YAML is out of scope by design.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    meta = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return meta
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", stripped)
        if not match:
            continue
        key, value = match.group(1), match.group(2)
        # Templates carry authoring hints as trailing comments
        # (`id: ""  # e.g. NOTE-001`); notes are not expected to use
        # ` # ` inside values, so cutting there is safe in practice.
        value = value.split(" #", 1)[0].strip()
        meta[key] = _parse_value(value)

    # No closing `---` means the file only *looks* like it has
    # frontmatter; treat it as not-a-note rather than half-parsing.
    return None


def _parse_value(value: str):
    """Convert a raw frontmatter value into str, int, or list of str."""
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [_strip_quotes(item.strip()) for item in inner.split(",")]
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return _strip_quotes(value)


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def find_notes(root):
    """Yield (path, frontmatter) for every note under the vault root.

    A "note" is any .md file outside SKIP_DIRS whose content starts
    with a well-formed frontmatter block.
    """
    root = Path(root)
    for path in sorted(root.rglob("*.md")):
        parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in parts[:-1]):
            continue
        meta = parse_frontmatter(path.read_text(encoding="utf-8"))
        if meta is not None:
            yield path, meta
