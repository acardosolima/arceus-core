# Changelog

Each entry documents what changed and — most importantly — the **vault migration** steps, if any. When a vault updates its `_arceus/` submodule, read every entry between the old and the new version and apply the migrations.

The version at the top of this file is the source of truth for releases: the GitHub Action tags `v<version>` automatically when a push to the main branch carries a new top version here. To release, add an entry — never tag by hand.

## 0.2.0 - 2026-07-03

### Added
- `scripts/` — deterministic Python tools (stdlib-only) so routine mechanics no longer depend on an LLM:
  - `new_note.py` — scaffold a note from the template with the next free ID
  - `ingest_move.py` — move a processed file from `_inbox/` to `sources/` with canonical name + row in `sources/_log.md`
  - `validate.py` — frontmatter lint (required fields, dates, unique IDs); non-zero exit on errors
- `_artifacts/` pattern — on-demand deliverables (reports, task lists) are written here instead of dying in the chat; gitignored, disposable
- `tests/` — unittest suite for the scripts (`python3 -m unittest discover -s tests`)
- `.github/workflows/release.yml` — runs tests and auto-tags from this changelog on every push to main
- `sources/_log.md` is now the defined ingestion log for every vault (created automatically by `ingest_move.py`)
- `LICENSE` — GPL-3.0: free to use, attribution required, published derivatives must stay under the same license

### Changed
- `schema_version` renamed to `revision` in the note template and prompts — it counts content merges, not schema changes
- `prompts/ingest.md` rewritten around the split "LLM for judgment, scripts for mechanics"
- `templates/claude-settings.json` tightened: broad `Bash(mv/cp/mkdir/python3 *)` rules replaced by the single narrow rule `Bash(python3 _arceus/scripts/*)`

### Vault migration
1. `_artifacts/`: create the folder with a `.gitkeep` and gitignore its contents (see core `.gitignore`)
2. `.claude/settings.json`: remove `Bash(mv *)`, `Bash(cp *)`, `Bash(mkdir *)`, `Bash(python3 *)`; add `Bash(python3 _arceus/scripts/*)`
3. Notes with `schema_version` keep working (validator warns); rename to `revision` opportunistically when a note is next merged
4. Run `python3 _arceus/scripts/validate.py` and fix anything it reports

## 0.1.0 - 2026-06-28

### Added
- Initial structure: base note template, `extract`/`merge`/`ingest` prompts, `_inbox/` pattern, vault-as-submodule convention, Claude Code permissions template
