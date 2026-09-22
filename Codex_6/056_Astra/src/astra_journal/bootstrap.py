from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .hermes_client import HermesClient, HermesEndpoint, HermesError
from .path_guard import PathGuard


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def project_root_from_file() -> Path:
    return Path(__file__).resolve().parents[2]


def load_runtime(root: Path) -> dict[str, Any]:
    runtime_path = root / "config" / "hermes_runtime.json"
    return json.loads(runtime_path.read_text(encoding="utf-8-sig"))


def _endpoint_from(runtime: dict[str, Any], key: str) -> HermesEndpoint:
    cfg = runtime[key]
    return HermesEndpoint(
        base_url=cfg["openai_base_url"],
        model=cfg["model"],
        context=int(cfg["context"]),
        role=cfg.get("role", key),
    )


def _model_present(models_payload: dict[str, Any], wanted: str) -> bool:
    data = models_payload.get("data")
    if not isinstance(data, list):
        return False
    return any(
        isinstance(item, dict) and item.get("id") == wanted
        for item in data
    )


def run_handshake(root: Path) -> tuple[dict[str, Any], int]:
    guard = PathGuard(root)
    out_dir = guard.inside("runs/bootstrap")
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = guard.inside("runs/bootstrap/hermes_handshake.json")

    runtime = load_runtime(root)
    timeout = float(runtime.get("limits", {}).get("timeout_seconds", 120))
    api_key = os.getenv("HERMES_API_KEY") or None
    attempts: list[dict[str, Any]] = []

    for key in ("main", "fallback"):
        if key not in runtime:
            continue

        endpoint = _endpoint_from(runtime, key)
        attempt: dict[str, Any] = {
            "worker": key,
            "base_url": endpoint.base_url,
            "model": endpoint.model,
            "context": endpoint.context,
            "started_at": _utc_now(),
        }

        try:
            client = HermesClient(endpoint, timeout=timeout, api_key=api_key)
            models, models_latency = client.list_models()
            attempt["models_latency_s"] = round(models_latency, 4)
            attempt["model_visible"] = _model_present(models, endpoint.model)
            attempt["models"] = [
                item.get("id")
                for item in models.get("data", [])
                if isinstance(item, dict) and item.get("id")
            ]

            parsed, raw, chat_latency = client.chat_json(
                task="bootstrap_healthcheck",
                instruction=(
                    "Return exactly a JSON object with status='ok', "
                    "role='hermes_subagent', arithmetic=42."
                ),
                max_tokens=int(
                    runtime.get("bootstrap", {}).get("max_output_tokens", 256)
                ),
            )
            attempt["chat_latency_s"] = round(chat_latency, 4)
            attempt["parsed"] = parsed
            attempt["raw_response_shape"] = {
                "id": raw.get("id"),
                "model": raw.get("model"),
                "created": raw.get("created"),
            }

            valid = (
                parsed.get("status") == "ok"
                and parsed.get("role") == "hermes_subagent"
                and parsed.get("arithmetic") == 42
            )
            attempt["valid"] = valid
            attempts.append(attempt)

            if valid:
                result = {
                    "status": "PASS",
                    "provenance": "local_runtime_handshake",
                    "generated_by": "astra_journal.bootstrap",
                    "selected_worker": key,
                    "selected_base_url": endpoint.base_url,
                    "selected_model": endpoint.model,
                    "selected_context": endpoint.context,
                    "created_at": _utc_now(),
                    "host": platform.node(),
                    "python": sys.version,
                    "attempts": attempts,
                }
                output_path.write_text(
                    json.dumps(result, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                return result, 0

        except HermesError as exc:
            attempt["valid"] = False
            attempt["error"] = str(exc)
            attempts.append(attempt)

    result = {
        "status": "BLOCKED_HERMES_BOOTSTRAP",
        "provenance": "local_runtime_handshake",
        "generated_by": "astra_journal.bootstrap",
        "created_at": _utc_now(),
        "host": platform.node(),
        "python": sys.version,
        "attempts": attempts,
    }
    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result, 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Astra Hermes bootstrap")
    parser.add_argument(
        "--root",
        type=Path,
        default=project_root_from_file(),
        help="Codex_6/056_Astra workspace root",
    )
    args = parser.parse_args()
    result, code = run_handshake(args.root.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
