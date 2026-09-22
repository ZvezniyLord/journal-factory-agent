from pathlib import Path

from astra_journal.run_model import resolve_final_destination


def test_destination_uses_conference_folder(tmp_path: Path) -> None:
    result = resolve_final_destination(
        output_root=tmp_path,
        conference_number="153",
    )
    assert result.parent.name == "153"
    assert result.name == "153-final.docx"


def test_destination_versions_existing_file(tmp_path: Path) -> None:
    folder = tmp_path / "153"
    folder.mkdir()
    (folder / "153-final.docx").write_bytes(b"x")
    result = resolve_final_destination(
        output_root=tmp_path,
        conference_number="153",
    )
    assert result.name == "153-final-v2.docx"
