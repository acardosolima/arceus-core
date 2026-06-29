# Arceus Core

Engine genérica de gestão de conhecimento pessoal (PKM / second brain). Agnóstica de domínio.

## O que é
Notas Markdown com YAML frontmatter, estruturadas para consulta por qualquer LLM via RAG ou chat direto. Git-versionado. Pode ser usado para qualquer tema: projetos, livros, cursos, filmes.

## Estrutura
- `templates/note.md` — template base de nota (campos YAML genéricos)
- `prompts/extract.md` — prompt LLM para criar nova nota a partir de input bruto
- `prompts/merge.md` — prompt LLM para atualizar nota existente sem apagar conteúdo

## Padrão de Vault
Cada vault é um repositório Git separado que inclui arceus-core como git submodule em `_arceus/`. O vault estende os templates base com campos específicos do domínio.

## Protocolo MERGE (regra central)
Ao atualizar uma nota existente com nova informação:
- NUNCA apagar conteúdo existente
- NUNCA sobrescrever se a nova info não for mais específica
- SEMPRE acrescentar a listas (append)
- SEMPRE preservar informações conflitantes com prefixo `[Variação YYYY-MM-DD | fonte: X]`
- Incrementar `schema_version`
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

`_inbox/` contents are gitignored (only `.gitkeep` is tracked). This keeps raw inputs out of history while preserving traceability via commit messages and the ingestion log.

## Claude Code Permissions (required for every vault)

Every vault based on arceus-core must have a `.claude/settings.json` with broad permissions. The agent will be editing markdowns constantly — prompting for approval on each edit is unnecessary friction.

When creating a new vault:
1. Copy `templates/claude-settings.json` to `.claude/settings.json`
2. Replace `VAULT_PATH` with the vault's absolute path (e.g. `/home/user/Repos/vault-my-project`)

Read/Write/Edit are scoped to `VAULT_PATH` only — which already covers `_inbox/`, so no extra permissions are needed to process incoming files. Never use `Read(*)` — it exposes SSH keys, credentials, and other sensitive system files.

## Development Conventions
- Use `git -C /home/user/Repos/arceus-core` instead of `cd` + git
