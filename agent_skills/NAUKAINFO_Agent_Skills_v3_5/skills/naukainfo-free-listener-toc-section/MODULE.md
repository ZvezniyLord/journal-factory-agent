---
name: naukainfo-free-listener-toc-section
description: Adds the published SPECIAL THANKS listener block as the final two rows of the same three-column TABLE OF CONTENTS table.
license: Proprietary project skill
compatibility: NAUKAINFO manifest + ETALON TOC; Дирежор project only.
metadata:
  author: naukainfo
  version: "3.3.0"
---

# Source of truth

Free listeners come only from the verified `LISTENERS` manifest group. They are non-article participants and do not create article pages, UDC, article numbering, or page numbers.

# Exact published heading

Use this exact visible text, including the final colon:

`SPECIAL THANKS FOR ACTIVE PARTICIPATION IN THE SCIENTIFIC AND PRACTICAL CONFERENCE ARE EXTENDED TO THE FOLLOWING PARTICIPANTS:`

Do not replace it with `FREE LISTENERS`, a Ukrainian translation, a singular form, or an improvised heading.

# TOC table contract

1. Append the listener block after the final article/title row **inside the existing three-column TOC Word table**.
2. Create one merged section row spanning all three columns. The heading paragraph uses actual ETALON style `TabSEC` (`Tab_SEC`), centered, with zero left/first-line indent and no tab stops.
3. Create exactly one following three-cell row:
   - column 1: empty, actual style `TabTaitl`;
   - column 2: all verified listener names in manifest order joined with comma + space (`Name 1, Name 2, Name 3`), actual style `TabPIP` (`Tab_PIP`);
   - column 3: empty, actual style `TabTaitl`.
4. The listener names paragraph must have effective left indent 0, first-line indent 0, no tabs, no numbering and no page number.
5. Do not create one row per listener. Do not continue article numbering. Do not add listener report titles unless a later explicit business rule defines a separate published format.
6. Remove stale listener paragraphs or pages outside the TOC table before release.
7. Rebuild from the final manifest on every full release; duplicate names and stale names are blockers.

# QA / fail closed

PASS requires: one exact heading row, one comma-separated names row, `TabSEC` + `TabPIP` actual style IDs, listener count equal to manifest count, zero listener paragraphs outside the TOC table, and no number/page value in the listener row.
