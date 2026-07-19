from __future__ import annotations

import argparse
import json
import os
import threading
from pathlib import Path

from journal_factory.phase1_app.composition import build_application
from journal_factory.phase1_app.server import Phase1HttpServer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--info", type=Path, required=True)
    arguments = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    application = build_application(
        desktop_path=Path.home() / "Desktop",
        state_directory=arguments.state,
    )
    server = Phase1HttpServer(
        application,
        index_path=root / "index.html",
        port=arguments.port,
    )
    server.start()
    arguments.info.parent.mkdir(parents=True, exist_ok=True)
    arguments.info.write_text(
        json.dumps({"pid": os.getpid(), "url": server.base_url + "/"}) + "\n",
        encoding="utf-8",
    )
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()


if __name__ == "__main__":
    main()
