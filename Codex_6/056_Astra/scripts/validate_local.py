from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import venv
from pathlib import Path


def _run(cmd: list[str], *, cwd: Path) -> dict:
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "output": proc.stdout[-20000:],
    }


def _ensure_venv(root: Path) -> Path:
    if os.name == "nt":
        python = root / ".venv" / "Scripts" / "python.exe"
    else:
        python = root / ".venv" / "bin" / "python"
    if not python.exists():
        venv.EnvBuilder(with_pip=True).create(root / ".venv")
    if not python.exists():
        raise RuntimeError(f"Local venv python was not created: {python}")
    return python


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Astra locally")
    parser.add_argument(
        "--root",
        default=r"X:\CODEX_5.5_redactor\Codex_6\056_Asttra",
    )
    parser.add_argument("--skip-word", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    run_dir = root / "runs" / "validation"
    run_dir.mkdir(parents=True, exist_ok=True)
    py = _ensure_venv(root)

    result = {
        "task": "astra_056_local_validation",
        "root": str(root),
        "python_path": str(py),
        "steps": {},
    }

    install = _run([str(py), "-m", "pip", "install", "-e", ".[dev]"], cwd=root)
    result["steps"]["install"] = install
    if install["returncode"] != 0:
        result["status"] = "fail"
        _write(run_dir, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    tests = _run([str(py), "-m", "pytest", "-q"], cwd=root)
    result["steps"]["pytest"] = tests
    if tests["returncode"] != 0:
        result["status"] = "fail"
        _write(run_dir, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 3

    fixture = run_dir / "golden.docx"
    make_fixture = _run(
        [str(py), "-m", "astra_journal.cli", "make-golden-fixture", str(fixture)],
        cwd=root,
    )
    result["steps"]["golden_fixture"] = make_fixture
    if make_fixture["returncode"] != 0:
        result["status"] = "fail"
        _write(run_dir, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 4

    audit_json = run_dir / "golden_audit.json"
    audit = _run(
        [
            str(py),
            "-m",
            "astra_journal.cli",
            "audit-docx",
            str(fixture),
            "--json",
            str(audit_json),
        ],
        cwd=root,
    )
    result["steps"]["audit"] = audit
    if audit["returncode"] != 0:
        result["status"] = "fail"
        _write(run_dir, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 5

    if not args.skip_word:
        word_out = run_dir / "golden_word_roundtrip.docx"
        word_json = run_dir / "word_roundtrip.json"
        word = _run(
            [
                str(py),
                "-m",
                "astra_journal.cli",
                "word-roundtrip",
                str(fixture),
                str(word_out),
                "--json",
                str(word_json),
            ],
            cwd=root,
        )
        result["steps"]["word_roundtrip"] = word
        if word["returncode"] == 3:
            result["status"] = "blocked"
            _write(run_dir, result)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 6
        if word["returncode"] != 0:
            result["status"] = "fail"
            _write(run_dir, result)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 7

    result["status"] = "ok"
    _write(run_dir, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _write(run_dir: Path, result: dict) -> None:
    (run_dir / "local_validation.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
