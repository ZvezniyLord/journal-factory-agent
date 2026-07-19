# Local Test Materials

This file records user-approved local paths for real-run and acceptance testing.

## Canonical raw conference archive

Use this exact Windows path as the primary real source archive for manifest, workspace, discovery, dashboard, and end-to-end acceptance checks:

```text
N:\Конференції\Конференції_zip\95_м_Оксфорд,_Велика_Британія,_6_8_лютого_2026_року.zip
```

Rules for Codex agents:

1. Treat the path as user-provided test input, not as repository content.
2. Verify that the drive and file exist before testing.
3. Do not modify, rename, move, or overwrite the archive.
4. Extract or copy only into a disposable test workspace or the product workspace selected by the user.
5. Record the resolved source path, archive size, SHA-256 when practical, extraction destination, discovered files, and all generated manifest/report paths.
6. Use this archive for a real local run whenever the task concerns source selection, workspace creation, manifest creation, dashboard state, or the browser entry point.
7. If the path is unavailable in the active local environment, report `STATUS: BLOCKED — RAW MATERIAL PATH UNAVAILABLE` and show the exact failed check.

## Current user acceptance finding

The current root `index.html` is rejected by the user as non-functional for normal operation. It does not provide the required controls for entering or selecting source and output paths and does not demonstrate creation of the expected workspace manifest and dashboard state.

A future acceptance cycle must not mark the browser entry point as passing until a user can locally:

- enter or select the source archive/folder;
- enter or select the output parent;
- review the journal number and computed workspace path;
- start the local run;
- see explicit success or structured failure;
- locate and inspect the generated manifest and dashboard state/report files.
