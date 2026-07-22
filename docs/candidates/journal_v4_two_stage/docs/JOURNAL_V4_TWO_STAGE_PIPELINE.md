# Journal v4 — Two-stage pipeline

## Мета

Відокремити безпечне складання чернетки від інтелектуального аналізу структури. Програма спочатку нічого не «розуміє» і не виправляє: вона механічно переносить статті. Лише після цього окреме ядро створює технічну JSON-карту.

## Канонічна послідовність

```text
Dashboard + Workspace
  -> load template_shell_contract.json
  -> copy ETALON to workspace
  -> resolve exact JOURNAL_CONTENT_SLOT
  -> prepare TOC placeholder/table
  -> insert one page break
  -> for each article in registry order:
       copy source to articles_raw
       Stage 1: 11 pt + 1.0 only
       save independent stage1 DOCX
       append stage1 article to draft body
       emit stage1 report
  -> save mechanical journal draft
  -> for each stage1 article:
       Stage 2: detect technical zones read-only
       validate JSON schema
       emit article zones JSON
  -> build/update conference TOC from accepted registry/zone data
  -> replace TOC content inside exact slot only
  -> save JOURNAL_<number>__DRAFT.docx
```

## Shell boundary

Runtime never discovers front/tail boundaries visually or semantically. The template owner defines them once through an exact OOXML bookmark or content-control tag. Runtime receives only the slot locator. Prefix and suffix are opaque.

Allowed mutation graph:

```text
ETALON copy
├── protected prefix: no access
├── JOURNAL_CONTENT_SLOT:
│   ├── conference TOC
│   ├── page break
│   └── draft article body
└── protected suffix: no access
```

## Stage 1 contract

Input: one source article.

Output: one independent Stage 1 article and a report.

Allowed changes:

```json
{"font_size_pt": 11, "line_spacing": 1.0}
```

Everything else is immutable. Stage 1 must compare ordered text/object signatures before and after and return `BLOCKED` when it changed anything else. The comparison is article-local; protected template pages are outside its scope.

## Stage 2 contract

Stage 2 reads the Stage 1 article and emits `article_technical_zones.schema.json`.

It must preserve:

- every paragraph and object in original order;
- a one-to-one or explicit one-to-many mapping from source elements to blocks;
- `unknown` for unsupported or ambiguous content;
- evidence and confidence for every resolved role.

Stage 2 does not apply styles, repair paragraphs, alter line breaks, remove contacts, rewrite headings, or normalize bibliography.

## Header model

```text
ArticleHeader
├── identifiers
│   ├── UDC
│   └── DOI
├── people[]
│   ├── person/name
│   ├── degree[]
│   ├── academic_title[]
│   ├── position[]
│   ├── institution[]
│   ├── department[]
│   ├── location[]
│   └── identifiers[] (ORCID etc.)
├── supervisors[]
├── article_title
└── boundary_to_body
```

A line may remain `unknown`; it must never be silently attached to the nearest person.

## Marker confidence

- Exact marker + valid position: deterministic high confidence.
- Marker family + registry/corpus support: medium/high confidence.
- Visual evidence only: supporting evidence.
- LLM-only guess: `review`, never automatic PASS below configured threshold.
- No evidence: `unresolved`.

## Future Stage 3

Production formatting, paragraph repair, header rewriting, reference numbering, layout correction, pagination and final visual QA are deliberately outside v4 draft. They require a separate approved stage that consumes, but never silently rewrites, the Stage 2 JSON.
