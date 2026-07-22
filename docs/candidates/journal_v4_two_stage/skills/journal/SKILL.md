---
name: journal-v4-two-stage-draft
description: Нова чернеткова MD-логіка Journal Factory: непрозорий незмінний ETALON-shell, механічне перенесення статей із єдиною нормалізацією 11 pt / 1.0, потім read-only JSON-розмітка технічних зон.
license: Proprietary project skill
compatibility: Journal Factory; DOC/DOCX; OOXML; local browser dashboard.
metadata:
  author: naukainfo
  version: "4.0.0-draft.1"
  status: "candidate-not-active"
  scope: "Дирежор / NAUKAINFO Journal Builder only"
---

# ЖУРНАЛ v4 — ДВОЕТАПНА ЧЕРНЕТКОВА ЛОГІКА

## 0. Статус версії

Це кандидат нової логіки. Він не змінює `ACTIVE_RELEASE.json` і не активується у production без окремого рішення користувача.

## 1. Абсолютне правило ETALON-shell

ETALON є непрозорою незмінною оболонкою.

- Перші сторінки та остання службова сторінка беруться тільки з ETALON.
- Під час звичайного run вони **не скануються, не аналізуються, не нормалізуються і не перевіряються**.
- Програма не перебудовує обкладинку, титульні дані, фінальну сторінку, секції, колонтитули або нумерацію.
- Дозволена рівно одна точка запису: точний bookmark/content-control tag `JOURNAL_CONTENT_SLOT`, заданий у `template_shell_contract.json`.
- У slot вставляється строго:
  1. таблиця змісту конференції;
  2. один page break;
  3. тіло чернетки журналу.
- Якщо точний slot відсутній або дублюється — `BUILD BLOCKED: CONTENT_SLOT_INVALID`.
- Заборонено шукати місце вставки за номером сторінки, номером абзацу, текстом обкладинки чи евристикою.

Це правило автоматично усуває повторне створення першої/останньої сторінки та випадкове додавання номера на останній сторінці: protected suffix не редагується взагалі.

## 2. Після Dashboard: Stage 1 — механічна чернетка

Статті обробляються окремо, послідовно, у порядку реєстру.

Для кожної статті:

1. створити робочу копію;
2. виділити **весь вміст саме цієї статті**, а не всього master-журналу;
3. застосувати лише:
   - font size `11 pt`;
   - line spacing `1.0 / single`;
4. зберегти статтю без інших змін;
5. перенести повну статтю до `draft_article_body`;
6. зафіксувати source hash, normalized hash і порядок вставки.

На Stage 1 заборонено:

- переписувати або виправляти текст;
- розбивати чи зливати абзаци;
- замінювати `Enter`/`Shift+Enter`;
- видаляти порожні абзаци;
- класифікувати шапку;
- призначати стилі ролям;
- рухати таблиці, рисунки, підписи чи джерела;
- редагувати DOI/UDC/авторів/установи;
- застосовувати `Ctrl+A` до master-журналу або ETALON-shell.

Результат Stage 1 — **механічний draft**, а не фінальний журнал.

## 3. Stage 2 — технічні зони та JSON

Stage 2 працює read-only відносно тексту. Він не змінює DOCX, а створює JSON-карту структури кожної статті.

Обов'язкові класи зон:

- `identifier.udc`, `identifier.doi`;
- `header.person`;
- `header.degree`, `header.academic_title`, `header.position`;
- `header.institution`, `header.department`, `header.location`;
- `header.orcid`, `header.contact`;
- `header.supervisor`, `header.language_supervisor`;
- `header.title`;
- `body.annotation`, `body.keywords`, `body.section_heading`, `body.paragraph`;
- `object.table`, `object.table_caption`;
- `object.figure`, `object.figure_caption`, `object.source_note`;
- `references.heading`, `references.entry`;
- `unknown`.

Кожний блок зберігає:

- точний source locator;
- порядок;
- original text або object reference;
- SHA-256 тексту;
- confidence;
- deterministic/registry/corpus/LLM/operator decision source;
- evidence;
- `resolved`, `review` або `unresolved`.

Кожна людина у шапці є окремою сутністю. До неї прив'язуються блоки імені, ступеня, звання, посади, установи, місця та ідентифікаторів. Рядок установи не може автоматично ставати продовженням посади або імені.

## 4. Порядок розпізнавання

1. точний marker lexicon;
2. позиція та OOXML-контейнер;
3. реєстр/Excel;
4. словники людей, професій, ступенів, посад, установ і географії;
5. частотні патерни корпусу;
6. локальна LLM тільки для невирішеної неоднозначності;
7. operator review при низькій упевненості.

LLM не має права змінювати документ. Вона повертає лише структурований результат за JSON Schema.

## 5. Частотна база маркерів

Корпусна база міститься у `data/structural_markers_v1.json`.

Рівні:

- Tier A: сімейство зустрічається у `>=90%` статей — сильна межова ознака;
- Tier B: `70–89.9%` — сильна допоміжна ознака;
- Tier C: `<70%` — лише умовна ознака, відсутність нічого не доводить.

Не можна вимагати `Анотацію`, `Ключові слова`, `Висновки`, DOI, ORCID, таблицю чи рисунок від кожної статті лише тому, що такий marker є у словнику.

## 6. Мінімальні артефакти

Для кожної статті:

- `articles_raw/<article_id>.*`;
- `articles_transformed/<article_id>__stage1.docx`;
- `reports/articles/<article_id>__stage1.json`;
- `reports/articles/<article_id>__zones.json`.

Для run:

- `reports/template_shell_contract.json`;
- `reports/corpus_marker_version.json`;
- `final/JOURNAL_<number>__DRAFT.docx`.

## 7. Gates

Stage 1 PASS:

- 11 pt і 1.0 застосовані до редагованого тексту статті;
- lexical content mutations = 0;
- абзаци, таблиці, рисунки та порядок не змінені;
- ETALON protected prefix/suffix не редагувалися.

Stage 2 PASS:

- JSON відповідає `article_technical_zones.schema.json`;
- усі source elements покриті блоками або `unknown`;
- немає overlap/order corruption;
- невпевнені блоки не перетворені на PASS.

Draft PASS:

- зміст вставлений тільки у `JOURNAL_CONTENT_SLOT`;
- після змісту рівно один page break;
- статті вставлені в заданому порядку;
- draft явно позначений як draft;
- `ACTIVE_RELEASE.json` не змінено.

## 8. Done when

Створено незмінний ETALON-shell із точним content slot, механічний draft усіх статей із єдиними змінами 11 pt / 1.0, та валідну read-only JSON-карту технічних зон кожної статті. Жодна semantic correction або production formatting у цю версію не входить.
