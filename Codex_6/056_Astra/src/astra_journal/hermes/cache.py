from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def make_cache_key(
    *,
    normalized_input: Any,
    task: str,
    prompt_version: str,
    schema_version: str,
    model: str,
    config_fingerprint: str,
) -> str:
    payload = {
        "input": normalized_input,
        "task": task,
        "prompt_version": prompt_version,
        "schema_version": schema_version,
        "model": model,
        "config_fingerprint": config_fingerprint,
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class DiskHermesCache:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, key: str) -> Path:
        if len(key) != 64 or any(ch not in "0123456789abcdef" for ch in key):
            raise ValueError("Cache key must be lowercase SHA-256 hex")
        return self.root / f"{key}.json"

    def get(self, key: str) -> dict[str, Any] | None:
        path = self.path_for(key)
        if not path.exists():
            return None
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Cached Hermes value must be an object")
        return value

    def put(self, key: str, value: dict[str, Any]) -> Path:
        path = self.path_for(key)
        temp = path.with_suffix(".tmp")
        temp.write_text(
            json.dumps(value, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(path)
        return path
