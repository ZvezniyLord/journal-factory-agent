from astra_journal.role_classifier import ParagraphRole, deterministic_role


def test_reference_typo_is_recognized_as_reference_heading() -> None:
    result = deterministic_role("REFERENS")
    assert result is not None
    assert result.role == ParagraphRole.REF_TITLE


def test_table_caption_is_recognized() -> None:
    result = deterministic_role("Таблиця 2. Результати")
    assert result is not None
    assert result.role == ParagraphRole.TABLE_CAPTION


def test_figure_caption_is_recognized() -> None:
    result = deterministic_role("Рис. 3. Схема")
    assert result is not None
    assert result.role == ParagraphRole.FIGURE_CAPTION


def test_supervisor_is_not_author_role() -> None:
    result = deterministic_role("Науковий керівник: Іваненко І. І.")
    assert result is not None
    assert result.role == ParagraphRole.SUPERVISOR
