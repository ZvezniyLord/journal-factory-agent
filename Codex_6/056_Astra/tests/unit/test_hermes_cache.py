from astra_journal.hermes.cache import DiskHermesCache, make_cache_key


def test_cache_key_is_stable() -> None:
    kwargs = {
        "normalized_input": {"b": 2, "a": 1},
        "task": "classify_file",
        "prompt_version": "1",
        "schema_version": "1",
        "model": "model",
        "config_fingerprint": "cfg",
    }
    assert make_cache_key(**kwargs) == make_cache_key(**kwargs)


def test_disk_cache_round_trip(tmp_path) -> None:
    cache = DiskHermesCache(tmp_path)
    key = make_cache_key(
        normalized_input="abc",
        task="classify_file",
        prompt_version="1",
        schema_version="1",
        model="model",
        config_fingerprint="cfg",
    )
    cache.put(key, {"status": "ok"})
    assert cache.get(key) == {"status": "ok"}
