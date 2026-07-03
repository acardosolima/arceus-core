"""Tests for scripts/_lib.py (slugify, frontmatter parsing, note discovery)."""

import tempfile
import unittest
from pathlib import Path

from fixtures import make_vault, write_note  # noqa: F401  (sets up sys.path)

import _lib


class TestSlugify(unittest.TestCase):
    def test_lowercases_and_hyphenates(self):
        self.assertEqual(_lib.slugify("Meeting Notes 02/07"), "meeting-notes-02-07")

    def test_strips_accents(self):
        self.assertEqual(_lib.slugify("Cerva de Cerinéia"), "cerva-de-cerineia")

    def test_collapses_symbol_runs_and_trims(self):
        self.assertEqual(_lib.slugify("  a -- b!! "), "a-b")

    def test_non_ascii_only_input_gives_empty_slug(self):
        self.assertEqual(_lib.slugify("日本語"), "")


class TestParseFrontmatter(unittest.TestCase):
    def test_returns_none_without_frontmatter(self):
        self.assertIsNone(_lib.parse_frontmatter("# Just a heading\n\ntext"))

    def test_returns_none_without_closing_fence(self):
        self.assertIsNone(_lib.parse_frontmatter('---\nid: "X-001"\n\nbody'))

    def test_parses_strings_ints_and_lists(self):
        meta = _lib.parse_frontmatter(
            '---\nid: "COMP-001"\nrevision: 3\ntags: [foundry, "legal"]\nrelated: []\n---\nbody'
        )
        self.assertEqual(meta["id"], "COMP-001")
        self.assertEqual(meta["revision"], 3)
        self.assertEqual(meta["tags"], ["foundry", "legal"])
        self.assertEqual(meta["related"], [])

    def test_ignores_template_trailing_comments(self):
        meta = _lib.parse_frontmatter('---\nid: ""              # e.g.: NOTE-001\n---\n')
        self.assertEqual(meta["id"], "")

    def test_skips_comment_only_lines(self):
        meta = _lib.parse_frontmatter("---\n# Connections\nsources: []\n---\n")
        self.assertEqual(meta, {"sources": []})


class TestFindNotes(unittest.TestCase):
    def test_finds_notes_and_skips_engine_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp)
            write_note(root, "components", "alpha", "COMP-001")
            # Template has frontmatter but must not be discovered as a note.
            (root / "README.md").write_text("# Vault\n", encoding="utf-8")
            found = {path.name for path, _ in _lib.find_notes(root)}
            self.assertEqual(found, {"alpha.md"})

    def test_root_level_note_is_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp, with_template=False)
            write_note(root, ".", "loose", "NOTE-001")
            found = {path.name for path, _ in _lib.find_notes(root)}
            self.assertEqual(found, {"loose.md"})


if __name__ == "__main__":
    unittest.main()
