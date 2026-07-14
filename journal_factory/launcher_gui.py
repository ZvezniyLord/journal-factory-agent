from __future__ import annotations

import os
import subprocess
import threading
import webbrowser
from dataclasses import dataclass
from pathlib import Path
import sys
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox


APP_URL = "http://127.0.0.1:8765"
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PYTHON = r"C:\Users\Vint\AppData\Local\Programs\Python\Python314\python.exe"
DOCKER_INPUT_CONTAINER = "/input/source"
DOCKER_OUTPUT_CONTAINER = "/app/build"


@dataclass
class LaunchState:
    server_proc: subprocess.Popen[str] | None = None
    docker_started: bool = False
    compose_started: bool = False
    last_error: str = ""


def _run(cmd: list[str], cwd: Path | None = None, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd or REPO_ROOT), text=True, capture_output=True, check=check)


def _configure_docker_paths(source: str, output: str, log: list[str]) -> None:
    if source:
        source_path = Path(source).resolve()
        if source_path.is_dir():
            os.environ["JOURNAL_INPUT_HOST"] = str(source_path)
            os.environ["JOURNAL_INPUT_CONTAINER"] = DOCKER_INPUT_CONTAINER
            os.environ["JOURNAL_ARCHIVE_CONTAINER"] = DOCKER_INPUT_CONTAINER
            log.append(f"Docker input folder: {source_path}")
        elif source_path.is_file():
            os.environ["JOURNAL_INPUT_HOST"] = str(source_path.parent)
            os.environ["JOURNAL_INPUT_CONTAINER"] = DOCKER_INPUT_CONTAINER
            os.environ["JOURNAL_ARCHIVE_CONTAINER"] = f"{DOCKER_INPUT_CONTAINER}/{source_path.name}"
            log.append(f"Docker input archive: {source_path}")
        else:
            log.append(f"input source does not exist: {source_path}")

    if output:
        output_path = Path(output).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
        os.environ["JOURNAL_OUTPUT_HOST"] = str(output_path)
        os.environ["JOURNAL_OUTPUT_DIR_CONTAINER"] = DOCKER_OUTPUT_CONTAINER
        log.append(f"Docker output folder: {output_path}")


def _candidate_python_executables() -> list[str]:
    candidates: list[str] = []

    if Path(DEFAULT_PYTHON).exists():
        candidates.append(DEFAULT_PYTHON)

    current = sys.executable
    if current:
        candidates.append(current)

    py = shutil.which("py")
    if py:
        candidates.extend([py, py])

    python = shutil.which("python")
    if python:
        candidates.append(python)

    uv = shutil.which("uv")
    if uv:
        candidates.append(uv)

    seen: set[str] = set()
    result: list[str] = []
    for item in candidates:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _probe_python(executable: str) -> bool:
    try:
        if Path(executable).name.lower() == "uv.exe":
            _run([executable, "run", "--no-project", "--with-requirements", "requirements.txt", "python", "-V"], check=True)
        else:
            _run([executable, "-V"], check=True)
        return True
    except Exception:
        return False


