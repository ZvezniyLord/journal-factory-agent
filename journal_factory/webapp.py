from __future__ import annotations

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json
import os
import threading
import time
from urllib.error import URLError
from urllib.request import urlopen

from .audit import audit_article, release_gate, write_reports
from .config import default_config, ensure_dirs
from .docx_builder import build_draft
from .ingest import extract_docx_text_from_zip, inventory_archive, inventory_as_dict, is_non_article_text
from .preflight import run_preflight, write_preflight
from .template import style_snapshot, write_style_snapshot


BUILD_LOCK = threading.Lock()
BUILD_STATE: dict = {
    "running": False,
    "status": "IDLE",
    "started_at": None,
    "finished_at": None,
    "log": [],
    "error": "",
}


def _set_build_state(**updates: object) -> None:
    with BUILD_LOCK:
        BUILD_STATE.update(updates)


def _append_log(message: str) -> None:
    stamp = time.strftime("%H:%M:%S")
    with BUILD_LOCK:
        log = BUILD_STATE.setdefault("log", [])
        if isinstance(log, list):
            log.append(f"[{stamp}] {message}")
            del log[:-200]


def _snapshot_build_state() -> dict:
    with BUILD_LOCK:
        return {
            **BUILD_STATE,
            "log": list(BUILD_STATE.get("log", [])),
        }


def _run_build() -> None:
    _set_build_state(running=True, status="RUNNING", started_at=time.time(), finished_at=None, log=[], error="")
    try:
        config = default_config()
        ensure_dirs(config)
        _append_log(f"source: {config.archive}")
        _append_log(f"output: {config.build_dir}")
        _append_log("preflight started")
        preflight = run_preflight(config)
        write_preflight(config, preflight)
        _append_log(f"preflight status: {preflight['status']}")

        _append_log("inventory started")
        entries = inventory_archive(config.archive)
        candidates = [entry for entry in entries if entry.article_candidate]
        _append_log(f"inventory complete: {len(entries)} files, {len(candidates)} article candidates")

        article_texts = []
        audits = []
        for index, entry in enumerate(candidates, start=1):
            text = extract_docx_text_from_zip(config.archive, entry.path)
            if text and is_non_article_text(text):
                _append_log(f"skipped non-article form: {entry.path}")
                continue
            audits.append(audit_article(entry, text))
            if text:
                article_texts.append((entry.path, text))
            if index == 1 or index % 5 == 0 or index == len(candidates):
                _append_log(f"audited {index}/{len(candidates)} article candidates")

        _append_log("template snapshot started")
        snapshot = style_snapshot(config.template)
        write_style_snapshot(snapshot, config.reports_dir / "template_style_snapshot.json")

        _append_log("draft build started")
        draft = build_draft(config.etalon, config.build_dir / "journal_mvp_draft.docx", article_texts)
        gate = release_gate(preflight, audits)
        write_reports(config.reports_dir, inventory_as_dict(entries), audits, gate)
        _append_log(f"draft written: {draft}")
        _append_log(f"release gate: {gate['status']}")
        _set_build_state(status=gate["status"], running=False, finished_at=time.time())
    except Exception as exc:
        _append_log(f"error: {exc}")
        _set_build_state(status="ERROR", running=False, finished_at=time.time(), error=str(exc))


def _start_build_if_idle() -> dict:
    with BUILD_LOCK:
        if BUILD_STATE.get("running"):
            return {
                **BUILD_STATE,
                "log": list(BUILD_STATE.get("log", [])),
            }
        BUILD_STATE.update({"running": True, "status": "STARTING", "log": []})
    threading.Thread(target=_run_build, daemon=True).start()
    return _snapshot_build_state()


