from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable

from astra_journal.hermes_client import HermesClient, HermesEndpoint, HermesError


@dataclass(frozen=True)
class RoutingResult:
    worker: str
    endpoint: HermesEndpoint
    parsed: dict[str, Any]
    raw: dict[str, Any]
    latency_s: float
    attempts: list[dict[str, Any]]


class HermesRouter:
    def __init__(
        self,
        endpoints: list[tuple[str, HermesEndpoint]],
        *,
        timeout: float = 120.0,
        api_key: str | None = None,
        max_retries: int = 2,
        retry_delay_s: float = 0.2,
        client_factory: Callable[..., HermesClient] = HermesClient,
    ) -> None:
        if not endpoints:
            raise ValueError("At least one Hermes endpoint is required")
        self.endpoints = endpoints
        self.timeout = timeout
        self.api_key = api_key
        self.max_retries = max(0, int(max_retries))
        self.retry_delay_s = max(0.0, float(retry_delay_s))
        self.client_factory = client_factory

    def chat_json(
        self,
        *,
        task: str,
        instruction: str,
        max_tokens: int = 512,
    ) -> RoutingResult:
        attempts: list[dict[str, Any]] = []

        for worker, endpoint in self.endpoints:
            for retry in range(self.max_retries + 1):
                record = {
                    "worker": worker,
                    "base_url": endpoint.base_url,
                    "model": endpoint.model,
                    "retry": retry,
                }
                try:
                    client = self.client_factory(
                        endpoint,
                        timeout=self.timeout,
                        api_key=self.api_key,
                    )
                    parsed, raw, latency = client.chat_json(
                        task=task,
                        instruction=instruction,
                        max_tokens=max_tokens,
                    )
                    record["status"] = "ok"
                    record["latency_s"] = latency
                    attempts.append(record)
                    return RoutingResult(
                        worker=worker,
                        endpoint=endpoint,
                        parsed=parsed,
                        raw=raw,
                        latency_s=latency,
                        attempts=attempts,
                    )
                except HermesError as exc:
                    record["status"] = "error"
                    record["error"] = str(exc)
                    attempts.append(record)
                    if retry < self.max_retries and self.retry_delay_s:
                        time.sleep(self.retry_delay_s)

        raise HermesError(
            "All Hermes routes failed: "
            + "; ".join(
                f"{a['worker']}#{a['retry']}={a.get('error','error')}"
                for a in attempts
            )
        )
