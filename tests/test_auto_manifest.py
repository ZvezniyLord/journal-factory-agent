from pathlib import Path
from types import SimpleNamespace
import json

from journal_factory import auto_manifest


def test_legacy_doc_reader_uses_short_temporary_paths(
    tmp_path: Path,
    monkeypatch,
) -> None:
    source = tmp_path / ("participant-" + "x" * 120) / "application.doc"
    source.parent.mkdir()
    source.write_bytes(b"legacy")
    observed: dict[str, str] = {}

    def fake_run(command, **kwargs):
        payload = json.loads(Path(kwargs["env"]["JF_LEGACY_INPUT"]).read_text(encoding="utf-8"))
        request = payload[0]
        observed.update(request)
        assert Path(request["read"]).name == "legacy_0000.doc"
        assert Path(request["read"]).read_bytes() == b"legacy"
        Path(kwargs["env"]["JF_LEGACY_OUTPUT"]).write_text(
            json.dumps({"results": {request["source"]: "application text"}, "errors": []}),
            encoding="utf-8",
        )
        return SimpleNamespace(returncode=0, stderr="")

    monkeypatch.setattr(auto_manifest.sys, "platform", "win32")
    monkeypatch.setattr(auto_manifest.subprocess, "run", fake_run)

    texts, method, errors = auto_manifest._extract_legacy_doc_texts([source])

    assert observed["source"] == str(source.resolve())
    assert texts[str(source.resolve())] == "application text"
    assert method == "word_com_read_only_isolated"
    assert errors == []
