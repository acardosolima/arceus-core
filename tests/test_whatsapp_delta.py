"""Tests for scripts/whatsapp_delta.py (parsing, anchoring, CLI contract)."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

import fixtures  # noqa: F401  # side effect: puts scripts/ on sys.path

import whatsapp_delta
from whatsapp_delta import AnchorNotFound, find_boundary, parse_export


def msg(ts, sender, text):
    """One export message as raw lines (multiline text = continuation lines)."""
    if sender is None:
        return f"{ts} - {text}\n"
    return f"{ts} - {sender}: {text}\n"


BASE = (
    msg("6/23/26, 10:40", None, "Messages and calls are end-to-end encrypted.")
    + msg("6/23/26, 11:34", "Ana", "Bom dia!")
    + msg("6/23/26, 12:56", "Fernando", "vai ter a reuniao 13h?")
)
EXTRA = (
    msg("6/24/26, 09:00", "Ana", "Segue o link do workshop")
    + msg("6/24/26, 09:01", "Fernando", "Blz")
)


def keys(text):
    return [m.key for m in parse_export(text)]


def run_main(argv):
    """Run main() capturing stdout/stderr; returns (exit_code, out, err)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = whatsapp_delta.main(argv)
    return code, out.getvalue(), err.getvalue()


def write_exports(tmp, old_text, new_text):
    old = Path(tmp) / "old.txt"
    new = Path(tmp) / "new.txt"
    old.write_text(old_text, encoding="utf-8")
    new.write_text(new_text, encoding="utf-8")
    return old, new


class TestParseExport(unittest.TestCase):
    def test_groups_continuation_lines(self):
        text = msg("6/23/26, 11:34", "Ana", "Bom dia!\nSegue o link.\nhttps://x")
        messages = parse_export(text)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].key, ("6/23/26, 11:34", "Ana"))
        self.assertEqual("".join(messages[0].lines), text)

    def test_senderless_system_messages_have_none_sender(self):
        messages = parse_export(BASE)
        self.assertIsNone(messages[0].key[1])
        self.assertEqual(messages[1].key, ("6/23/26, 11:34", "Ana"))

    def test_colon_inside_system_text_is_deterministic(self):
        # `created group "AGU <> VF: ..."` has no real sender, but contains
        # ": " - the split yields a garbage sender, which is fine as long as
        # both parses of the same chat produce the same key.
        line = msg("4/6/26, 11:36", None, 'Gerusa created group "AGU <> VF: Grupo"')
        self.assertEqual(keys(line), keys(line))
        self.assertEqual(parse_export(line)[0].key[1], 'Gerusa created group "AGU <> VF')

    def test_rejects_non_whatsapp_text(self):
        with self.assertRaises(ValueError):
            parse_export("just some\nrandom notes\n")


class TestFindBoundary(unittest.TestCase):
    def test_prefix_fast_path(self):
        old, new = keys(BASE), keys(BASE + EXTRA)
        boundary, mode, warnings = find_boundary(old, new)
        self.assertEqual((boundary, mode, warnings), (len(old), "prefix", []))

    def test_tail_fallback_after_midfile_deletion(self):
        old_text = BASE + msg("6/23/26, 14:00", "Ana", "msg extra") + EXTRA
        # New export lost BASE's second message ("deleted for me" upstream).
        new_text = (
            BASE.replace(msg("6/23/26, 11:34", "Ana", "Bom dia!"), "")
            + msg("6/23/26, 14:00", "Ana", "msg extra")
            + EXTRA
            + msg("6/25/26, 08:00", "Fernando", "novidade")
        )
        old, new = keys(old_text), keys(new_text)
        boundary, mode, _ = find_boundary(old, new)
        self.assertEqual(boundary, len(new) - 1)
        self.assertTrue(mode.startswith("tail:"), mode)

    def test_ambiguous_tail_prefers_expected_position(self):
        burst = msg("6/23/26, 16:37", "Fernando", "a") * 3
        # Old starts with a message the new export no longer has, so the
        # prefix path fails and the tail window (a key burst) matches twice.
        old_text = msg("6/23/26, 09:00", "Ana", "sumida") + burst
        new_text = burst + msg("6/23/26, 16:37", "Fernando", "a") + EXTRA
        old, new = keys(old_text), keys(new_text)
        boundary, mode, warnings = find_boundary(old, new)
        self.assertEqual(boundary, 4)  # occurrence closest to the expected position wins
        self.assertTrue(any("matches" in w for w in warnings))

    def test_deletion_inside_tail_min_window_errors(self):
        old_text = BASE + EXTRA
        # The last message of the old export is gone from the new one:
        # every candidate window includes it, so anchoring must fail loudly.
        new_text = BASE + msg("6/24/26, 09:00", "Ana", "Segue o link do workshop")
        with self.assertRaises(AnchorNotFound):
            find_boundary(keys(old_text), keys(new_text))


