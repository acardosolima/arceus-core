"""Tests for scripts/validate.py (required fields, dates, revision, unique ids)."""

import tempfile
import unittest

from fixtures import make_vault, write_note  # noqa: F401

import validate


class TestValidateVault(unittest.TestCase):
    def test_valid_vault_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp)
            write_note(root, "components", "a", "COMP-001")
            write_note(root, "concepts", "b", "CONC-001")
            errors, warnings = validate.validate_vault(root)
            self.assertEqual(errors, [])
            self.assertEqual(warnings, [])

    def test_missing_and_empty_required_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp)
            write_note(root, "components", "a", "")  # empty id
            errors, _ = validate.validate_vault(root)
            self.assertTrue(any("missing or empty `id`" in e for e in errors))

    def test_bad_date_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp)
            path = write_note(root, "components", "a", "COMP-001")
            text = path.read_text(encoding="utf-8").replace('"2026-07-01"', '"01/07/2026"')
            path.write_text(text, encoding="utf-8")
            errors, _ = validate.validate_vault(root)
            self.assertTrue(any("expected YYYY-MM-DD" in e for e in errors))

    def test_duplicate_ids_across_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp)
            write_note(root, "components", "a", "COMP-001")
            write_note(root, "concepts", "b", "COMP-001")
            errors, _ = validate.validate_vault(root)
            self.assertTrue(any("duplicate id `COMP-001`" in e for e in errors))

    def test_legacy_schema_version_warns_but_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp)
            write_note(root, "components", "a", "COMP-001", revision="schema_version: 2")
            errors, warnings = validate.validate_vault(root)
            self.assertEqual(errors, [])
            self.assertTrue(any("`schema_version` is deprecated" in w for w in warnings))

    def test_missing_revision_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp)
            write_note(root, "components", "a", "COMP-001", revision="sources: []")
            errors, _ = validate.validate_vault(root)
            self.assertTrue(any("missing `revision`" in e for e in errors))

    def test_non_integer_revision_is_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp)
            write_note(root, "components", "a", "COMP-001", revision='revision: "one"')
            errors, _ = validate.validate_vault(root)
            self.assertTrue(any("expected an integer >= 1" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
