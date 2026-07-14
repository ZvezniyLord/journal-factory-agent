# v3.0 verified release report

Conference 136 was rebuilt and rendered as a 96-page DOCX release.

## Confirmed fixes

- ETALON three-section pagination and visible page numbering preserved.
- 24 article starts use `pageBreakBefore`; no dummy page-break paragraph exists inside the article region.
- Hnysiuk blank before table and list-definition fidelity preserved.
- Magdysiuk figures restored and body-subheading bold preserved.
- Annotation/keywords adjacency normalized; exactly one blank follows keywords.
- Matviienko nested shape/textbox captions and tables deep-scanned and styled.
- Inline table captions split into label/title without deleting title text.
- Unmarked terminal bibliographies can be inferred conservatively.
- Sherbon fake leading-space indents removed without lexical change.
- Todorova Figure 2 restored and caption retained.
- FREE LISTENERS appended to TOC from the six-record manifest.

## What worked

- Per-article object/media verification plus render inspection.
- `pageBreakBefore` at article starts instead of break-only paragraphs.
- Exact preservation of ETALON section properties and footer relationships.
- Final TOC rebuild after all body and listener records were stable.

## What did not work and is removed from active logic

- Aggregate media counts as proof of article completeness.
- Dummy blank/break paragraphs as article boundaries.
- Treating the template front-matter break as an author-body defect.
- Marker-only reference detection that cannot infer an omitted terminal heading.
- Global whitespace cleanup instead of first-text-node leading-space cleanup.
