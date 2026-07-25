from app.core.settings import settings
from app.rag.embeddings import EmbeddingModel
from tests.conftest import FAKE_MODELS, FakeProvider


class _FakeEmbeddingModel(EmbeddingModel):
    def __init__(self, vectors: dict[str, list[float]]):
        self._vectors = vectors

    def embed(self, texts):
        return [self._vectors.get(t, [0.0, 0.0, 0.0]) for t in texts]

    def embed_one(self, text):
        return self._vectors.get(text, [0.0, 0.0, 0.0])


def _patch_embeddings(monkeypatch, vectors: dict[str, list[float]]):
    import app.api.chat as chat_api_module
    import app.memory.retrieval as memory_retrieval_module

    model = _FakeEmbeddingModel(vectors)
    monkeypatch.setattr(chat_api_module, "default_embedding_model", model)
    monkeypatch.setattr(memory_retrieval_module, "default_embedding_model", model)


def test_memory_disabled_by_default_never_stores_anything(
    client, clean_registry, monkeypatch, tmp_path
):
    clean_registry.register(FakeProvider([FAKE_MODELS[0]]))
    _patch_embeddings(monkeypatch, {})

    response = client.post(
        "/v1/chat/completions",
        json={
            "messages": [
                {"role": "user", "content": "Please remember that I use tabs, not spaces."}
            ],
            "lair_project_scope": "project-a",
        },
    )

    assert response.status_code == 200
    assert response.json()["lair_meta"]["memory_injected_count"] == 0

    import app.api.chat as chat_api_module

    assert chat_api_module.default_memory_store.list_for_scope("project-a") == []


def test_memory_without_scope_never_stores_anything(
    client, clean_registry, monkeypatch, tmp_path
):
    clean_registry.register(FakeProvider([FAKE_MODELS[0]]))
    _patch_embeddings(monkeypatch, {})
    monkeypatch.setattr(settings, "ENABLE_PROJECT_MEMORY", True)

    response = client.post(
        "/v1/chat/completions",
        json={
            "messages": [
                {"role": "user", "content": "Please remember that I use tabs, not spaces."}
            ],
        },
    )

    assert response.status_code == 200

    import app.api.chat as chat_api_module

    assert chat_api_module.default_memory_store.all_for_scope("") == []


def test_durable_statement_is_remembered_and_later_retrieved(
    client, clean_registry, monkeypatch, tmp_path
):
    clean_registry.register(FakeProvider([FAKE_MODELS[0]]))
    monkeypatch.setattr(settings, "ENABLE_PROJECT_MEMORY", True)
    _patch_embeddings(
        monkeypatch,
        {
            "Please remember that I use tabs, not spaces.": [1.0, 0.0, 0.0],
            "What indentation style do I use?": [1.0, 0.0, 0.0],
        },
    )

    first = client.post(
        "/v1/chat/completions",
        json={
            "messages": [
                {"role": "user", "content": "Please remember that I use tabs, not spaces."}
            ],
            "lair_project_scope": "project-a",
        },
    )
    assert first.status_code == 200

    import app.api.chat as chat_api_module

    assert len(chat_api_module.default_memory_store.list_for_scope("project-a")) == 1

    captured = {}

    class _CapturingProvider(FakeProvider):
        async def complete(self, model_id, messages, *args, **kwargs):
            captured["messages"] = messages
            return await super().complete(model_id, messages, *args, **kwargs)

    clean_registry._providers.clear()
    clean_registry.register(_CapturingProvider([FAKE_MODELS[0]]))

    second = client.post(
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "What indentation style do I use?"}],
            "lair_project_scope": "project-a",
        },
    )

    assert second.status_code == 200
    assert second.json()["lair_meta"]["memory_injected_count"] == 1
    forwarded_content = " ".join(m["content"] for m in captured["messages"])
    assert "tabs, not spaces" in forwarded_content


def test_ordinary_message_is_not_remembered(
    client, clean_registry, monkeypatch, tmp_path
):
    clean_registry.register(FakeProvider([FAKE_MODELS[0]]))
    monkeypatch.setattr(settings, "ENABLE_PROJECT_MEMORY", True)
    _patch_embeddings(monkeypatch, {})

    response = client.post(
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "what does this function do?"}],
            "lair_project_scope": "project-a",
        },
    )

    assert response.status_code == 200

    import app.api.chat as chat_api_module

    assert chat_api_module.default_memory_store.list_for_scope("project-a") == []
