"""Tests for scripts/new_note.py (ID assignment, template rendering, scaffolding)."""

import datetime
import tempfile
import unittest
from pathlib import Path

from fixtures import make_vault, write_note, TEMPLATE  # noqa: F401

import _lib
import new_note


class TestNextId(unittest.TestCase):
    def test_empty_vault_starts_at_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp)
            self.assertEqual(new_note.next_id(root, "COMP"), "COMP-001")

    def test_continues_after_highest_not_after_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp)
            write_note(root, "components", "a", "COMP-002")
            write_note(root, "components", "b", "COMP-009")
            self.assertEqual(new_note.next_id(root, "COMP"), "COMP-010")

    def test_prefixes_are_independent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp)
            write_note(root, "components", "a", "COMP-007")
            self.assertEqual(new_note.next_id(root, "CONC"), "CONC-001")


class TestCreateNote(unittest.TestCase):
    def test_scaffolds_with_filled_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp)
            target = new_note.create_note(root, "concepts", "Golden Record", "CONC")
            self.assertEqual(target, Path(root) / "concepts" / "golden-record.md")
            meta = _lib.parse_frontmatter(target.read_text(encoding="utf-8"))
            today = datetime.date.today().isoformat()
            self.assertEqual(meta["id"], "CONC-001")
            self.assertEqual(meta["title"], "Golden Record")
            self.assertEqual(meta["created_at"], today)
            self.assertEqual(meta["updated_at"], today)
            self.assertEqual(meta["revision"], 1)

    def test_strips_template_comments_but_keeps_body_guidance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp)
            target = new_note.create_note(root, "concepts", "Clean Note", "CONC")
            text = target.read_text(encoding="utf-8")
            self.assertNotIn("e.g.", text.split("---")[1])  # frontmatter is clean
            self.assertIn("<!-- Direct definition. -->", text)  # body hints survive

    def test_falls_back_to_arceus_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp, with_template=False)
            (root / "_arceus" / "templates").mkdir(parents=True)
            (root / "_arceus" / "templates" / "note.md").write_text(TEMPLATE, encoding="utf-8")
            target = new_note.create_note(root, "notes", "From Base", "NOTE")
            self.assertTrue(target.is_file())

    def test_refuses_to_overwrite_existing_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp)
            new_note.create_note(root, "concepts", "Dup", "CONC")
            with self.assertRaises(FileExistsError):
                new_note.create_note(root, "concepts", "Dup", "CONC")

    def test_rejects_title_with_empty_slug(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp)
            with self.assertRaises(ValueError):
                new_note.create_note(root, "concepts", "!!!", "CONC")

    def test_errors_without_any_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp, with_template=False)
            with self.assertRaises(FileNotFoundError):
                new_note.create_note(root, "concepts", "No Template", "CONC")


if __name__ == "__main__":
    unittest.main()
