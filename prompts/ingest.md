# Arceus — Ingest Prompt

Use this workflow to process a raw file from `_inbox/` into vault notes.

---

## Steps

1. **Read** the file from `_inbox/`
2. **Identify** what kind of source it is (meeting transcript, export, document, chat log, etc.)
3. **Decide** whether to create new notes or merge into existing ones:
   - New entity not in the vault → use `prompts/extract.md`
   - Existing note needs updating → use `prompts/merge.md`
4. **Write or update** the notes
5. **Move** the file from `_inbox/` to `sources/` with a canonical name: `YYYY-MM-DD_description.ext`
6. **Update** the ingestion log (if the vault has one) with a row: `date | filename | source type | method | notes created/updated`
7. **Commit** with a message that includes what was processed and what changed

---

## Rules

- Do not invent information not present in the source.
- Certainty level must reflect the source type:
  - `high` — structured export from the system itself (e.g. JSON from Foundry, DB export)
  - `medium` — diagrams, slides, structured documents
  - `low` — verbal descriptions, meeting notes, chat logs
- If the vault defines extended templates or domain-specific certainty rules, follow those instead.
- The file in `_inbox/` is **not committed** — only the processed output in `sources/` and the updated notes are.
