# v2.8 critical blocker report

This report records the new red flags found in the 24-article journal build.

## Blocking defects

1. **Hnysiuk Anastasiia** — body list numbering became decimal `1/2` after merge although the source used non-decimal/bullet-like structure. Root cause: numbering definition collision/remap. Body lists must preserve source numbering semantics unless they are inside references.
2. **Magdysiuk Mykhailo** — Figure 2 was missing in the journal. Root cause: object/media relationship fidelity was insufficient. Any lost figure makes the release invalid.
3. **Magdysiuk Mykhailo** — body subheadings (`Вступ`, `Матеріали та методи`, `Результати та їх обговорення`, `Висновки`) lost bold emphasis. Root cause: normalization/style operations overwrote run-level author emphasis.
4. **Matviienko Yevhenii** — nested shape/textbox content contains figure/table captions and tables; those were not recursively styled or audited. This can produce 1.5 spacing, first-line indents in nested tables, and page overflow.
5. **Kosynskyi P. I.** — scientific supervisor line must be split so the person receives `AUTOR` and role/degree text receives `pip`.
6. **Kovalenko Mykyta** — one-line table caption must be split into canonical table number + table title paragraphs.
7. **Zhelinska Olena** — author page breaks and stray blank paragraphs inside body must be removed, while business-required blank after keywords must remain.
8. **Ariaiev Mykola** — titles/degrees such as `член-кореспондент НАМН України` must not receive `AUTOR` style.
9. **English articles** — UDC is correct in English articles, but references heading must be `REFERENCES`, not Ukrainian stamp.
10. Every article boundary must be a real page break; a stray blank paragraph before UDC is not an acceptable separator.

## Decision

The previous full-release file is treated as a diagnostic build, not publication-ready. A new full rebuild must run the v2.8 gates before delivery.
