---
name: naukainfo-toc-body-author-sync
description: Rebuilds TOC author rows from final AUTOR paragraphs after header cleanup and fails on stale, missing, duplicated, or role-only author entries.
version: "2.9.0"
---
# TOC/body synchronization

The TOC is rebuilt only after all final `AUTOR`/`pip` decisions. Its author row must exactly equal the ordered `AUTOR` paragraphs between UDC and title for that article.

Never reuse stale author text from an earlier TOC. Degrees and roles such as `Hon. PhD` or `член-кореспондент...` must not appear in the TOC. Scientific supervisors marked as participating people do appear as `AUTOR`.

Run `scripts/audit_toc_author_sync.py` after the final TOC rebuild. Any missing coauthor, extra role, duplicate, or title mismatch blocks release.
