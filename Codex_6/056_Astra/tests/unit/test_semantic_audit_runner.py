import json
from pathlib import Path
from types import SimpleNamespace

import astra_journal.semantic_audit_runner as runner
from astra_journal.hermes_client import HermesEndpoint


class FakeRouter:
    calls = []

    def __init__(self, endpoints, **kwargs):
        self.endpoints = endpoints

    def chat_json(self, *, task, instruction, max_tokens):
        self.calls.append((task, instruction, max_tokens))
        source = "a.docx" if '"path":"a.docx"' in instruction else "b.docx"
        parsed = {
            "task": "article_semantic_audit",
            "status": "ok",
            "confidence": 0.99,
            "result": {
                "source_path": source,
                "author": "Author",
                "coauthors": [],
                "supervisor": None,
                "affiliation": None,
                "position_degree": None,
                "orcid": None,
                "title": "Title",
                "udc_status": "present",
                "abstract_status": "present",
                "keywords_status": "present",
                "table_caption_count": 0,
                "figure_caption_count": 0,
                "ref_title": "REFERENCES",
                "references_region": "present",
                "section_raw": "Section",
                "section_mapping_status": "review",
                "ambiguities": [],
            },
            "evidence": [],
            "warnings": [],
        }
        endpoint = self.endpoints[0][1]
        return SimpleNamespace(
            worker="main",
            endpoint=endpoint,
            parsed=parsed,
            raw={"choices": [{"message": {"content": json.dumps(parsed)}}]},
            latency_s=0.01,
            attempts=[{"status": "ok"}],
        )


def _record(path: str) -> dict:
    return {
        "path": path,
        "sha256": "a" * 64,
        "paragraph_count": 10,
        "table_count": 0,
        "media_count": 0,
        "hyperlink_count": 0,
        "title_candidates": ["Title"],
        "semantic_signals": {
            "head": [{"index": 0, "text": "Author", "style_name": "Normal"}],
            "tail": [{"index": 9, "text": "REFERENCES", "style_name": "Normal"}],
            "role_hits": [
                {
                    "index": 9,
                    "text": "REFERENCES",
                    "role": "REF_TITLE",
                    "confidence": 0.99,
                    "evidence": ["reference-heading"],
                }
            ],
            "role_counts": {"REF_TITLE": 1},
        },
    }


def test_runner_uses_fresh_one_article_calls_and_checkpoints(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "project"
    (root / "config").mkdir(parents=True)
    (root / "config" / "hermes_runtime.json").write_text(
        json.dumps(
            {
                "main": {
                    "openai_base_url": "http://main/v1",
                    "model": "model",
                    "context": 10000,
                    "role": "main",
                },
                "limits": {
                    "article_semantic_batch_size": 1,
                    "article_semantic_max_input_chars": 8000,
                    "article_semantic_max_request_chars": 12000,
                    "article_semantic_max_output_tokens": 800,
                    "article_semantic_max_retries": 0,
                    "article_semantic_max_new_articles_per_process": 1,
                    "timeout_seconds": 10,
                },
            }
        ),
        encoding="utf-8",
    )

    manifest = {
        "materials": [
            {
                "excel_row": 2,
                "authors_raw": "A",
                "title_raw": "Title A",
                "section_raw": "Section",
                "match_status": "MATCHED",
                "matched_source": "a.docx",
            },
            {
                "excel_row": 3,
                "authors_raw": "B",
                "title_raw": "Title B",
                "section_raw": "Section",
                "match_status": "MATCHED",
                "matched_source": "b.docx",
            },
        ]
    }
    source_index = {"records": [_record("a.docx"), _record("b.docx")]}

    manifest_path = tmp_path / "manifest.json"
    source_path = tmp_path / "source.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    source_path.write_text(json.dumps(source_index), encoding="utf-8")

    FakeRouter.calls = []
    monkeypatch.setattr(runner, "HermesRouter", FakeRouter)

    first = runner.run_stateless_semantic_audit(
        root=root,
        manifest_path=manifest_path,
        source_index_path=source_path,
        run_dir=tmp_path / "run",
        max_new_articles=1,
    )
    assert first["status"] == "INCOMPLETE"
    assert first["completed"] == 1
    assert first["remaining"] == 1
    assert len(FakeRouter.calls) == 1
    assert "a.docx" in FakeRouter.calls[0][1]
    assert "b.docx" not in FakeRouter.calls[0][1]

    second = runner.run_stateless_semantic_audit(
        root=root,
        manifest_path=manifest_path,
        source_index_path=source_path,
        run_dir=tmp_path / "run",
        max_new_articles=1,
    )
    assert second["status"] == "PASS"
    assert second["completed"] == 2
    assert second["cached"] == 1
    assert second["remaining"] == 0
    assert len(FakeRouter.calls) == 2
    assert "b.docx" in FakeRouter.calls[1][1]
    assert (tmp_path / "run" / "semantic_audit.json").exists()
