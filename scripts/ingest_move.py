"""Move a processed file from _inbox/ to sources/ and log the ingestion.

Usage:
    python3 _arceus/scripts/ingest_move.py <file> <description> --type TYPE [--notes "..."]

Renames the file to the canonical `YYYY-MM-DD_<slug>.<ext>` form,
moves it into `sources/`, and appends a row to `sources/_log.md`
(created on first use). Prints the destination path on stdout.

This is the mechanical tail of the ingestion workflow
(prompts/ingest.md): the LLM decides *what* the file is and *which*
notes to write; moving, renaming and logging are deterministic and
belong here.
"""

import argparse
import datetime
import shutil
import sys
from pathlib import Path

from _lib import slugify

LOG_NAME = "_log.md"
LOG_HEADER = (
    "# Ingestion Log\n"
    "\n"
    "One row per file processed from `_inbox/`.\n"
    "\n"
    "| Date | Original | Canonical | Type | Notes created/updated |\n"
    "|------|----------|-----------|------|-----------------------|\n"
)


def canonical_name(description: str, extension: str, date: str) -> str:
    slug = slugify(description)
    if not slug:
        raise ValueError(f"description {description!r} produces an empty slug")
    return f"{date}_{slug}{extension}"


def move_to_sources(root, file_path, description, source_type, notes="") -> Path:
    root = Path(root)
    source = Path(file_path)
    if not source.is_file():
        raise FileNotFoundError(f"{source} does not exist or is not a file")
    # Only _inbox/ files are eligible: moving arbitrary vault files
    # through this script would silently untrack committed content
    # (sources/ is tracked, but the move away from the origin isn't
    # something this script should ever do to a note).
    if source.resolve().parent != (root / "_inbox").resolve():
        raise ValueError(f"{source} is not inside {root / '_inbox'}")

    today = datetime.date.today().isoformat()
    target = root / "sources" / canonical_name(description, source.suffix, today)
    if target.exists():
        # Failing (instead of auto-suffixing) forces a more specific
        # description, which is what the log needs to stay useful.
        raise FileExistsError(f"{target} already exists — use a more specific description")

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(target))
    _append_log(root, today, source.name, target.name, source_type, notes)
    return target


def _append_log(root, date, original, canonical, source_type, notes):
    log = root / "sources" / LOG_NAME
    if not log.exists():
        log.write_text(LOG_HEADER, encoding="utf-8")
    cells = [date, original, canonical, source_type, notes or "—"]
    # Pipes inside a cell would break the markdown table structure.
    row = "| " + " | ".join(cell.replace("|", "/") for cell in cells) + " |\n"
    with log.open("a", encoding="utf-8") as handle:
        handle.write(row)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Move a processed file from _inbox/ to sources/ and log the ingestion."
    )
    parser.add_argument("file", help="path to the file in _inbox/")
    parser.add_argument("description", help="short description for the canonical name")
    parser.add_argument(
        "--type",
        required=True,
        dest="source_type",
        help="source type, e.g. 'meeting transcript', 'JSON export'",
    )
    parser.add_argument("--notes", default="", help="notes created/updated, for the log")
    args = parser.parse_args(argv)

    try:
        target = move_to_sources(
            Path.cwd(), args.file, args.description, args.source_type, args.notes
        )
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(target)
    return 0


if __name__ == "__main__":
    sys.exit(main())
