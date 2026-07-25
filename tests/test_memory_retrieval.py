from app.memory.retrieval import retrieve_relevant_memories
from app.memory.store import MemoryStore
from app.rag.embeddings import EmbeddingModel


class _FakeEmbeddingModel(EmbeddingModel):
    def __init__(self, vectors: dict[str, list[float]]):
        self._vectors = vectors

    def embed(self, texts):
        return [self._vectors.get(t, [0.0, 0.0, 0.0]) for t in texts]

    def embed_one(self, text):
        return self._vectors.get(text, [0.0, 0.0, 0.0])


def test_retrieves_most_similar_memory_first(tmp_path):
    store = MemoryStore(path=tmp_path / "memory.json")
    store.remember("project-a", "prefers dark mode", [1.0, 0.0, 0.0])
    store.remember("project-a", "uses tabs not spaces", [0.0, 1.0, 0.0])

    model = _FakeEmbeddingModel({"what theme do I like?": [1.0, 0.0, 0.0]})

    results = retrieve_relevant_memories(
        "project-a", "what theme do I like?", top_k=1, store=store, embedding_model=model
    )

    assert results == ["prefers dark mode"]


def test_unknown_scope_returns_no_memories(tmp_path):
    store = MemoryStore(path=tmp_path / "memory.json")
    model = _FakeEmbeddingModel({})

    results = retrieve_relevant_memories(
        "no-such-scope", "anything", store=store, embedding_model=model
    )

    assert results == []


def test_never_retrieves_memories_from_a_different_scope(tmp_path):
    store = MemoryStore(path=tmp_path / "memory.json")
    store.remember("project-a", "fact about a", [1.0, 0.0, 0.0])
    store.remember("project-b", "fact about b", [1.0, 0.0, 0.0])

    model = _FakeEmbeddingModel({"query": [1.0, 0.0, 0.0]})

    results = retrieve_relevant_memories(
        "project-a", "query", top_k=5, store=store, embedding_model=model
    )

    assert results == ["fact about a"]


def test_token_budget_trims_lower_ranked_memories(tmp_path):
    store = MemoryStore(path=tmp_path / "memory.json")
    big_text = " ".join(["word"] * 2000)  # ~500 tokens
    # Different *direction*, not just magnitude (cosine similarity is
    # scale-invariant), so these two memories don't dedup-merge into
    # one -- see test_memory_store.py's own scope-isolation tests for
    # the same reasoning.
    store.remember("project-a", big_text + " one", [1.0, 0.0, 0.0])
    store.remember("project-a", big_text + " two", [0.8, 0.6, 0.0])

    model = _FakeEmbeddingModel({"query": [1.0, 0.0, 0.0]})

    results = retrieve_relevant_memories(
        "project-a", "query", top_k=2, token_budget=600, store=store, embedding_model=model
    )

    assert len(results) == 1
