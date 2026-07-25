import math

from app.rag.chunking import estimate_chunk_tokens
from app.rag.embeddings import EmbeddingModel, default_embedding_model
from app.memory.store import MemoryStore, default_memory_store


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def retrieve_relevant_memories(
    project_scope: str,
    query: str,
    top_k: int = 5,
    token_budget: int = 500,
    store: MemoryStore | None = None,
    embedding_model: EmbeddingModel | None = None,
) -> list[str]:
    """
    Returns `project_scope`'s memories most relevant to `query`, ranked
    by embedding cosine similarity, trimmed to `token_budget` -- the
    same shape as `app.rag.retrieval.retrieve_relevant_chunks` (I-08),
    deliberately not a new design.
    """

    store = store or default_memory_store
    embedding_model = embedding_model or default_embedding_model

    records = store.all_for_scope(project_scope)

    if not records:
        return []

    query_embedding = embedding_model.embed_one(query)

    ranked = sorted(
        records,
        key=lambda record: _cosine_similarity(query_embedding, record.embedding),
        reverse=True,
    )

    selected: list[str] = []
    used_tokens = 0

    for record in ranked[:top_k]:
        record_tokens = estimate_chunk_tokens(record.text)

        if selected and used_tokens + record_tokens > token_budget:
            break

        selected.append(record.text)
        used_tokens += record_tokens

    return selected
