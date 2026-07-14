---
name: naukainfo-reference-language-and-marker-contract
description: Recognizes Ukrainian and English reference headings, replaces them with the correct language-specific stamp, and applies REFER numbering independently per article.
version: "2.8.0"
---

# Ukrainian articles

Use exactly:

`СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:`

# English articles

Use exactly:

`REFERENCES`

Do not replace an English article’s references block with the Ukrainian stamp.

# Recognition

Recognize variants such as:

- `Список використаних джерел`, `Список літератури`, `Література`, `References`, `Reference list`, `Bibliography`;
- numbered headings such as `14. Список використаних джерел` or `References:`.

Normalize the heading, then apply the correct `REF-TITLE` and rebuild entries with `REFER`, restarting from 1 for each article.

# DOI/URL in references

- ordinary web links must be preceded by `URL:`;
- DOI links or DOI strings must be preceded by `DOI:`;
- preserve the rest of the reference text.

## v2.9 multilingual extension

Use the shared marker library. German `Literaturverzeichnis` and `Quellenverzeichnis` are separate standard headings; preserve that distinction. Recognize numbered markers such as `14. Список використаних джерел`, remove only the service number, and rebuild the list from 1. English `REFERENCE.` normalizes to `REFERENCES`.
