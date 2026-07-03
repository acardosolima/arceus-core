"""Tests for scripts/ingest_move.py (canonical rename, log, guardrails)."""

import datetime
import tempfile
import unittest
from pathlib import Path

from fixtures import make_vault  # noqa: F401

import ingest_move


def drop_in_inbox(root, name, content="raw"):
    path = Path(root) / "_inbox" / name
    path.write_text(content, encoding="utf-8")
    return path


class TestMoveToSources(unittest.TestCase):
    def test_moves_with_canonical_name_and_logs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp)
            dropped = drop_in_inbox(root, "Reunião 02-07.txt", "transcript body")
            target = ingest_move.move_to_sources(
                root, dropped, "Reunião refinamento", "meeting transcript", "COMP-003"
            )
            today = datetime.date.today().isoformat()
            self.assertEqual(target.name, f"{today}_reuniao-refinamento.txt")
            self.assertFalse(dropped.exists())
            self.assertEqual(target.read_text(encoding="utf-8"), "transcript body")

            log = (root / "sources" / "_log.md").read_text(encoding="utf-8")
            self.assertIn("| Date | Original | Canonical |", log)
            self.assertIn(f"| {today} | Reunião 02-07.txt | {target.name} "
                          f"| meeting transcript | COMP-003 |", log)

    def test_log_appends_without_duplicating_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp)
            ingest_move.move_to_sources(root, drop_in_inbox(root, "a.txt"), "first", "doc")
            ingest_move.move_to_sources(root, drop_in_inbox(root, "b.txt"), "second", "doc")
            log = (root / "sources" / "_log.md").read_text(encoding="utf-8")
            self.assertEqual(log.count("# Ingestion Log"), 1)
            self.assertEqual(log.count("| doc |"), 2)

    def test_rejects_file_outside_inbox(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp)
            stray = Path(root) / "stray.txt"
            stray.write_text("x", encoding="utf-8")
            with self.assertRaises(ValueError):
                ingest_move.move_to_sources(root, stray, "stray", "doc")
            self.assertTrue(stray.exists())  # nothing was moved

    def test_rejects_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp)
            with self.assertRaises(FileNotFoundError):
                ingest_move.move_to_sources(root, Path(root) / "_inbox" / "ghost.txt", "g", "doc")

    def test_same_day_same_description_collision_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp)
            ingest_move.move_to_sources(root, drop_in_inbox(root, "a.txt"), "daily sync", "doc")
            second = drop_in_inbox(root, "b.txt")
            with self.assertRaises(FileExistsError):
                ingest_move.move_to_sources(root, second, "daily sync", "doc")
            self.assertTrue(second.exists())  # inbox file untouched on failure

    def test_pipes_in_fields_cannot_break_the_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_vault(tmp)
            ingest_move.move_to_sources(
                root, drop_in_inbox(root, "a.txt"), "sync", "doc", notes="COMP-001|COMP-002"
            )
            log = (root / "sources" / "_log.md").read_text(encoding="utf-8")
            self.assertIn("COMP-001/COMP-002", log)


if __name__ == "__main__":
    unittest.main()
