---
name: naukainfo-versioned-backup-release
description: Preserves immutable versioned backups of source documents, prior journal releases, skills packages, and QA reports before every repair or rebuild.
version: "2.9.0"
---
# Versioned backups

Never overwrite the source article, ETALON, prior release, prior skills ZIP, or prior QA report. Every repair produces a new versioned filename and records its parent input.

Minimum retained chain:
- source/original article archive;
- last accepted journal release;
- current stage and final release;
- previous and current skills archives;
- QA reports and recovery artifacts.

A cleanup may remove caches, temporary renders, and failed disposable stages only after the new release passes QA. Versioned backups are not deleted automatically.
