from astra_journal.reference_policy import (
    EN_CANONICAL,
    UK_CANONICAL,
    normalize_reference_heading,
)


def test_ukrainian_variants_normalize_to_standard_heading() -> None:
    for value in ("Література", "Список літератури", "Використані джерела"):
        result = normalize_reference_heading(value)
        assert result.matched
        assert result.canonical == UK_CANONICAL


def test_english_typo_normalizes_to_references() -> None:
    result = normalize_reference_heading("Referens")
    assert result.matched
    assert result.canonical == EN_CANONICAL


def test_reference_heading_not_applied_to_arbitrary_text() -> None:
    result = normalize_reference_heading("The reference model is described below")
    assert not result.matched
