# Changelog

Each entry documents what changed and — most importantly — the **vault migration** steps, if any. When a vault updates its `_arceus/` submodule, read every entry between the old and the new version and apply the migrations.

The version at the top of this file is the source of truth for releases: the GitHub Action tags `v<version>` automatically when a push to the main branch carries a new top version here. To release, add an entry — never tag by hand.

## 0.3.1 - 2026-07-06

### Changed
- `templates/claude-settings.json` now follows least privilege: `Write`/`Edit` are per-folder and markdown-only instead of `VAULT_PATH/**` (broad `Read` stays - consulting is the vault's purpose). No rule covers `_inbox/` (user territory; the agent moves files out via script) or non-markdown files (they enter through the user); `_artifacts/` keeps any-format Write/Edit for deliverables. New-vault setup gains step 3: add one Write/Edit pair per domain note folder.

### Vault migration
- Vaults created from the old template: narrow `Write(VAULT_PATH/**)` / `Edit(VAULT_PATH/**)` in `.claude/settings.json` to the per-folder rules of the new template, adding a pair per domain note folder. Vaults that already hand-tightened their settings (the new template mirrors vault-hercules) need nothing.

## 0.3.0 - 2026-07-06

### Added
- `scripts/whatsapp_delta.py` - cut the new-message delta from a cumulative WhatsApp chat export. WhatsApp only exports the full history, so every new export repeats what was already ingested; the script anchors on the previously ingested export (matching messages by timestamp + sender, never by text, which changes between exports) and emits only the new messages, verbatim. `prompts/ingest.md` gained the corresponding sub-step: extract knowledge from the delta only, then move the full new export to `sources/` as the next diff base.

### Vault migration
None.

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
