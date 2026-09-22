from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .word_stability import inspect_docx


class WordComUnavailable(RuntimeError):
    pass


def _word():
    try:
        import win32com.client  # type: ignore
    except ImportError as exc:
        raise WordComUnavailable(
            "pywin32 is required for Microsoft Word COM validation"
        ) from exc
    try:
        return win32com.client.DispatchEx("Word.Application")
    except Exception as exc:
        raise WordComUnavailable(f"Microsoft Word COM is unavailable: {exc}") from exc


def roundtrip_word(
    source: str | Path,
    destination: str | Path,
    *,
    visible: bool = False,
) -> dict[str, Any]:
    source_path = Path(source).resolve()
    dest_path = Path(destination).resolve()
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    before = inspect_docx(source_path)
    app = _word()
    doc = None
    try:
        app.Visible = bool(visible)
        app.DisplayAlerts = 0
        doc = app.Documents.Open(
            str(source_path),
            ReadOnly=False,
            AddToRecentFiles=False,
            ConfirmConversions=False,
        )
        doc.SaveAs2(str(dest_path), FileFormat=16, AddToRecentFiles=False)
        doc.Close(SaveChanges=False)
        doc = None

        doc = app.Documents.Open(
            str(dest_path),
            ReadOnly=True,
            AddToRecentFiles=False,
            ConfirmConversions=False,
        )
        doc.Close(SaveChanges=False)
        doc = None
    finally:
        if doc is not None:
            try:
                doc.Close(SaveChanges=False)
            except Exception:
                pass
        try:
            app.Quit()
        except Exception:
            pass

    after = inspect_docx(dest_path)
    return {
        "status": "PASS",
        "source": str(source_path),
        "destination": str(dest_path),
        "before": before,
        "after": after,
    }


def write_roundtrip_report(path: str | Path, report: dict[str, Any]) -> None:
    Path(path).write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
