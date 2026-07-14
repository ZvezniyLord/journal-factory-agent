---
name: naukainfo-multilingual-marker-library
description: Provides conservative multilingual recognition for figure/table captions and reference headings without rewriting article prose.
version: "2.9.0"
---
# Marker library

Use `scripts/normalize_multilingual_markers.py` as the shared classifier.

Supported examples:
- figures: `Рис.`, `Рисунок`, `Мал.`, `Fig.`, `Figure`, `Abb.`, `Abbildung`, `Rys.`, `Obr.`, `AGD1`;
- tables: `Таблиця`, `Table`, `Tabelle`, `Tabela`, `Tabulka`, `Tableau`, with or without a number;
- references: Ukrainian source/literature variants, English `References/Bibliography`, German `Literaturverzeichnis/Quellenverzeichnis`, and common Polish/Czech/Slovak/French variants.

Strip a leading section number only for marker classification, e.g. `14. Список використаних джерел`. Do not alter ordinary prose that merely contains these words.

Canonical output follows article language: Ukrainian stamp for Ukrainian articles, `REFERENCES` for English, standard German distinction for German articles.
