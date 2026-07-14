---
name: naukainfo-toc-author-cleaning
description: Clean author display names for the Table of Contents without leaking roles, institutions, degrees, ORCID, cities, contacts, or supervisor lines.
---

# TOC Author Cleaning

This skill is invoked after article front matter is normalized and before `naukainfo-toc-table-builder` materializes the static table of contents.

## Rule

TOC author cells must contain **only participant names**, separated by commas. They must not include:

- degrees, titles, ranks, professional positions;
- institution or department names;
- city/country lines;
- ORCID, e-mail, phone, messenger or other contact data;
- words like `науковий керівник`, `PhD`, `Senior Lecturer`, `Department`, `University`, `імені`, unless these words are part of a person's actual name, which is exceptional and requires review.

## Source of truth

1. Prefer cleaned author names from the manifest/evidence-matching layer.
2. If the manifest is incomplete, parse only the source article header **before the title** and accept a paragraph as an author candidate only if it matches a person-name pattern.
3. When a source line combines name + role/degree, split for TOC display; preserve the original line in the body unless header-normalization has an explicit safe rule to split it.
4. Never build TOC author text by simply joining every paragraph styled `AUTOR`: body style errors must not leak into the table of contents.

## Person-name acceptance

Accepted examples:

- `Соловйов Олег Володимирович`
- `Косинський П. І.`
- `Novak Natalya`
- `Sherbon Fedir`

Rejected examples:

- `PhD in Architektur`
- `Senior Lecturer of Acting`
- `імені Івана Огієнка`
- `Bohdan Khmelnytskyi National Academy of`
- `м. Одеса, Україна`
- `https://orcid.org/...`

## QA

Fail the TOC author gate if any TOC author cell contains role/institution/contact tokens or if a known article participant is missing. Store the cleaned author map in the QA report.

## Regression fixed in v2.4

The 24-article release exposed a defect where scanning raw `AUTOR` paragraphs pulled role and institution lines into the TOC. The active fix is: **TOC author display uses a cleaned author map; `AUTOR` is a signal, not a source by itself.**