def _llm_status() -> dict:
    base_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    model = os.environ.get("OLLAMA_MODEL", "qwen3.5:latest")
    endpoint = f"{base_url}/api/tags"
    try:
        with urlopen(endpoint, timeout=2.5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        models = [item.get("name") for item in payload.get("models", []) if item.get("name")]
        return {
            "ok": model in models,
            "endpoint": base_url,
            "configured_model": model,
            "available_models": models,
            "note": "This MVP build path is deterministic and does not call the LLM during article audit.",
        }
    except (OSError, URLError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "endpoint": base_url,
            "configured_model": model,
            "available_models": [],
            "error": str(exc),
            "note": "Ollama is not reachable from this server; no model calls are being made.",
        }


INDEX = """<!doctype html>
<html lang="uk">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Journal Factory</title>
  <style>
    body{font-family:Segoe UI,Arial,sans-serif;margin:0;background:#f6f7f9;color:#17202a}
    header{background:#fff;border-bottom:1px solid #d9dee7;padding:16px 24px;display:flex;gap:16px;align-items:center;justify-content:space-between}
    main{padding:24px;display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(300px,1fr))}
    section{background:#fff;border:1px solid #d9dee7;border-radius:8px;padding:16px}
    h1{font-size:22px;margin:0} h2{font-size:16px;margin:0 0 12px}
    button{background:#1f5eff;color:#fff;border:0;border-radius:6px;padding:10px 14px;font-weight:600;cursor:pointer}
    button:disabled{background:#8b96aa;cursor:not-allowed}
    pre{white-space:pre-wrap;font-size:12px;background:#f0f2f5;padding:12px;border-radius:6px;max-height:420px;overflow:auto}
    .blocked{color:#a12828;font-weight:700}.pass{color:#126b3a;font-weight:700}.running{color:#7a4b00;font-weight:700}
    .wide{grid-column:1/-1}
  </style>
</head>
<body>
<header><h1>Journal Factory Admin</h1><button id="run" onclick="runBuild()">Run build</button></header>
<main>
  <section><h2>Status</h2><div id="status">Loading...</div></section>
  <section><h2>Build Progress</h2><pre id="progress"></pre></section>
  <section><h2>LLM / Model</h2><pre id="llm"></pre></section>
  <section><h2>Config</h2><pre id="config"></pre></section>
  <section><h2>Preflight</h2><pre id="preflight"></pre></section>
  <section><h2>Release Gate</h2><pre id="gate"></pre></section>
  <section class="wide"><h2>Inventory</h2><pre id="inventory"></pre></section>
</main>
<script>
function statusClass(value){
  if(value==='PASS' || value==='READY') return 'pass';
  if(value==='RUNNING' || value==='STARTING') return 'running';
  return 'blocked';
}
async function load(){
  const statusResponse=await fetch('/api/status'); const status=await statusResponse.json();
  document.getElementById('progress').textContent=(status.log||[]).join('\\n') || status.status;
  document.getElementById('run').disabled=!!status.running;

  const llmResponse=await fetch('/api/llm'); const llm=await llmResponse.json();
  document.getElementById('llm').textContent=JSON.stringify(llm,null,2);

  const configResponse=await fetch('/api/config'); const config=await configResponse.json();
  document.getElementById('config').textContent=JSON.stringify(config,null,2);

  for (const [id,url] of Object.entries({preflight:'/api/preflight',gate:'/api/gate',inventory:'/api/inventory'})) {
    const r=await fetch(url); const j=await r.json();
    document.getElementById(id).textContent=JSON.stringify(j,null,2);
    if(id==='gate') {
      const label=status.running ? status.status : (j.status||'NO BUILD');
      document.getElementById('status').innerHTML='<span class="'+statusClass(label)+'">'+label+'</span>';
    }
  }
}
async function runBuild(){
  document.getElementById('run').disabled=true;
  await fetch('/api/run',{method:'POST'});
  await load();
}
load();
setInterval(load, 2500);
</script>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        config = default_config()
        mapping = {
            "/api/preflight": config.reports_dir / "preflight.json",
            "/api/gate": config.reports_dir / "final_quality_gate.json",
            "/api/inventory": config.reports_dir / "archive_inventory.json",
        }
        if self.path == "/":
            self._send("text/html; charset=utf-8", INDEX.encode("utf-8"))
            return
        if self.path == "/api/status":
            self._send_json(_snapshot_build_state())
            return
        if self.path == "/api/llm":
            self._send_json(_llm_status())
            return
        if self.path == "/api/config":
            self._send_json(
                {
                    "archive": str(config.archive),
                    "build_dir": str(config.build_dir),
                    "reports_dir": str(config.reports_dir),
                    "etalon": str(config.etalon),
                    "template": str(config.template),
                }
            )
            return
        if self.path in mapping:
            path = mapping[self.path]
            data = path.read_bytes() if path.exists() else b'{"status":"NO BUILD"}'
            self._send("application/json; charset=utf-8", data)
            return
        self.send_error(404)

    def do_POST(self) -> None:
        if self.path == "/api/run":
            self._send_json(_start_build_if_idle())
            return
        self.send_error(404)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _send(self, content_type: str, body: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: dict) -> None:
        self._send("application/json; charset=utf-8", json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))


def serve(host: str, port: int) -> None:
    ThreadingHTTPServer((host, port), Handler).serve_forever()
