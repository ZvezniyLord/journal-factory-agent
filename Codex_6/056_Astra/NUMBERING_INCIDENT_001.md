# NUMBERING_INCIDENT_001.md

## Status
RELEASE BLOCKER.

## Reproduction
The synthetic golden fixture passed pre-Word structural checks and Word COM save-close-reopen itself succeeded.

Before Word:
- article 1 references used numId 101;
- article 2 references used numId 102;
- each had startOverride=1;
- each numId referenced a separate but structurally identical abstractNum.

After Microsoft Word SaveAs2 + close + reopen:
- Word canonicalized/deduplicated the numbering definitions;
- all reference paragraphs were rebound to one numId;
- article 2 continued as 3, 4 instead of restarting at 1.

## Root cause hypothesis
Separate numId values alone are not sufficient when the backing abstract numbering definitions are semantically identical and lack stable unique list identity metadata. Word may deduplicate them during save.

## Required fix
Do not claim a numbering strategy is valid until Microsoft Word roundtrip proves that:
- first reference in every article has ListValue=1;
- each article's bibliography remains an independent logical list after Save/Close/Reopen;
- no manual "Start at 1" repair is needed.

## Candidate strategies to test
A. Existing strategy (control): separate identical abstractNum + separate num + startOverride=1.
B. Shared abstractNum + distinct num instances, with restart only on subsequent article instances.
C. Per-article abstractNum with unique Word list identity metadata (unique nsid and tmpl) + per-article num.
D. C plus explicit lvlOverride/startOverride=1 on each per-article num.

The accepted production strategy is whichever survives Word COM roundtrip and Word-visible ListFormat.ListValue probes.

Do not optimize for pretty numbering.xml. Optimize for stable Microsoft Word behavior.
