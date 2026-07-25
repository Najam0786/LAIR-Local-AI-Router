import math

from app.rag.chunking import estimate_chunk_tokens
from app.rag.embeddings import EmbeddingModel, default_embedding_model
from app.rag.store import DocumentStore, default_document_store


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def retrieve_relevant_chunks(
    document_id: str,
    query: str,
    top_k: int = 5,
    token_budget: int = 1500,
    store: DocumentStore | None = None,
    embedding_model: EmbeddingModel | None = None,
) -> list[str]:
    """
    Returns the `document_id` chunks most relevant to `query`, ranked
    by embedding cosine similarity, trimmed to fit `token_budget` --
    I-08's "retrieval context fits the target model's context budget"
    (respecting I-03's per-model limits, whatever budget the caller
    passes in for the actually-selected model).

    Returns [] for an unknown document rather than raising -- an
    ingested-document reference that no longer exists shouldn't break
    the chat request, just retrieve nothing.
    """

    store = store or default_document_store
    embedding_model = embedding_model or default_embedding_model

    document = store.get(document_id)

    if document is None or not document.chunks:
        return []

    query_embedding = embedding_model.embed_one(query)

    ranked = sorted(
        document.chunks,
        key=lambda chunk: _cosine_similarity(query_embedding, chunk.embedding),
        reverse=True,
    )

    selected: list[str] = []
    used_tokens = 0

    for chunk in ranked[:top_k]:
        chunk_tokens = estimate_chunk_tokens(chunk.text)

        if selected and used_tokens + chunk_tokens > token_budget:
            break

        selected.append(chunk.text)
        used_tokens += chunk_tokens

    return selected
