import time

from app.cache.response_cache import CachedResponse, ResponseCache, cache_key_for


def _entry(model_id: str = "m", cached_at: float | None = None) -> CachedResponse:
    return CachedResponse(
        text="hello",
        finish_reason="stop",
        completion_tokens=3,
        prompt_tokens=5,
        model_id=model_id,
        cached_at=cached_at if cached_at is not None else time.time(),
    )


def test_cache_key_is_stable_for_identical_conversations():
    messages = [{"role": "user", "content": "hi"}]

    assert cache_key_for(messages) == cache_key_for(messages)


def test_cache_key_differs_for_different_conversation_history():
    key_a = cache_key_for([{"role": "user", "content": "hi"}])
    key_b = cache_key_for(
        [
            {"role": "system", "content": "be nice"},
            {"role": "user", "content": "hi"},
        ]
    )

    assert key_a != key_b


def test_get_returns_none_for_missing_key(tmp_path):
    cache = ResponseCache(max_entries=10, ttl_seconds=3600, path=tmp_path / "c.json")

    assert cache.get("missing") is None


def test_put_then_get_round_trips(tmp_path):
    cache = ResponseCache(max_entries=10, ttl_seconds=3600, path=tmp_path / "c.json")

    cache.put("key", _entry())
    result = cache.get("key")

    assert result is not None
    assert result.text == "hello"


def test_expired_entry_is_not_returned(tmp_path):
    cache = ResponseCache(max_entries=10, ttl_seconds=1, path=tmp_path / "c.json")

    cache.put("key", _entry(cached_at=time.time() - 10))

    assert cache.get("key") is None


def test_lru_eviction_drops_the_oldest_entry(tmp_path):
    cache = ResponseCache(max_entries=2, ttl_seconds=3600, path=tmp_path / "c.json")

    cache.put("a", _entry("a"))
    cache.put("b", _entry("b"))
    cache.put("c", _entry("c"))

    assert cache.get("a") is None
    assert cache.get("b") is not None
    assert cache.get("c") is not None


def test_get_refreshes_lru_order(tmp_path):
    cache = ResponseCache(max_entries=2, ttl_seconds=3600, path=tmp_path / "c.json")

    cache.put("a", _entry("a"))
    cache.put("b", _entry("b"))
    cache.get("a")  # "a" is now more recently used than "b"
    cache.put("c", _entry("c"))

    assert cache.get("b") is None
    assert cache.get("a") is not None
    assert cache.get("c") is not None


def test_persists_across_instances(tmp_path):
    path = tmp_path / "c.json"
    cache = ResponseCache(max_entries=10, ttl_seconds=3600, path=path)
    cache.put("key", _entry())

    reloaded = ResponseCache(max_entries=10, ttl_seconds=3600, path=path)

    assert reloaded.get("key") is not None


def test_corrupt_cache_file_is_skipped_gracefully(tmp_path):
    path = tmp_path / "c.json"
    path.write_text("not valid json", encoding="utf-8")

    cache = ResponseCache(max_entries=10, ttl_seconds=3600, path=path)

    assert cache.get("anything") is None


def test_get_and_put_overhead_is_small(tmp_path):
    # A local, honest proxy for I-07's "cache hit path adds <50ms /
    # miss path adds <20ms" budget: what the cache module itself
    # contributes, measured on this machine -- not a cross-platform
    # guarantee of the full HTTP request path.
    cache = ResponseCache(max_entries=500, ttl_seconds=3600, path=tmp_path / "c.json")
    cache.put("key", _entry())

    start = time.perf_counter()
    cache.get("key")
    get_elapsed_ms = (time.perf_counter() - start) * 1000

    start = time.perf_counter()
    cache.put("key2", _entry("key2"))
    put_elapsed_ms = (time.perf_counter() - start) * 1000

    assert get_elapsed_ms < 50
    assert put_elapsed_ms < 50
