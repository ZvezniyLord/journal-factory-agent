# База знань Journal Builder

База знань допомагає deterministic parser розпізнавати шапки, секції та службові маркери. Вона не є джерелом авторського тексту й не має права переписувати статті.

## Що накопичуємо

- прізвища, імена, ініціали та транслітерації;
- наукові ступені, звання й посади;
- кафедри, факультети, установи та скорочення;
- міста, регіони й країни;
- section headings;
- UDC, DOI та ORCID patterns;
- annotation/abstract/keywords/references markers;
- figure/table/caption/source markers;
- observed header layouts;
- failure classes і результати rules;
- підтверджені aliases.

## Provenance

Кожен запис зберігає:

- `conference_id`;
- `source_path`;
- `source_sha256`;
- `evidence_text` або evidence span;
- `extraction_method`;
- `confidence`;
- `review_status`;
- `created_at`;
- `ruleset_version`.

Без provenance запис не потрапляє у production lookup.

## Рівні довіри

- `CONFIRMED` — підтверджено manifest або кількома незалежними джерелами;
- `OBSERVED` — знайдено в реальному source, але ще не перевірено;
- `SUGGESTED` — запропоновано LLM або heuristic;
- `REJECTED` — хибний або небезпечний запис.

Production auto-apply використовує тільки `CONFIRMED`. `OBSERVED` може підвищувати score, але не створює незворотних змін. `SUGGESTED` завжди потребує review.

## Імпорт із конференцій

Conference agent залишає:

```text
knowledge_base/imports/conference_<NNN>.jsonl
```

Кожен рядок — один observation. Integrator перевіряє duplicates, aliases, provenance і counterexamples перед merge у SQLite.

## Використання

1. Parser збирає deterministic candidates.
2. SQLite lookup додає aliases і відомі entity types.
3. Rule engine оцінює confidence.
4. За низької впевненості створюється REVIEW або обмежений LLM request.
5. Після підтвердження observation може стати `CONFIRMED`.

## Заборони

- не зберігати весь авторський body як словник;
- не вважати частотність доказом істини;
- не виправляти прізвище за схожістю без provenance;
- не перетворювати LLM suggestion на confirmed record автоматично;
- не створювати rules, прив’язані до номера конференції.
