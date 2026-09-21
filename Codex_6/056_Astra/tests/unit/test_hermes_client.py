from astra_journal.hermes_client import extract_json_object


def test_extract_json_object_from_plain_json() -> None:
    value = extract_json_object('{"status":"ok","arithmetic":42}')
    assert value["status"] == "ok"
    assert value["arithmetic"] == 42


def test_extract_json_object_from_wrapped_text() -> None:
    value = extract_json_object(
        'analysis omitted {"status":"ok","role":"hermes_subagent","arithmetic":42} trailing'
    )
    assert value["role"] == "hermes_subagent"
