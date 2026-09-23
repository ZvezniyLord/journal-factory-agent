from astra_journal.hermes_client import HermesEndpoint, build_chat_payload, extract_json_object


def test_extract_json_object_from_plain_json() -> None:
    value = extract_json_object('{"status":"ok","arithmetic":42}')
    assert value["status"] == "ok"
    assert value["arithmetic"] == 42


def test_extract_json_object_from_wrapped_text() -> None:
    value = extract_json_object(
        'analysis omitted {"status":"ok","role":"hermes_subagent","arithmetic":42} trailing'
    )
    assert value["role"] == "hermes_subagent"


def test_build_chat_payload_applies_safe_request_overrides() -> None:
    endpoint = HermesEndpoint(
        "http://localhost:11434/v1",
        "model",
        1000,
        "main",
        request_overrides={
            "chat_template_kwargs": {"enable_thinking": False},
            "response_format": {"type": "json_object"},
            "model": "must-not-override",
            "max_tokens": 99999,
        },
    )
    payload = build_chat_payload(
        endpoint,
        task="x",
        instruction="y",
        max_tokens=123,
    )
    assert payload["model"] == "model"
    assert payload["max_tokens"] == 123
    assert payload["chat_template_kwargs"]["enable_thinking"] is False
    assert payload["response_format"] == {"type": "json_object"}
