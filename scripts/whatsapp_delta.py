"""Cut the new-message delta from a cumulative WhatsApp chat export.

Usage:
    python3 _arceus/scripts/whatsapp_delta.py <new_export> --previous <old_export> [--output <file>]

WhatsApp only exports the full chat history - every new export repeats
everything already ingested. Given the new export and the previously
ingested one, this prints only the messages that appeared after the
previous export ended, verbatim and still in WhatsApp format, ready for
normal ingestion. With --output the delta is written to that file and
its path is printed instead.

The LLM decides *which* file in sources/ is the previous export of the
same chat (judgment); the cut itself is deterministic and belongs here
(see prompts/ingest.md).

Messages are matched by (timestamp, sender) key, never by text: the
same message can render differently between exports (edits gain
"<This message was edited>", media placeholders depend on the export
options). Timestamps are opaque strings - they are locale-dependent
(M/D vs D/M) and not even monotonic (group history can predate the
exporter joining), so interpreting them would only add wrong
assumptions.

Known limits: text that changed only inside the already-ingested range
(an old message edited later) never shows up in any delta. A device
timezone change between exports shifts every timestamp and breaks
anchoring - that fails loudly (ingest the full file) rather than
producing a silently wrong delta.
"""

import argparse
import re
import sys
from collections import namedtuple
from pathlib import Path

# A message header line: optional LRM mark, date, time, optional AM/PM
# (plain, NBSP or narrow-NBSP separated, depending on device locale),
# then " - " and the rest. Continuation lines of multiline messages
# don't match and attach to the previous message.
MSG_START = re.compile(
    r"^‎?"
    r"(\d{1,2}/\d{1,2}/\d{2,4}, \d{1,2}:\d{2}(?:[   ]?[APap]\.?[Mm]\.?)?)"
    r" - (.*)"
)

# Anchor window bounds: a single (timestamp, sender) key is not unique
# (minute resolution + message bursts), so the previous export's tail is
# matched as a sequence, shrinking from MAX until it fits, never below
# MIN - below that, bursts make false positives likely.
TAIL_WINDOW_MAX = 10
TAIL_WINDOW_MIN = 3

Message = namedtuple("Message", "key lines")


class AnchorNotFound(ValueError):
    """The previous export's tail does not occur in the new export."""


def parse_export(text):
    """Parse a WhatsApp export into Message records with raw lines.

    The key is (timestamp, sender); sender is None for system messages
    (no ": " in the body). When a system message happens to contain
    ": " (e.g. a group name with a colon), the split yields a wrong
    "sender" - harmless, because keys are only ever compared between
    two parses of the same chat, so they just need to be deterministic.
    """
    messages = []
    for line in text.splitlines(keepends=True):
        match = MSG_START.match(line)
        if match:
            rest = match.group(2)
            sender = rest.split(": ", 1)[0] if ": " in rest else None
            messages.append(Message((match.group(1), sender), [line]))
        elif messages:
            messages[-1].lines.append(line)
        # Lines before the first header (never seen in real exports)
        # carry no key and are dropped.
    if not messages:
        raise ValueError("no WhatsApp message lines found - not a chat export?")
    return messages


def find_boundary(old_keys, new_keys):
    """Locate where the previous export ends inside the new one.

    Returns (index into new records, anchor mode, warnings). Fast path:
    the old key sequence is a strict prefix of the new one (the normal
    case; text differences don't matter because keys ignore text).
    Fallback for perturbed histories (messages deleted from the middle):
    slide the old export's tail window over the new keys, shrinking the
    window until it matches. Ambiguous matches pick the occurrence
    closest to where the boundary would be if nothing had been deleted -
    deterministic, and biased toward re-reading a message over losing
    one. No match at all raises AnchorNotFound.
    """
    if new_keys[: len(old_keys)] == old_keys:
        return len(old_keys), "prefix", []

    warnings = []
    max_window = min(TAIL_WINDOW_MAX, len(old_keys))
    min_window = min(TAIL_WINDOW_MIN, max_window)
    for window in range(max_window, min_window - 1, -1):
        tail = old_keys[-window:]
        occurrences = [
            i
            for i in range(len(new_keys) - window + 1)
            if new_keys[i : i + window] == tail
        ]
        if not occurrences:
            continue
        expected = len(old_keys) - window
        if len(occurrences) > 1:
            warnings.append(
                f"anchor window of {window} messages matches "
                f"{len(occurrences)} positions; using the one closest "
                f"to the expected boundary"
            )
        best = min(occurrences, key=lambda i: abs(i - expected))
        return best + window, f"tail:{window}", warnings

    raise AnchorNotFound(
        "previous export's tail not found in the new export - different "
        "chat, swapped arguments, or timestamps shifted (timezone "
        "change); ingest the full file instead"
    )


def _parse_file(path):
    text = Path(path).read_text(encoding="utf-8")
    try:
        return parse_export(text)
    except ValueError as exc:
        raise ValueError(f"{path}: {exc}") from None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Print only the messages a cumulative WhatsApp export "
        "gained since the previously ingested one."
    )
    parser.add_argument("new_export", help="path to the new (full) chat export")
    parser.add_argument(
        "--previous",
        required=True,
        help="path to the previously ingested export of the same chat",
    )
    parser.add_argument(
        "--output", help="write the delta to this file instead of stdout"
    )
    args = parser.parse_args(argv)

    try:
        old = _parse_file(args.previous)
        new = _parse_file(args.new_export)
        if len(new) < len(old):
            print(
                "warning: new export has fewer messages than the previous "
                "one - swapped arguments?",
                file=sys.stderr,
            )
        boundary, mode, warnings = find_boundary(
            [m.key for m in old], [m.key for m in new]
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    delta = new[boundary:]
    print(
        f"{len(old)} messages in previous export, {len(new)} in new, "
        f"{len(delta)} new (anchor: {mode})",
        file=sys.stderr,
    )
    if not delta:
        return 0

    content = "".join(line for message in delta for line in message.lines)
    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
        print(args.output)
    else:
        sys.stdout.write(content)
    return 0


if __name__ == "__main__":
    sys.exit(main())
