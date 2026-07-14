---
name: naukainfo-numbering-definition-fidelity
description: Preserve author list numbering/bullets when assembling NAUKAINFO journals from multiple DOCX articles.
---

# NAUKAINFO Numbering Definition Fidelity

## Scope
Only for the Дирежор / NAUKAINFO Journal Builder project and only after explicit activation in the current project chat.

## Priority
This skill is subordinate to `naukainfo-author-body-fidelity` and supports it: author body lists must not silently change visual type, numbering scheme, bullet symbol, indentation, list level, or restart behavior.

## Business rule
When a paragraph in the author body has `w:numPr`, the final journal must preserve both:

1. the paragraph `numId/ilvl` relationship, and
2. the referenced `numbering.xml` definitions (`abstractNum`, `num`, `numFmt`, `lvlText`, paragraph indent, tabs, run font for bullets).

It is not enough to preserve the paragraph XML. If a multi-document merge remaps `numId` to an existing decimal list, a source bullet list can visually become `1.` / `2.`. This is a critical body-fidelity failure.

## Allowed exceptions
References are handled by `naukainfo-reference-block-fidelity` and must be rebuilt as independent decimal lists starting at 1 for each article. This exception applies only after the canonical heading `СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ:`.

## Required algorithm

1. Before article insertion, snapshot every source paragraph with `w:numPr`:
   - source article id / file;
   - paragraph text hash;
   - role: body list or reference entry;
   - `numId`, `ilvl`;
   - resolved `abstractNumId`;
   - `numFmt` and `lvlText` for that `ilvl`;
   - paragraph indentation and tab settings;
   - bullet run font if any.
2. During insertion, never reuse a destination `numId` unless its resolved definition is semantically identical.
3. If the destination already has that `numId`, allocate a fresh `numId` and copy the source `abstractNum`/`num` pair.
4. After assembly, audit every non-reference list paragraph against its source snapshot.
5. Stop the build if a body bullet became decimal or a decimal list became bullet.
6. Render and visually inspect the affected page.

## Regression example fixed in v2.7
In the Hnysiuk article, two body paragraphs beginning:

- `Пряма форма включає заробітну плату...`
- `Непряма матеріальна мотивація спрямована...`

were source bullet paragraphs (`numFmt=bullet`, `lvlText=-`) but after merging their `numId=41` pointed to a decimal abstract definition, rendering as `1.` and `2.`. The correct fix is to preserve/copy the source bullet numbering definition. No author text may be changed.

## Verification gate
A final DOCX passes only when:

- all body list paragraphs keep their original list kind and marker;
- all reference lists restart independently at 1;
- no manual body list is converted into references;
- render confirms the visible markers.
