---
name: naukainfo-skill-map-change-log
description: Records verified skill changes, successful and failed approaches, active sequence, regression evidence, and short user-facing release notes.
version: "2.9.0"
---

# naukainfo-skill-map-change-log

## Purpose
Keep the Agent Skills library operational, ordered, and non-redundant during NAUKAINFO Journal Builder work.

## Mandatory sequence
After each confirmed correction or regression:
1. Name the affected skill(s).
2. Record what worked.
3. Record what failed.
4. Remove failed approaches from active decision logic.
5. Update the skill map and changelog.
6. Add/adjust deterministic tests when the rule is stable.
7. Return a short user-facing skill report.

## Active rule
Do not keep obsolete logic merely because it once worked visually. Visual similarity is not enough; style IDs, outline levels, numbering IDs, object preservation, and text fidelity must be verified.
