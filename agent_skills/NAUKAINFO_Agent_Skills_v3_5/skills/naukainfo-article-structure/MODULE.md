---
name: naukainfo-article-structure
description: Inspects DOCX or converted workspace copies read-only to identify UDC/DOI, authors, affiliations, title, body start, references, tables, images, formulas, shapes, and suspicious service-form structure. Use when a title is multiline, a header is ambiguous, or matching needs evidence.
license: Proprietary project skill
compatibility: Windows 11; Python 3.11+; NAUKAINFO Journal Builder project; MCP tools recommended.
metadata:
  author: naukainfo
  version: "1.0.0"
---

# Procedure

1. Call `inspect_docx_readonly` on the source or workspace copy.
2. Read the first front-matter paragraphs plus table cells, not the full article unless necessary.
3. Identify:
   - DOI and UDC;
   - human author names;
   - degree/position/institution/city/country/ORCID;
   - complete multi-paragraph title;
   - body boundary;
   - references heading and list behavior;
   - object counters.
4. Classify uncertain lines as `unknown`, not automatically as affiliation.
5. Return evidence with paragraph indices and exact short excerpts.

## Hard distinctions

- `author`: human name only.
- `affiliation`: degrees, positions, institutions, locations, ORCID and other service metadata.
- A university named after a person is still an institution.
- Text after the title is not header unless there is strong structural evidence.
- Application/participant form tables are service documents even when they contain a presentation title.

Read `references/front-matter.md` for detailed rules.
