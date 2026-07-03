"""Lint the frontmatter of every note in the vault.

Usage:
    python3 _arceus/scripts/validate.py [vault_root]

Checks that every note (any .md file with frontmatter outside the
engine/transient directories) has the required fields filled, valid
ISO dates, a revision counter, and a vault-unique id. Exits non-zero
on errors so it can gate commits.

Warnings (deprecated fields) are reported but never fail the run:
a vault must be able to adopt the validator before migrating old notes.
"""

import re
import sys
from pathlib import Path

from _lib import find_notes

REQUIRED_FIELDS = ("id", "title", "created_at", "updated_at")
DATE_FIELDS = ("created_at", "updated_at")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def validate_vault(root):
    """Return (errors, warnings), each a list of `path: message` strings."""
    errors = []
    warnings = []
    seen_ids = {}

    for path, meta in find_notes(root):
        rel = path.relative_to(root)

        for field in REQUIRED_FIELDS:
            if not str(meta.get(field, "")).strip():
                errors.append(f"{rel}: missing or empty `{field}`")

        for field in DATE_FIELDS:
            value = str(meta.get(field, ""))
            if value.strip() and not DATE_RE.fullmatch(value):
                errors.append(f"{rel}: `{field}` is {value!r}, expected YYYY-MM-DD")

        # `schema_version` was renamed to `revision` (it counts content
        # merges, not schema changes). Old notes keep working, but the
        # deprecation is surfaced on every run until they migrate.
        revision = meta.get("revision", meta.get("schema_version"))
        if "schema_version" in meta and "revision" not in meta:
            warnings.append(f"{rel}: `schema_version` is deprecated, rename it to `revision`")
        if revision is None:
            errors.append(f"{rel}: missing `revision`")
        elif not isinstance(revision, int) or revision < 1:
            errors.append(f"{rel}: `revision` is {revision!r}, expected an integer >= 1")

        note_id = str(meta.get("id", "")).strip()
        if note_id:
            if note_id in seen_ids:
                errors.append(f"{rel}: duplicate id `{note_id}` (also in {seen_ids[note_id]})")
            else:
                seen_ids[note_id] = rel

    return errors, warnings


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    root = Path(argv[0]) if argv else Path.cwd()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 1

    errors, warnings = validate_vault(root)
    for warning in warnings:
        print(f"warning: {warning}")
    for error in errors:
        print(f"error: {error}")

    checked = sum(1 for _ in find_notes(root))
    if errors:
        print(f"\n{checked} notes checked: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"{checked} notes checked: ok ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
