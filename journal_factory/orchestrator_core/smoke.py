from __future__ import annotations

import json
import threading
import urllib.request

from .server import OrchestratorApplication, make_server


def request_json(url: str, method: str = "GET", payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=3) as response:
        return json.loads(response.read())


def main() -> None:
    server = make_server("127.0.0.1", 0, OrchestratorApplication())
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base_url = f"http://{host}:{port}"
    shutdown_clean = False
    try:
        with urllib.request.urlopen(base_url + "/", timeout=3) as response:
            html = response.read()
        initial = request_json(base_url + "/api/orchestrator/state")
        final = request_json(
            base_url + "/api/orchestrator/start",
            "POST",
            {"run_id": "real-smoke-run"},
        )
        if initial["state"] != "idle" or final["state"] != "completed":
            raise RuntimeError("Smoke run did not reach expected states")
        if b'id="start-run"' not in html:
            raise RuntimeError("Root command menu is missing")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
        shutdown_clean = not thread.is_alive()

    report = {
        "url": base_url + "/",
        "html_bytes": len(html),
        "initial_state": initial["state"],
        "final_state": final["state"],
        "completed_cores": final["completed_cores"],
        "action_count": final["action_count"],
        "shutdown_clean": shutdown_clean,
    }
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
