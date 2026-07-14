---
name: naukainfo-table-caption-split-contract
description: Normalizes table captions written as a single author line into the NAUKAINFO two-line table caption format without changing the caption meaning.
version: "2.8.0"
---

# Canonical format

If an author writes:

`Таблиця 1 – Порівняння підходів до обробки запитів`

or similar one-line variants, convert to:

1. `Таблиця 1` — separate paragraph, bold, right aligned.
2. `Порівняння підходів до обробки запитів` — next paragraph, centered, actual ETALON style `РисПід` (`styleId af6`), single spacing.

The dash/colon after the number is formatting noise and may be removed only if the title text is preserved exactly.

# Constraints

- Do not rewrite the title.
- Do not delete table context.
- Keep the caption with the table.
- Apply this both in body text and inside shape/textbox `w:txbxContent`.

## v3.0 canonical inline-caption split

For an author line such as `Таблиця 1 – Порівняння підходів до обробки запитів`, preserve both semantic parts but remove only the separator dash: create `Таблиця 1` as a separate bold right-aligned paragraph, then the title as a separate centered bold caption paragraph (actual ETALON `РисПід` style (`styleId af6`)). Keep the table immediately after the title and prevent the label/title from splitting away from it.
