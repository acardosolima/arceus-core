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

## Claude Code Permissions (required for every vault)

Every vault based on arceus-core must have a `.claude/settings.json` with broad permissions. The agent will be editing markdowns constantly — prompting for approval on each edit is unnecessary friction.

When creating a new vault:
1. Copy `templates/claude-settings.json` to `.claude/settings.json`
2. Replace `VAULT_PATH` with the vault's absolute path (e.g. `/home/user/Repos/vault-my-project`)

Permissions that must be allowed in any vault:
- `Bash(git*)`, `Bash(cp *)`, `Bash(mv *)`, `Bash(ls*)`, `Bash(find *)`, `Bash(grep *)`, `Bash(wc *)`, `Bash(cat *)`, `Bash(python3 *)`, `Bash(mkdir *)`
- `Read(*)` — read any file (needed to process external sources)
- `Write(VAULT_PATH/*)` and `Edit(VAULT_PATH/*)` — writes scoped to the vault

## Development Conventions
- Use `git -C /home/user/Repos/arceus-core` instead of `cd` + git
