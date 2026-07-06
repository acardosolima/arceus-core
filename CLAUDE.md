# Arceus Core

Generic personal knowledge management engine (PKM / second brain). Domain-agnostic.

## What it is
Markdown notes with YAML frontmatter, structured for querying by any LLM via RAG or direct chat. Git-versioned. Can be used for any subject: projects, books, courses, movies.

## Structure
- `templates/note.md` — base note template (generic YAML fields)
- `prompts/extract.md` — LLM prompt to create a new note from raw input
- `prompts/merge.md` — LLM prompt to update an existing note without deleting content
- `prompts/ingest.md` — workflow for processing files from `_inbox/`
- `prompts/lint.md` — periodic semantic check of the vault (contradictions, orphan notes, missing-note concepts, stale claims)
- `scripts/` — deterministic Python tools (see "Scripts")
- `tests/` — test suite for the scripts (`python3 -m unittest discover -s tests`)
- `CHANGELOG.md` — version history and vault migrations (source of truth for releases)

## Vault Pattern
Each vault is a separate Git repository that includes arceus-core as a git submodule at `_arceus/`. The vault extends the base templates with domain-specific fields.

## MERGE Protocol (core rule)
When updating an existing note with new information:
- NEVER delete existing content
- NEVER overwrite unless the new info is more specific
- ALWAYS append to lists
- ALWAYS preserve conflicting information with the prefix `[Variation YYYY-MM-DD | source: X]`
- Increment `revision` (formerly called `schema_version`; old notes may keep the old name until the next merge)
- Log the change under `## History`

## Language
Arceus core: English (agnostic). Vaults use the domain's language.

## Inbox Pattern

Raw files to be processed go into `_inbox/`. The agent reads from there, extracts knowledge into notes, moves the file to `sources/`, and commits.

```
user drops file into _inbox/
        ↓
agent processes with prompts/ingest.md
        ↓
file moved to sources/ with canonical name
        ↓
notes created or merged → git commit
```

`_inbox/` contents are gitignored (only `.gitkeep` is tracked). This keeps raw inputs out of history while preserving traceability via commit messages and the ingestion log (`sources/_log.md`, maintained automatically by `scripts/ingest_move.py`).

## Artifacts Pattern (on-demand deliverables)

Chat answers are ephemeral — that is the default and it is fine. But when the user asks for a **deliverable** (a task list to import somewhere, a report, a briefing, anything they need after the terminal closes), write it to `_artifacts/` and give them the path. Never write deliverables to the vault root or into note folders.

- `_artifacts/` contents are gitignored (only `.gitkeep` is tracked) — deliverables are disposable and regenerable, not knowledge
- Only create a file when the user asks for one (or clearly needs the output elsewhere); do not persist every answer
- If a deliverable turns out to be durable knowledge, promote it into a proper note instead of keeping it in `_artifacts/`

## Scripts (LLM for judgment, scripts for mechanics)

Routine mechanical actions must not depend on an LLM. The LLM decides *what* (which notes, what content, how to classify a source); the scripts in `scripts/` do the deterministic part. From a vault, always call them instead of doing the equivalent by hand:

- `python3 _arceus/scripts/new_note.py <folder> "<Title>" --prefix <PREFIX>` — scaffold a note from the template with the next free ID (never invent IDs manually)
- `python3 _arceus/scripts/ingest_move.py "_inbox/<file>" "<description>" --type "<source type>" --notes "<IDs>"` — canonical rename, move to `sources/`, log row in `sources/_log.md`
- `python3 _arceus/scripts/whatsapp_delta.py <new_export> --previous <old_export> [--output <file>]` - cut the new-message delta from a cumulative WhatsApp chat export, anchored on the previously ingested export of the same chat
- `python3 _arceus/scripts/validate.py` — frontmatter lint for the whole vault; run before committing note changes

Scripts are Python stdlib-only (no pip, no venv) and resolve paths from the current working directory — run them from the vault root.

## Versioning & Vault Updates

Releases are automatic: the GitHub Action (`.github/workflows/release.yml`) runs the tests and tags `v<version>` from the top entry of `CHANGELOG.md` on every push to the main branch. To release, add a changelog entry — never tag by hand.

Vaults pin an exact arceus-core commit via the `_arceus/` submodule; nothing propagates until the vault updates it deliberately. Update protocol (run inside the vault):

1. `git -C _arceus describe --tags` — note the current version
2. `git -C _arceus fetch --tags && git submodule update --remote _arceus`
3. `git -C _arceus describe --tags` — note the new version
4. Read the `CHANGELOG.md` entries between the two versions and apply every "Vault migration" step
5. Commit the submodule pointer together with the migration changes

## Claude Code Permissions (required for every vault)

Every vault based on arceus-core must have a `.claude/settings.json` based on `templates/claude-settings.json`. The agent edits markdowns constantly — prompting for approval on each edit is unnecessary friction — but Bash access stays narrow.

When creating a new vault:
1. Copy `templates/claude-settings.json` to `.claude/settings.json`
2. Replace `VAULT_PATH` with the vault's absolute path (e.g. `/home/user/Repos/vault-my-project`)
3. Add one `Write`/`Edit` pair per domain note folder (e.g. `Write(VAULT_PATH/components/*.md)`) - the template cannot know them

Principles (least privilege - enable only what each actor actually does):
- `Read` is the one broad rule (`VAULT_PATH/**`): consulting is the vault's purpose and reading inside the vault is harmless. Never use `Read(*)` - it exposes SSH keys, credentials, and other sensitive system files.
- `Write`/`Edit` are narrow and per-folder, markdown only. No rule covers `_inbox/` (the user drops files there; the agent only reads and moves them out via script) or non-markdown files anywhere (images, CSVs, PDFs enter through the user). `_artifacts/` is the exception without `.md` restriction - deliverables can be any format.
- The only executable permission beyond read-only inspection and git is `Bash(python3 _arceus/scripts/*)` - the Arceus scripts and nothing else. Do not add broad rules like `Bash(python3 *)`, `Bash(mv *)` or `Bash(cp *)`: file moves inside the vault go through the scripts, and everything else can prompt.
- When a legitimate flow starts prompting for approval, allow that specific case - never widen to `Write(VAULT_PATH/**)`.

## Development Conventions
- Use `git -C /home/user/Repos/arceus-core` instead of `cd` + git
