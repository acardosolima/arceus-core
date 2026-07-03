"""Test fixtures: build throwaway vaults on disk.

Scripts resolve everything from a vault root, so tests exercise them
against real temporary directories instead of mocks — the filesystem
behavior (moves, collisions, encoding) is exactly what's under test.
"""

import sys
from pathlib import Path

# Tests import the scripts directly (`import validate`), so the scripts
# directory must be importable regardless of where unittest is run from.
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

TEMPLATE = '''---
id: ""              # Unique identifier. e.g.: NOTE-001, COMP-042
title: ""           # Note title
tags: []            # Free-form tags
created_at: ""      # ISO 8601. e.g.: 2026-06-28
updated_at: ""      # Updated on every MERGE
revision: 1         # Increments on every MERGE

# Connections
sources: []
related: []
---

## What it is
<!-- Direct definition. -->

## Details
'''


def make_vault(root, with_template=True):
    """Lay out the minimal vault structure inside `root`."""
    root = Path(root)
    (root / "_inbox").mkdir()
    (root / "sources").mkdir()
    if with_template:
        (root / "templates").mkdir()
        (root / "templates" / "note.md").write_text(TEMPLATE, encoding="utf-8")
    return root


def write_note(root, folder, name, note_id, title="Some Note", revision="revision: 1"):
    """Write a minimal valid note; `revision` is a raw line for override tests."""
    path = Path(root) / folder / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'''---
id: "{note_id}"
title: "{title}"
tags: []
created_at: "2026-07-01"
updated_at: "2026-07-01"
{revision}
sources: []
related: []
---

## What it is
Something.
''',
        encoding="utf-8",
    )
    return path
