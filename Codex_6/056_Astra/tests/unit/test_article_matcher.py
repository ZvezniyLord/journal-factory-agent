from astra_journal.article_matcher import deterministic_match, title_similarity


def test_exact_title_match() -> None:
    assert title_similarity(
        "Психологічні детермінанти довірчих відносин",
        "ПСИХОЛОГІЧНІ ДЕТЕРМІНАНТИ ДОВІРЧИХ ВІДНОСИН",
    ) == 1.0


def test_title_based_match_prefers_correct_source() -> None:
    records = [
        {"path": "a.docx", "title_candidates": ["Інша стаття"]},
        {"path": "b.docx", "title_candidates": ["Право державних службовців бути не на зв'язку"]},
    ]
    result = deterministic_match(
        "Право державних службовців бути не на зв’язку",
        records,
        auto_accept=0.9,
    )
    assert result["status"] == "MATCHED"
    assert result["match"] == "b.docx"
