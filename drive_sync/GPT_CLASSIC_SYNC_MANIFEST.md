# GPT Classic sync manifest

Sync date: 2026-07-17

## GitHub target

- Repository: `ZvezniyLord/journal-factory-agent`
- Branch: `agent/gpt-classic-sync`
- Base commit: `52b102b15b967b2e3c3c42324d1c778602038fb7`

## Google Drive source

- Root folder: `JOURNAL_FACTORY_MASTER_v1`
- Folder ID: `12OwADnVY06T__bwxlfkuRMqtJbnlGCe1`
- Journal skill folder: `01_SKILL_JOURNAL`
- Journal skill folder ID: `1X0MUqVA1y4cDcAfJWB3Jsz3rpd7ohGDu`
- GitHub handoff folder: `08_GITHUB_HANDOFF__Jurnali_Skills`
- Handoff folder ID: `1lOJublJivlUgZMrOxGSvTH38RrhHP02N`
- Source bundle: `NAUKAINFO_Agent_Skills_v3_2_ALL_SKILLS.md`
- Source bundle file ID: `1RlY4frKpT_VGPW5AD5SGpEC0FJSFUXLB`
- Regression reference: `JOURNAL_136_FINAL_RELEASE_v33.docx`
- Regression file ID: `1BGE0JSPDQJHhgdr-M7ZExhD-XeozaJKR`

## Files mirrored in this sync

- `skills/journal/SKILL.md`
- `docs/PUBLISHED_REFERENCE_PARITY_136_137.md`
- `drive_sync/GPT_CLASSIC_SYNC_MANIFEST.md`
- `GPT_CLASSIC.md`

## Scope note

This sync mirrors the active journal instructions and the new published-reference parity findings. It does not duplicate all binary templates, PDFs, DOCX fixtures, archives, or generated releases into GitHub. Those remain authoritative on Google Drive and are referenced by immutable IDs above.

Binary mirroring should be implemented later with a checksum manifest and Git LFS/release assets. Blindly committing every Drive binary is prohibited because it would duplicate large generated files and mix authoritative inputs with outputs.
