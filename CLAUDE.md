# Arceus Core

Engine genérica de gestão de conhecimento pessoal (PKM / second brain). Agnóstica de domínio.

## O que é
Notas Markdown com YAML frontmatter, estruturadas para consulta por qualquer LLM via RAG ou chat direto. Git-versionado. Pode ser usado para qualquer tema: projetos, livros, cursos, filmes.

## Estrutura
- `templates/note.md` — template base de nota (campos YAML genéricos)
- `prompts/extract.md` — prompt LLM para criar nova nota a partir de input bruto
- `prompts/merge.md` — prompt LLM para atualizar nota existente sem apagar conteúdo
- `prompts/ingest.md` — workflow de processamento de arquivos do `_inbox/`
- `scripts/` — ferramentas determinísticas em Python (ver "Scripts")
- `tests/` — suite de testes dos scripts (`python3 -m unittest discover -s tests`)
- `CHANGELOG.md` — registro de versões e migrações de vault (fonte de verdade das releases)

## Padrão de Vault
Cada vault é um repositório Git separado que inclui arceus-core como git submodule em `_arceus/`. O vault estende os templates base com campos específicos do domínio.

## Protocolo MERGE (regra central)
Ao atualizar uma nota existente com nova informação:
- NUNCA apagar conteúdo existente
- NUNCA sobrescrever se a nova info não for mais específica
- SEMPRE acrescentar a listas (append)
- SEMPRE preservar informações conflitantes com prefixo `[Variação YYYY-MM-DD | fonte: X]`
- Incrementar `revision` (antes chamado `schema_version`; notas antigas podem manter o nome até o próximo merge)
- Registrar mudança em `## History`

## Língua
Arceus core: Inglês (agnóstico). Vaults usam a língua do domínio.

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

Principles:
- Read/Write/Edit are scoped to `VAULT_PATH` only — which already covers `_inbox/` and `_artifacts/`. Never use `Read(*)` — it exposes SSH keys, credentials, and other sensitive system files.
- The only executable permission beyond read-only inspection and git is `Bash(python3 _arceus/scripts/*)` — the Arceus scripts and nothing else. Do not add broad rules like `Bash(python3 *)`, `Bash(mv *)` or `Bash(cp *)`: file moves inside the vault go through the scripts, and everything else can prompt.

## Development Conventions
- Use `git -C /home/user/Repos/arceus-core` instead of `cd` + git
