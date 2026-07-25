from app.rag.chunking import chunk_text, estimate_chunk_tokens


def test_empty_text_yields_no_chunks():
    assert chunk_text("") == []


def test_short_text_yields_a_single_chunk():
    chunks = chunk_text("hello world", chunk_size_tokens=300, overlap_tokens=50)

    assert len(chunks) == 1
    assert chunks[0] == "hello world"


def test_long_text_is_split_into_multiple_chunks():
    text = " ".join(f"word{i}" for i in range(2000))

    chunks = chunk_text(text, chunk_size_tokens=100, overlap_tokens=10)

    assert len(chunks) > 1


def test_chunks_overlap():
    text = " ".join(f"word{i}" for i in range(500))

    chunks = chunk_text(text, chunk_size_tokens=100, overlap_tokens=20)

    first_words = chunks[0].split()
    second_words = chunks[1].split()

    assert first_words[-1] in second_words[:30]


def test_no_word_is_dropped_across_chunk_boundaries():
    words = [f"word{i}" for i in range(500)]
    text = " ".join(words)

    chunks = chunk_text(text, chunk_size_tokens=100, overlap_tokens=10)
    covered = set()
    for chunk in chunks:
        covered.update(chunk.split())

    assert covered == set(words)


def test_estimate_chunk_tokens_is_positive_for_nonempty_text():
    assert estimate_chunk_tokens("some text here") > 0
