from __future__ import annotations

from pathlib import Path


class DocConversionBlocked(RuntimeError):
    pass


def convert_doc_to_docx(source: str | Path, destination: str | Path) -> Path:
    src = Path(source).resolve()
    dst = Path(destination).resolve()
    if not src.exists():
        raise DocConversionBlocked(f"SOURCE_NOT_FOUND:{src}")
    if src.suffix.casefold() != ".doc":
        raise DocConversionBlocked(f"NOT_LEGACY_DOC:{src}")
    dst.parent.mkdir(parents=True, exist_ok=True)

    try:
        import win32com.client  # type: ignore
    except ImportError as exc:
        raise DocConversionBlocked("PYWIN32_UNAVAILABLE") from exc

    app = None
    doc = None
    try:
        app = win32com.client.DispatchEx("Word.Application")
        app.Visible = False
        app.DisplayAlerts = 0
        doc = app.Documents.Open(
            str(src),
            ReadOnly=True,
            AddToRecentFiles=False,
            ConfirmConversions=False,
        )
        # 16 = wdFormatDocumentDefault (.docx)
        doc.SaveAs2(str(dst), FileFormat=16, AddToRecentFiles=False)
        doc.Close(SaveChanges=False)
        doc = None
    except Exception as exc:
        raise DocConversionBlocked(f"WORD_CONVERSION_FAILED:{exc}") from exc
    finally:
        if doc is not None:
            try:
                doc.Close(SaveChanges=False)
            except Exception:
                pass
        if app is not None:
            try:
                app.Quit()
            except Exception:
                pass

    if not dst.exists():
        raise DocConversionBlocked("CONVERTED_DOCX_NOT_CREATED")
    return dst
