from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class HermesError(RuntimeError):
    pass


def _request_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout: float = 120.0,
    api_key: str | None = None,
) -> tuple[dict[str, Any], float]:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise HermesError(f"{method} {url} failed: {exc}") from exc

    elapsed = time.perf_counter() - started
    try:
        return json.loads(raw), elapsed
    except json.JSONDecodeError as exc:
        raise HermesError(f"{method} {url} returned invalid JSON: {raw[:500]}") from exc


def extract_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()

    try:
        value = json.loads(cleaned)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    if start < 0:
        raise HermesError(f"Hermes response has no JSON object: {cleaned[:500]}")

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(cleaned)):
        char = cleaned[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                fragment = cleaned[start : index + 1]
                try:
                    value = json.loads(fragment)
                except json.JSONDecodeError as exc:
                    raise HermesError(
                        f"Could not parse JSON object from Hermes response: {fragment[:500]}"
                    ) from exc
                if not isinstance(value, dict):
                    raise HermesError("Hermes JSON result is not an object")
                return value

    raise HermesError(f"Unclosed JSON object in Hermes response: {cleaned[:500]}")


@dataclass(frozen=True)
class HermesEndpoint:
    base_url: str
    model: str
    context: int
    role: str
    request_overrides: dict[str, Any] | None = None

    @property
    def normalized_base_url(self) -> str:
        return self.base_url.rstrip("/")


def build_chat_payload(
    endpoint: HermesEndpoint,
    *,
    task: str,
    instruction: str,
    max_tokens: int,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": endpoint.model,
        "temperature": 0,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are Hermes, a local semantic subagent. "
                    "Return JSON only."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {"task": task, "instruction": instruction},
                    ensure_ascii=False,
                ),
            },
        ],
    }
    if endpoint.request_overrides:
        # Repository configuration may set OpenAI-compatible server options,
        # e.g. chat_template_kwargs.enable_thinking=false for Qwen chat
        # templates. Core fields remain controlled by Astra.
        for key, value in endpoint.request_overrides.items():
            if key not in {"model", "messages", "max_tokens"}:
                payload[key] = value
    return payload


class HermesClient:
    def __init__(
        self,
        endpoint: HermesEndpoint,
        *,
        timeout: float = 120.0,
        api_key: str | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.timeout = timeout
        self.api_key = api_key

    def list_models(self) -> tuple[dict[str, Any], float]:
        return _request_json(
            f"{self.endpoint.normalized_base_url}/models",
            timeout=self.timeout,
            api_key=self.api_key,
        )

    def chat_json(
        self,
        *,
        task: str,
        instruction: str,
        max_tokens: int = 512,
    ) -> tuple[dict[str, Any], dict[str, Any], float]:
        payload = build_chat_payload(
            self.endpoint,
            task=task,
            instruction=instruction,
            max_tokens=max_tokens,
        )
        raw, elapsed = _request_json(
            f"{self.endpoint.normalized_base_url}/chat/completions",
            method="POST",
            payload=payload,
            timeout=self.timeout,
            api_key=self.api_key,
        )
        try:
            message = raw["choices"][0]["message"]
            content = message.get("content")
        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            raise HermesError(
                f"Unexpected OpenAI-compatible response shape: {json.dumps(raw)[:1000]}"
            ) from exc
        if content is None or not str(content).strip():
            finish_reason = None
            reasoning_present = False
            try:
                finish_reason = raw["choices"][0].get("finish_reason")
                reasoning_present = bool(
                    message.get("reasoning_content")
                    or message.get("reasoning")
                    or message.get("analysis")
                )
            except Exception:
                pass
            suffix = (
                f"; finish_reason={finish_reason!r}"
                f"; hidden_reasoning_present={reasoning_present}"
            )
            raise HermesError(
                "Hermes returned empty visible content" + suffix
            )

        parsed = extract_json_object(str(content))
        return parsed, raw, elapsed
