from app.rag.embeddings import EmbeddingModel
from app.rag.retrieval import retrieve_relevant_chunks
from app.rag.store import DocumentChunk, DocumentStore


class _FakeEmbeddingModel(EmbeddingModel):
    """
    Deterministic stand-in: embeds text into a one-hot-ish vector from
    an explicit text->vector map, so similarity ranking is fully
    controlled by the test rather than depending on real semantics.
    """

    def __init__(self, vectors: dict[str, list[float]]):
        self._vectors = vectors

    def embed(self, texts):
        return [self._vectors.get(t, [0.0, 0.0, 0.0]) for t in texts]

    def embed_one(self, text):
        return self._vectors.get(text, [0.0, 0.0, 0.0])


def test_retrieves_most_similar_chunk_first(tmp_path):
    store = DocumentStore(path=tmp_path / "docs.json")
    chunks = [
        DocumentChunk(text="about cats", embedding=[1.0, 0.0, 0.0]),
        DocumentChunk(text="about dogs", embedding=[0.0, 1.0, 0.0]),
    ]
    document_id = store.ingest("pets.txt", chunks)

    model = _FakeEmbeddingModel({"tell me about cats": [1.0, 0.0, 0.0]})

    results = retrieve_relevant_chunks(
        document_id, "tell me about cats", top_k=1, store=store, embedding_model=model
    )

    assert results == ["about cats"]


def test_unknown_document_returns_no_chunks(tmp_path):
    store = DocumentStore(path=tmp_path / "docs.json")
    model = _FakeEmbeddingModel({})

    results = retrieve_relevant_chunks(
        "no-such-doc", "anything", store=store, embedding_model=model
    )

    assert results == []


def test_top_k_limits_number_of_candidates_considered(tmp_path):
    store = DocumentStore(path=tmp_path / "docs.json")
    # Varying *direction*, not just magnitude -- cosine similarity is
    # scale-invariant, so colinear vectors (e.g. [1,0,0] vs [9,0,0])
    # would all tie at similarity 1.0 and not actually test ranking.
    chunks = [
        DocumentChunk(text=f"chunk {i}", embedding=[10.0 - i, float(i), 0.0])
        for i in range(10)
    ]
    document_id = store.ingest("doc.txt", chunks)
    model = _FakeEmbeddingModel({"query": [0.0, 9.0, 0.0]})

    results = retrieve_relevant_chunks(
        document_id, "query", top_k=3, token_budget=100_000, store=store, embedding_model=model
    )

    assert len(results) <= 3
    assert "chunk 9" in results


def test_token_budget_trims_lower_ranked_chunks(tmp_path):
    store = DocumentStore(path=tmp_path / "docs.json")
    big_chunk_text = " ".join(["word"] * 2000)  # ~500 tokens
    chunks = [
        DocumentChunk(text=big_chunk_text, embedding=[1.0, 0.0, 0.0]),
        DocumentChunk(text=big_chunk_text, embedding=[0.9, 0.0, 0.0]),
        DocumentChunk(text=big_chunk_text, embedding=[0.8, 0.0, 0.0]),
    ]
    document_id = store.ingest("doc.txt", chunks)
    model = _FakeEmbeddingModel({"query": [1.0, 0.0, 0.0]})

    # Budget only fits one ~500-token chunk.
    results = retrieve_relevant_chunks(
        document_id, "query", top_k=3, token_budget=600, store=store, embedding_model=model
    )

    assert len(results) == 1


def test_always_returns_at_least_one_chunk_even_over_budget(tmp_path):
    store = DocumentStore(path=tmp_path / "docs.json")
    huge_chunk = " ".join(["word"] * 5000)
    chunks = [DocumentChunk(text=huge_chunk, embedding=[1.0, 0.0, 0.0])]
    document_id = store.ingest("doc.txt", chunks)
    model = _FakeEmbeddingModel({"query": [1.0, 0.0, 0.0]})

    results = retrieve_relevant_chunks(
        document_id, "query", top_k=1, token_budget=10, store=store, embedding_model=model
    )

    assert len(results) == 1