def _start_docker_and_compose(state: LaunchState, log: list[str]) -> None:
    docker = shutil.which("docker")
    if not docker:
        log.append("docker CLI not found; skipping container start")
        return
    try:
        _run([docker, "--version"], check=True)
    except Exception as exc:
        log.append(f"docker --version failed: {exc}")
        return

    desktop_candidates = [
        r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
        r"C:\Program Files\Docker\Docker\Docker Desktop",
    ]
    for candidate in desktop_candidates:
        if Path(candidate).exists():
            try:
                subprocess.Popen([candidate], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                state.docker_started = True
                log.append("Docker Desktop launch requested")
                break
            except Exception as exc:
                log.append(f"Docker Desktop launch failed: {exc}")

    compose = REPO_ROOT / "docker-compose.yml"
    if compose.exists():
        try:
            _run([docker, "compose", "up", "-d"], check=True)
            state.compose_started = True
            log.append("docker compose up -d completed")
        except subprocess.CalledProcessError as exc:
            log.append(exc.stdout or "")
            log.append(exc.stderr or "")
            log.append("docker compose up -d failed")


def _start_server(state: LaunchState, log: list[str]) -> None:
    if state.server_proc and state.server_proc.poll() is None:
        log.append("server already running")
        return
    python_executable = next((exe for exe in _candidate_python_executables() if _probe_python(exe)), None)
    if not python_executable:
        raise RuntimeError("No working Python executable found; check Python installation and PATH")

    if Path(python_executable).name.lower() == "uv.exe":
        cmd = [
            python_executable,
            "run",
            "--no-project",
            "--with-requirements",
            "requirements.txt",
            "python",
            "-m",
            "journal_factory.cli",
            "serve",
            "--host",
            "127.0.0.1",
            "--port",
            "8765",
        ]
    else:
        cmd = [
            python_executable,
            "-m",
            "journal_factory.cli",
            "serve",
            "--host",
            "127.0.0.1",
            "--port",
            "8765",
        ]
    state.server_proc = subprocess.Popen(cmd, cwd=str(REPO_ROOT), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log.append("server started")


def build_ui() -> tk.Tk:
    root = tk.Tk()
    root.title("Journal Factory Launcher")
    root.geometry("620x320")
    root.minsize(560, 280)

    state = LaunchState()
    status_var = tk.StringVar(value="Ready")
    source_var = tk.StringVar(value=os.environ.get("JOURNAL_ARCHIVE", ""))
    output_var = tk.StringVar(value=str(REPO_ROOT / "build"))
    source_kind = tk.StringVar(value="file")

    def pick_source() -> None:
        if source_kind.get() == "dir":
            path = filedialog.askdirectory(title="Select input folder")
        else:
            path = filedialog.askopenfilename(title="Select input archive", filetypes=[("ZIP archives", "*.zip"), ("All files", "*.*")])
        if path:
            source_var.set(path)

    def pick_output() -> None:
        path = filedialog.askdirectory(title="Select output folder")
        if path:
            output_var.set(path)

    def launch() -> None:
        def worker() -> None:
            log: list[str] = []
            try:
                status_var.set("Starting Docker and server...")
                if source_var.get():
                    os.environ["JOURNAL_ARCHIVE"] = source_var.get()
                if output_var.get():
                    os.environ["JOURNAL_OUTPUT_DIR"] = output_var.get()
                _configure_docker_paths(source_var.get(), output_var.get(), log)
                _start_docker_and_compose(state, log)
                if state.compose_started:
                    log.append("using Docker web server on port 8765")
                else:
                    _start_server(state, log)
                webbrowser.open(APP_URL)
                status_var.set("Server running at http://127.0.0.1:8765")
            except Exception as exc:
                state.last_error = str(exc)
                status_var.set(f"Error: {exc}")
                messagebox.showerror("Journal Factory Launcher", str(exc))
            finally:
                details.delete("1.0", tk.END)
                details.insert(tk.END, "\n".join(log) or "No additional actions were required.")

        threading.Thread(target=worker, daemon=True).start()

    frm = tk.Frame(root, padx=14, pady=14)
    frm.pack(fill="both", expand=True)

    tk.Label(frm, text="Journal Factory", font=("Segoe UI", 16, "bold")).pack(anchor="w")
    tk.Label(frm, textvariable=status_var, fg="#1f2937").pack(anchor="w", pady=(2, 10))

    kind_row = tk.Frame(frm)
    kind_row.pack(fill="x", pady=4)
    tk.Label(kind_row, text="Input type", width=14, anchor="w").pack(side="left")
    tk.Radiobutton(kind_row, text="ZIP archive", value="file", variable=source_kind).pack(side="left")
    tk.Radiobutton(kind_row, text="Folder", value="dir", variable=source_kind).pack(side="left", padx=(8, 0))

    row1 = tk.Frame(frm)
    row1.pack(fill="x", pady=4)
    tk.Label(row1, text="Input source", width=14, anchor="w").pack(side="left")
    tk.Entry(row1, textvariable=source_var).pack(side="left", fill="x", expand=True, padx=(0, 8))
    tk.Button(row1, text="Browse", command=pick_source).pack(side="left")

    row2 = tk.Frame(frm)
    row2.pack(fill="x", pady=4)
    tk.Label(row2, text="Output folder", width=14, anchor="w").pack(side="left")
    tk.Entry(row2, textvariable=output_var).pack(side="left", fill="x", expand=True, padx=(0, 8))
    tk.Button(row2, text="Browse", command=pick_output).pack(side="left")

    button_row = tk.Frame(frm)
    button_row.pack(fill="x", pady=(10, 8))
    tk.Button(button_row, text="Start", command=launch, height=2, width=14).pack(side="left")
    tk.Button(button_row, text="Open Browser", command=lambda: webbrowser.open(APP_URL)).pack(side="left", padx=8)

    details = tk.Text(frm, height=8, wrap="word")
    details.pack(fill="both", expand=True)
    return root


def main() -> int:
    build_ui().mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
