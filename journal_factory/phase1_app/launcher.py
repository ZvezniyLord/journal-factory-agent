from __future__ import annotations

import argparse
import os
import sys
import threading
import webbrowser
from pathlib import Path

from .composition import build_application
from .server import Phase1HttpServer


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Launch Journal Factory Phase 1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    arguments = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    local_data = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "JournalFactory"
    application = build_application(
        desktop_path=Path.home() / "Desktop",
        state_directory=local_data / "state",
    )
    try:
        server = Phase1HttpServer(application, index_path=root / "index.html", port=arguments.port)
    except OSError:
        server = Phase1HttpServer(application, index_path=root / "index.html", port=0)
    server.start()
    url = server.base_url + "/"
    print(f"Journal Factory: {url}", flush=True)
    if not arguments.no_browser:
        webbrowser.open(url)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
