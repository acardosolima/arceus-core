"""Scaffold a new note from the vault's template with the next free ID.

Usage:
    python3 _arceus/scripts/new_note.py <directory> <title> [--prefix NOTE]

Creates `<directory>/<slugified-title>.md` from the vault template
(falling back to the base template in `_arceus/`), with `id`, `title`
and dates filled in. Prints the created path on stdout.

This removes two failure modes of letting an LLM scaffold notes:
guessed (possibly colliding) IDs, and frontmatter drift from the
template.
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

from _lib import find_notes, slugify


def next_id(root, prefix: str) -> str:
    """Return the next free `PREFIX-NNN` id by scanning existing notes.

    Scanning beats a counter file: parallel branches can't corrupt it on
    merge, and manually created notes are respected automatically.
    """
    highest = 0
    for _, meta in find_notes(root):
        match = re.fullmatch(rf"{re.escape(prefix)}-(\d+)", str(meta.get("id", "")))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{prefix}-{highest + 1:03d}"


def resolve_template(root) -> Path:
    """Pick the note template: the vault's own extends (wins over) the base."""
    root = Path(root)
    for candidate in (root / "templates" / "note.md", root / "_arceus" / "templates" / "note.md"):
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "no note template found (looked in templates/ and _arceus/templates/)"
    )


def render(template_text: str, values: dict) -> str:
    """Fill frontmatter fields and strip authoring comments.

    Trailing `# ...` comments in the template frontmatter are hints for
    humans editing the template, not note content — a scaffolded note
    must start clean. Body HTML comments are kept: they guide whoever
    (or whatever) fills the sections in.
    """
    out = []
    fence_count = 0
    for line in template_text.splitlines():
        if line.strip() == "---" and fence_count < 2:
            fence_count += 1
            out.append(line)
            continue
        if fence_count != 1:
            out.append(line)
            continue

        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):", line)
        if not match:
            # Frontmatter comment/blank lines are template organization
            # (e.g. `# Connections`); keep them for readability.
            out.append(line)
            continue
        key = match.group(1)
        if key in values:
            value = values[key]
            rendered = value if isinstance(value, int) else f'"{value}"'
            out.append(f"{key}: {rendered}")
        else:
            out.append(re.sub(r"\s+#.*$", "", line))
    return "\n".join(out) + "\n"


def create_note(root, directory: str, title: str, prefix: str) -> Path:
    root = Path(root)
    template = resolve_template(root)

    slug = slugify(title)
    if not slug:
        raise ValueError(f"title {title!r} produces an empty filename")
    target = root / directory / f"{slug}.md"
    if target.exists():
        raise FileExistsError(f"{target} already exists — merge into it instead")

    today = datetime.date.today().isoformat()
    values = {
        "id": next_id(root, prefix),
        "title": title,
        "created_at": today,
        "updated_at": today,
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render(template.read_text(encoding="utf-8"), values), encoding="utf-8")
    return target


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a new note from the vault's template with the next free ID."
    )
    parser.add_argument("directory", help="vault folder for the note, e.g. components")
    parser.add_argument("title", help="note title (filename is derived from it)")
    parser.add_argument("--prefix", default="NOTE", help="id prefix, e.g. COMP (default: NOTE)")
    args = parser.parse_args(argv)

    try:
        target = create_note(Path.cwd(), args.directory, args.title, args.prefix)
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
