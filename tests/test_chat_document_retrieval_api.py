from app.core.settings import settings
from app.rag.embeddings import EmbeddingModel
from app.rag.store import DocumentChunk, DocumentStore
from tests.conftest import FakeProvider


class _FakeEmbeddingModel(EmbeddingModel):
    def __init__(self, vectors):
        self._vectors = vectors

    def embed(self, texts):
        return [self._vectors.get(t, [0.0, 0.0, 0.0]) for t in texts]

    def embed_one(self, text):
        return self._vectors.get(text, [1.0, 0.0, 0.0])


def test_document_id_injects_retrieved_context_into_the_forwarded_prompt(
    client, clean_registry, monkeypatch, tmp_path
):
    captured = {}

    class _CapturingProvider(FakeProvider):
        async def complete(self, model_id, messages, *args, **kwargs):
            captured["messages"] = messages
            return await super().complete(model_id, messages, *args, **kwargs)

    from tests.conftest import FAKE_MODELS

    clean_registry.register(_CapturingProvider([FAKE_MODELS[0]]))

    store = DocumentStore(path=tmp_path / "docs.json")
    document_id = store.ingest(
        "manual.txt",
        [
            DocumentChunk(text="the widget assembly procedure", embedding=[1.0, 0.0, 0.0]),
            DocumentChunk(text="unrelated section about invoices", embedding=[0.0, 1.0, 0.0]),
        ],
    )

    import app.rag.retrieval as retrieval_module

    monkeypatch.setattr(
        retrieval_module,
        "default_embedding_model",
        _FakeEmbeddingModel({"how do I assemble the widget?": [1.0, 0.0, 0.0]}),
    )
    monkeypatch.setattr(retrieval_module, "default_document_store", store)
    monkeypatch.setattr(settings, "RAG_RETRIEVAL_TOP_K", 1)

    response = client.post(
        "/v1/chat/completions",
        json={
            "messages": [
                {"role": "user", "content": "how do I assemble the widget?"}
            ],
            "lair_document_id": document_id,
        },
    )

    assert response.status_code == 200
    forwarded_content = " ".join(m["content"] for m in captured["messages"])
    assert "widget assembly procedure" in forwarded_content
    assert "unrelated section about invoices" not in forwarded_content


def test_no_document_id_never_injects_anything(client, registered_fake_provider):
    response = client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert response.status_code == 200


def test_unknown_document_id_degrades_gracefully(client, registered_fake_provider):
    response = client.post(
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "hello"}],
            "lair_document_id": "no-such-document",
        },
    )

    assert response.status_code == 200
