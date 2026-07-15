from journal_factory.audit import ArticleAudit, release_gate


def test_release_gate_reviews_warning_issues() -> None:
    gate = release_gate(
        {"status": "READY", "blockers": []},
        [
            ArticleAudit(
                path="article.docx",
                status="WARN",
                text_chars=5000,
                has_udc=False,
                has_references=False,
                object_risk="unchecked_in_mvp",
                issues=["missing_udc_marker", "missing_references_marker"],
            )
        ],
    )

    assert gate["status"] == "REVIEW"
    assert gate["production_ready"] is False
    assert "missing_udc_marker:article.docx" in gate["warnings"]


def test_diagnostic_mvp_never_returns_production_pass() -> None:
    gate = release_gate({"status": "READY", "blockers": []}, [], mode="diagnostic-mvp")

    assert gate["status"] == "REVIEW"
    assert gate["production_ready"] is False
    assert "diagnostic_mvp_cannot_produce_production_pass" in gate["warnings"]
