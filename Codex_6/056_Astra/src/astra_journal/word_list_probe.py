from __future__ import annotations

from pathlib import Path
from typing import Any


class WordListProbeUnavailable(RuntimeError):
    pass


def probe_reference_list_values(
    path: str | Path,
    *,
    style_names: tuple[str, ...] = ("REFER",),
) -> dict[str, Any]:
    try:
        import win32com.client  # type: ignore
    except ImportError as exc:
        raise WordListProbeUnavailable("pywin32 is required") from exc

    source = Path(path).resolve()
    try:
        app = win32com.client.DispatchEx("Word.Application")
    except Exception as exc:
        raise WordListProbeUnavailable(f"Microsoft Word COM unavailable: {exc}") from exc

    doc = None
    rows: list[dict[str, Any]] = []
    try:
        app.Visible = False
        app.DisplayAlerts = 0
        doc = app.Documents.Open(
            str(source),
            ReadOnly=True,
            AddToRecentFiles=False,
            ConfirmConversions=False,
        )
        for index in range(1, doc.Paragraphs.Count + 1):
            paragraph = doc.Paragraphs(index)
            text = paragraph.Range.Text.replace("\r", "").replace("\x07", "").strip()
            if not text:
                continue
            try:
                style_name = str(paragraph.Range.Style.NameLocal)
            except Exception:
                style_name = str(paragraph.Range.Style)
            if style_name not in style_names:
                continue

            try:
                list_type = int(paragraph.Range.ListFormat.ListType)
            except Exception:
                list_type = None
            try:
                list_value = int(paragraph.Range.ListFormat.ListValue)
            except Exception:
                list_value = None
            try:
                list_string = str(paragraph.Range.ListFormat.ListString)
            except Exception:
                list_string = ""

            rows.append(
                {
                    "paragraph_index": index,
                    "style": style_name,
                    "text": text,
                    "list_type": list_type,
                    "list_value": list_value,
                    "list_string": list_string,
                }
            )
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

    return {
        "path": str(source),
        "reference_paragraphs": rows,
    }
