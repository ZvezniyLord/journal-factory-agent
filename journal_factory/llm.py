from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _float_env(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class LLMClient:
    def __init__(self, context: str):
        self.context = context

    def _base_url(self) -> str:
        if self.context == "same_container":
            return os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        if self.context == "other_docker_network":
            return os.environ.get(
                "OLLAMA_BASE_URL",
                "http://journal-factory-ollama-qwen35:11434",
            ).rstrip("/")
        return os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11435").rstrip("/")

    def classify(self, prompt: str) -> dict:
        endpoint = f"{self._base_url()}/api/chat"
        model = os.environ.get("OLLAMA_MODEL", "qwen3.5:latest")
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "think": _bool_env("OLLAMA_THINK", False),
            "options": {
                "temperature": 0,
                "num_predict": _int_env("OLLAMA_NUM_PREDICT", 256),
            },
        }
        timeout_s = _float_env("OLLAMA_TIMEOUT_SECONDS", 120.0)

        request = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout_s) as response:
                body = json.loads(response.read().decode("utf-8"))
            return {"ok": True, "model": model, "endpoint": endpoint, "response": body}
        except HTTPError as exc:
            return {
                "ok": False,
                "offline": False,
                "endpoint": endpoint,
                "status": exc.code,
                "error": str(exc),
            }
        except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            return {"ok": False, "offline": True, "endpoint": endpoint, "error": str(exc)}
