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
├── templates/        ← vault-specific templates (extend the base ones here)
├── prompts/          ← vault-specific prompts (extend the base ones here)
├── <topic-folder>/   ← notes organized however makes sense for the vault
│   └── _index.md
└── README.md
```

## Base templates

`templates/note.md` — the generic base note. Every vault template should include these fields and can add domain-specific ones on top.

## Base prompts

Two prompts cover all ingestion scenarios:

- `prompts/extract.md` — creates a new note from any raw input (document, transcript, export, manual text)
- `prompts/merge.md` — updates an existing note with new information **without deleting** what's already there

## How to create a new vault

```bash
git init vault-<topic>
cd vault-<topic>
git submodule add <arceus-core-url> _arceus
cp _arceus/templates/note.md templates/
cp _arceus/prompts/* prompts/
# extend templates and prompts for your domain
```
