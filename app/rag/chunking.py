from app.execution.context_compression import estimate_tokens

# ~4 chars/token (I-09's same rule of thumb) means ~0.75 words/token
# for typical English text -- used only to convert a token budget into
# a word-count chunk size, not as a precise count.
_WORDS_PER_TOKEN_ESTIMATE = 0.75


def chunk_text(
    text: str,
    chunk_size_tokens: int = 300,
    overlap_tokens: int = 50,
) -> list[str]:
    """
    Splits text into overlapping, roughly token-sized chunks (I-08).

    Word-based, not a real tokenizer -- consistent with the same
    approximation `estimate_tokens` (I-09) already uses elsewhere in
    this codebase, rather than introducing a second, differently-
    calibrated chunking heuristic.
    """

    words = text.split()

    if not words:
        return []

    chunk_size_words = max(1, int(chunk_size_tokens * _WORDS_PER_TOKEN_ESTIMATE))
    overlap_words = max(0, int(overlap_tokens * _WORDS_PER_TOKEN_ESTIMATE))
    step = max(1, chunk_size_words - overlap_words)

    chunks: list[str] = []

    for start in range(0, len(words), step):
        chunk_words = words[start : start + chunk_size_words]

        if not chunk_words:
            continue

        chunks.append(" ".join(chunk_words))

        if start + chunk_size_words >= len(words):
            break

    return chunks


def estimate_chunk_tokens(chunk: str) -> int:
    return estimate_tokens(chunk)
