# Arceus — Ingest Prompt

Use this workflow to process a raw file from `_inbox/` into vault notes.

**Division of labor**: the LLM does judgment (what is this source, which notes to create or merge, what content to write). Scripts do mechanics (scaffolding, moving, renaming, logging, validating). Never do by hand what a script below already does.

---

## Steps

1. **Read** the file from `_inbox/`
2. **Identify** what kind of source it is (meeting transcript, export, document, chat log, etc.)
   - Cumulative chat export (WhatsApp exports always contain the full history): find the most recent previous export of the same chat in `sources/`, then cut the delta and extract knowledge from the delta only:
     ```
     python3 _arceus/scripts/whatsapp_delta.py "_inbox/<new export>" --previous "sources/<previous export>" --output "_artifacts/<chat>-delta.txt"
     ```
     The full new export still goes through `ingest_move.py` in step 5 - it becomes the base for the next delta. If the script errors (anchor not found), ingest the full file instead.
3. **Decide** whether to create new notes or merge into existing ones:
   - New entity not in the vault → scaffold with the script, then fill following `prompts/extract.md`:
     ```
     python3 _arceus/scripts/new_note.py <folder> "<Title>" --prefix <PREFIX>
     ```
     The script assigns the next free ID and fills the dates — never invent an ID manually.
   - Existing note needs updating → follow `prompts/merge.md`
4. **Write** the note content
5. **Move and log** with one script call (canonical rename + row in `sources/_log.md`):
   ```
   python3 _arceus/scripts/ingest_move.py "_inbox/<file>" "<short description>" --type "<source type>" --notes "<IDs created/updated>"
   ```
6. **Validate** the vault; fix any errors before committing:
   ```
   python3 _arceus/scripts/validate.py
   ```
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
