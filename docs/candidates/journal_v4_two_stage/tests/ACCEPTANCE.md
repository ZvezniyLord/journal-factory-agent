# Acceptance — Journal v4 draft logic

## Template shell

- [ ] Exact `JOURNAL_CONTENT_SLOT` exists once.
- [ ] Runtime does not scan or normalize protected prefix/suffix.
- [ ] No operation edits sections, headers, footers or page numbering.
- [ ] Slot contains TOC, exactly one page break, then draft body.

## Stage 1

- [ ] Each article is processed independently and in registry order.
- [ ] All editable article text is 11 pt.
- [ ] Every article paragraph is single-spaced.
- [ ] Ordered lexical text is unchanged.
- [ ] Paragraph boundaries and manual line breaks are unchanged.
- [ ] Tables, figures, drawings and relationships are unchanged.
- [ ] No semantic classifier or LLM runs in Stage 1.
- [ ] `Ctrl+A` semantics are article-local, never master-document-wide.

## Stage 2

- [ ] JSON validates against `article_technical_zones.schema.json`.
- [ ] Every source element is mapped or explicitly `unknown`.
- [ ] Header people are distinct entities.
- [ ] Degree/title/position/institution/location lines retain source locators.
- [ ] UDC/DOI/annotation/keywords/references use versioned marker evidence.
- [ ] Low-confidence classifications are REVIEW/BLOCKED.
- [ ] Stage 2 writes no DOCX changes.

## Release safety

- [ ] Output name includes `DRAFT`.
- [ ] `ACTIVE_RELEASE.json` is unchanged.
- [ ] Candidate activation requires explicit operator approval.