class TestMain(unittest.TestCase):
    def test_basic_delta_verbatim(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, new = write_exports(tmp, BASE, BASE + EXTRA)
            code, out, err = run_main([str(new), "--previous", str(old)])
            self.assertEqual(code, 0)
            self.assertEqual(out, EXTRA)
            self.assertIn("2 new", err)
            self.assertIn("anchor: prefix", err)

    def test_multiline_delta_message_survives_byte_for_byte(self):
        extra = msg("6/24/26, 10:00", "Ana", "linha 1\nlinha 2\n\nlinha 4")
        with tempfile.TemporaryDirectory() as tmp:
            old, new = write_exports(tmp, BASE, BASE + extra)
            code, out, _ = run_main([str(new), "--previous", str(old)])
            self.assertEqual(code, 0)
            self.assertEqual(out, extra)

    def test_text_divergence_in_overlap_keeps_prefix_anchor(self):
        # Same chat exported with/without media, or an edited message:
        # keys match, text does not. The delta must ignore text changes.
        old_text = BASE + msg("6/23/26, 16:34", "Fernando", "<Media omitted>")
        new_text = (
            BASE
            + msg("6/23/26, 16:34", "Fernando", "IMG-0055.jpg (file attached)\nlegenda")
            + EXTRA
        )
        with tempfile.TemporaryDirectory() as tmp:
            old, new = write_exports(tmp, old_text, new_text)
            code, out, err = run_main([str(new), "--previous", str(old)])
            self.assertEqual(code, 0)
            self.assertEqual(out, EXTRA)
            self.assertIn("anchor: prefix", err)

    def test_no_new_messages_exits_zero_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, new = write_exports(tmp, BASE, BASE)
            output = Path(tmp) / "delta.txt"
            code, out, err = run_main(
                [str(new), "--previous", str(old), "--output", str(output)]
            )
            self.assertEqual(code, 0)
            self.assertEqual(out, "")
            self.assertFalse(output.exists())
            self.assertIn("0 new", err)

    def test_output_flag_writes_file_and_prints_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, new = write_exports(tmp, BASE, BASE + EXTRA)
            output = Path(tmp) / "delta.txt"
            code, out, _ = run_main(
                [str(new), "--previous", str(old), "--output", str(output)]
            )
            self.assertEqual(code, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), EXTRA)
            self.assertEqual(out.strip(), str(output))

    def test_anchor_not_found_suggests_full_ingest(self):
        unrelated = msg("1/1/26, 08:00", "Outro", "chat completamente diferente") * 4
        with tempfile.TemporaryDirectory() as tmp:
            old, new = write_exports(tmp, unrelated, BASE + EXTRA)
            code, out, err = run_main([str(new), "--previous", str(old)])
            self.assertEqual(code, 1)
            self.assertEqual(out, "")
            self.assertIn("error:", err)
            self.assertIn("full file", err)

    def test_missing_file_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, _ = write_exports(tmp, BASE, BASE)
            code, _, err = run_main(
                [str(Path(tmp) / "ghost.txt"), "--previous", str(old)]
            )
            self.assertEqual(code, 1)
            self.assertIn("error:", err)

    def test_unparseable_input_errors_with_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, new = write_exports(tmp, "notas soltas\nsem formato\n", BASE)
            code, _, err = run_main([str(new), "--previous", str(old)])
            self.assertEqual(code, 1)
            self.assertIn("error:", err)
            self.assertIn("old.txt", err)

    def test_new_shorter_than_previous_warns_about_swap(self):
        with tempfile.TemporaryDirectory() as tmp:
            old, new = write_exports(tmp, BASE + EXTRA, BASE)
            code, _, err = run_main([str(new), "--previous", str(old)])
            self.assertEqual(code, 1)
            self.assertIn("swapped", err)


if __name__ == "__main__":
    unittest.main()
