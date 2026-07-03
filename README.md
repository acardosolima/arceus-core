# Arceus

A generic, personal knowledge management engine built on plain text.

Arceus defines the conventions, templates, and LLM prompts to capture, structure, and query any kind of knowledge — work projects, books, courses, concepts, research, anything.

## Core ideas

- **Vaults** are independent Git repositories that follow this structure, one per topic or project
- **Notes** are `.md` files with structured YAML frontmatter
- **Prompts** are LLM instructions (paste into Claude, ChatGPT, Ollama, etc.) to extract and update notes from any raw input
- **Bidirectional links** (`[[Note Title]]`) connect knowledge across the vault

## Vault structure

```
vault-<topic>/
├── _arceus/          ← this repo as a git submodule
├── _inbox/           ← raw files waiting to be processed (gitignored)
├── _artifacts/       ← on-demand deliverables: reports, task lists (gitignored)
├── sources/          ← processed raw files, canonical names + _log.md
├── templates/        ← vault-specific templates (extend the base ones here)
├── prompts/          ← vault-specific prompts (extend the base ones here)
├── <topic-folder>/   ← notes organized however makes sense for the vault
│   └── _index.md
└── README.md
```

## Base templates

`templates/note.md` — the generic base note. Every vault template should include these fields and can add domain-specific ones on top.

## Base prompts

- `prompts/extract.md` — creates a new note from any raw input (document, transcript, export, manual text)
- `prompts/merge.md` — updates an existing note with new information **without deleting** what's already there
- `prompts/ingest.md` — end-to-end workflow for processing an `_inbox/` file

## Scripts

Deterministic mechanics live in `scripts/` (Python, stdlib-only) so they never depend on an LLM: note scaffolding with safe ID assignment (`new_note.py`), inbox → sources moves with canonical naming and logging (`ingest_move.py`), and vault-wide frontmatter linting (`validate.py`). Run them from the vault root; see `CLAUDE.md` for the exact invocations.

## Versioning

Vaults pin an exact core commit through the submodule. Releases are tagged automatically from `CHANGELOG.md` by CI; each changelog entry carries the migration steps a vault must apply when it updates `_arceus/`. The update protocol is documented in `CLAUDE.md`.

## How to create a new vault

```bash
git init vault-<topic>
cd vault-<topic>
git submodule add <arceus-core-url> _arceus
mkdir -p _inbox _artifacts sources templates prompts .claude
touch _inbox/.gitkeep _artifacts/.gitkeep
cp _arceus/.gitignore .gitignore
cp _arceus/templates/note.md templates/
cp _arceus/prompts/* prompts/
cp _arceus/templates/claude-settings.json .claude/settings.json
# replace VAULT_PATH in .claude/settings.json with the vault's absolute path
# extend templates and prompts for your domain
```
