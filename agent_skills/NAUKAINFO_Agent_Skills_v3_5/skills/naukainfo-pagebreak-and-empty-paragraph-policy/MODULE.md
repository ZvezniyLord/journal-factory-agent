---
name: naukainfo-pagebreak-and-empty-paragraph-policy
description: Removes author-inserted page breaks and stray empty paragraphs inside articles while preserving required journal spacing and ensuring each article starts on a new page.
version: "2.8.0"
---

# Page breaks

Author manual page breaks inside an article are not accepted. Remove them unless they are the journal assembly boundary between articles.

During journal assembly, every article must start with a real page break / section-aware boundary before DOI/UDC, not with an accidental empty paragraph.

# Empty paragraphs preserved by business rules

Keep or create exactly one empty paragraph:

- after UDC/UDC line;
- between the cleaned author header and the article title;
- after article title;
- after annotation/abstract only when required by business layout;
- after keywords;
- after each table, figure, or `Джерело:` / `Source:` note;
- before and after the reference heading stamp.

# Empty paragraphs removed

Remove stray author blank paragraphs before ordinary body paragraphs, before numbered body paragraphs, and around manual page breaks if they are not one of the allowed business spacing points.

# Safety

Removing an empty paragraph must never remove adjacent text or join two articles. If deleting a blank before UDC causes article merge, insert/restore the article page break instead.

## v3.0 article-boundary and spacing contract

- Do not create an empty paragraph that contains only a manual page break before an article.
- Remove author-inserted page breaks from inside article bodies.
- Set `pageBreakBefore` on the first structural paragraph of every article (`SECTION` when newly emitted, otherwise DOI/UDC). This creates a clean new-page start without a dummy paragraph.
- Preserve the ETALON front-matter page break before `TABLE OF CONTENTS`; it is outside the article region and is not an author break.
- There must be no blank paragraph between `Анотація`/`Abstract` and `Ключові слова`/`Keywords`.
- There must be exactly one blank paragraph after the keywords block.
- There must be exactly one blank paragraph immediately before a table/figure cluster when the preceding paragraph is ordinary body text, and one after the complete cluster/source note.
