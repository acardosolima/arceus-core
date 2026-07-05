# Arceus — Lint Prompt

Semantic lint: reads note **content** across the whole vault to find issues that `scripts/validate.py` cannot see. `validate.py` checks the *shape* of each note in isolation (frontmatter fields, dates, unique ids) — mechanical, no understanding required. This prompt checks the *substance* of the vault as a whole — contradictions, gaps, staleness — which needs judgment, so it's a prompt, not a script.

Run this periodically (e.g. weekly), not on every commit — it reads the full vault and is too slow/expensive to gate commits.

---

## Steps

1. Read every note in the vault.
2. Run the four checks below across all of them.
3. Write findings to `_artifacts/lint-<YYYY-MM-DD>.md` (per the Artifacts Pattern — this is a disposable report, not vault knowledge).
4. **Do not modify any note.** This prompt only reports; follow-up merges/new notes are separate, deliberate actions the user reviews first.

---

## Checks

### 1. Contradictions between notes
Two notes make factual claims about the same thing that disagree, and neither has recorded the other as a `[Variation YYYY-MM-DD | fonte: X]` per the merge protocol — meaning the conflict was never reconciled, just left sitting in two places.

### 2. Orphan pages
A note with an empty `related` field that no other note links to via `[[...]]` either. It exists but nothing points to it and it points to nothing — structurally valid, practically unreachable.

### 3. Concepts without a dedicated note
An entity or term mentioned in the body of several different notes (rule of thumb: 3+) but that has no note of its own (`new_note.py` was never run for it). Signals a missing note, not a defect in an existing one.

### 4. Stale claims
A note states something (e.g. a status, an assignment, an ownership) that a more recently updated note implicitly supersedes, but the older note was never merged/updated to reflect it.

---

## Output format

Write to `_artifacts/lint-<YYYY-MM-DD>.md`, grouped by check, one line per finding with the note id(s) and a suggested next action:

```markdown
# Lint Report — 2026-07-05

## Contradictions
- COMP-004 vs NOTE-017: acquisition status disagrees. → Suggest: reconcile via prompts/merge.md.

## Orphan pages
- NOTE-031: no inbound links, empty `related`. → Suggest: link from relevant notes or confirm it's intentionally standalone.

## Missing notes
- "Project Chimera" mentioned in NOTE-012, NOTE-019, NOTE-024, no dedicated note. → Suggest: python3 _arceus/scripts/new_note.py <folder> "Project Chimera" --prefix <PREFIX>

## Stale claims
- NOTE-002 (updated 2025-11-03) states Alice leads the project; NOTE-040 (updated 2026-06-01) implies reassignment. → Suggest: review and merge into NOTE-002 if confirmed.
```

If a section has no findings, omit it rather than writing "none found."

---

## Rules

- Report only — no note is edited as part of this prompt.
- Every finding must cite specific note ids; no vague claims like "some notes seem outdated."
- If uncertain whether something is a real contradiction/staleness (vs. two notes about genuinely different things), don't report it — false positives erode trust in the report.
