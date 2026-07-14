# Legacy Analysis

Reference package found:

`C:\Users\Vint\Downloads\_source_zip\NAukaInfo_JournalBuilder_CLEAN_FOR_CODEX`

Observed guidance:

- build a new clean version instead of patching old code;
- use current `Jurnal.dotx` styles, not legacy 14 pt rules;
- DOI and UDC use `UDC` style;
- mandatory empty paragraphs must be audited and safely repaired;
- JSON files are controlled pipeline state, not disposable debug logs;
- final output must be blocked on critical text/object/style loss.

Rejected as current source:

- old output journals;
- old hardcoded 14 pt formatting;
- cache/debug/venv artifacts;
- failed archive journal copies.

