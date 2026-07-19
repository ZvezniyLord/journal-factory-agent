# Next Chat Task — Manifest, Dashboard, and Browser Acceptance

## User verdict

The current root `index.html` is a failed acceptance result. It is not a usable Journal Factory entry point because the operator cannot enter/select the source and output paths, review the workspace, start the real run, or see where the manifest and dashboard artifacts were created.

Previous automated test counts do not override this user-visible failure.

## Real local source

Use the user-approved archive recorded in `docs/LOCAL_TEST_MATERIALS.md`:

```text
N:\Конференції\Конференції_zip\95_м_Оксфорд,_Велика_Британія,_6_8_лютого_2026_року.zip
```

Do not alter the archive.

## Required task

A fresh Codex chat must perform a new Phase 1 acceptance/fix cycle covering the Browser UI, Dashboard, Workspace Driver, and their real local integration. It must resolve ownership through `CORE_WORK_REGISTRY.yaml`; when the required work crosses existing core scopes, it must register a narrowly defined integration/acceptance work item rather than silently editing several released cores without a lock.

The chat must:

1. Work from the user's actual local repository and synchronize it safely with `origin/main` without destroying staged or uncommitted user changes.
2. Reproduce the user's finding by launching the current product locally and inspecting `index.html` in a real browser.
3. Mark the prior browser acceptance as failed in the appropriate plan/registry evidence.
4. Add failing tests before implementation for the missing visible workflow.
5. Make the root browser entry point usable. It must visibly provide:
   - source archive/folder path input or a local selection bridge;
   - output-parent path input or selection bridge;
   - journal number input/review;
   - computed workspace path;
   - validation feedback;
   - create/start control;
   - current run state and core progress;
   - links or exact paths to generated manifest, dashboard state, reports, and output folders;
   - structured error display without Python traceback.
6. Use the real archive above for a local run.
7. Verify whether the required workspace files are actually created, including at minimum:
   - `reports/run_manifest.json`;
   - `reports/action_log.jsonl`;
   - `reports/path_registry.json`;
   - `reports/report_registry.json`;
   - `reports/run_summary.html`;
   - the persisted Dashboard state/report defined by the implementation.
8. Parse every JSON/JSONL artifact and verify that recorded source/output paths, run ID, journal number, statuses, timestamps, and report/file references are coherent.
9. Test browser behavior at desktop and narrow/mobile widths and capture local evidence.
10. Run focused tests, the full available suite, the real local run, artifact inspection, and repository acceptance.
11. Leave all resulting source files, tests, logs, screenshots, and generated acceptance artifacts visible on the user's computer.
12. Commit and push only after local verification, then fetch and verify the remote result.
13. Do not report `PASS` until the user can perform the workflow manually from the browser. End with exact manual steps and `STATUS: WAITING FOR USER`.

## Definition of failure

The cycle is `FAIL` if any of these occurs:

- `index.html` is only a status screen or command mock-up;
- paths cannot be entered or selected;
- the real archive is not used;
- the workspace or required manifest/report files are absent;
- displayed paths do not point to real files;
- only test adapters are exercised instead of the local integration;
- the browser must be edited manually or commands must replace the normal UI workflow;
- the user-visible local checkout is not updated;
- a traceback, silent failure, or false success is shown.

## Command for the fresh chat

```text
Open AGENTS.md and follow its mandatory navigation exactly. Then read docs/LOCAL_TEST_MATERIALS.md and docs/NEXT_CHAT_MANIFEST_DASHBOARD_ACCEPTANCE.md completely. Treat the user's verdict as authoritative: the current index.html failed acceptance and previous automated PASS WITH WARNINGS does not count as browser acceptance. Resolve this work through CORE_WORK_REGISTRY.yaml, register a narrow integration/acceptance work item if no single existing core legally owns the whole fix, acquire and remotely verify its lock, and work in the user's actual local repository. Reproduce the failure in a real browser, create failing tests, fix the visible source/output path workflow, and perform a real local run using N:\Конференції\Конференції_zip\95_м_Оксфорд,_Велика_Британія,_6_8_лютого_2026_року.zip. Verify that run_manifest.json, action_log.jsonl, path_registry.json, report_registry.json, run_summary.html, and persisted dashboard state are genuinely created and parse correctly. Keep all files and evidence visible on the user's computer, run focused and full tests plus artifact inspection, push only after local verification, and finish with exact browser manual-test steps and STATUS: WAITING FOR USER. Do not declare PASS before the user manually confirms the browser workflow.
```
