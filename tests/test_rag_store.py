from app.rag.store import DocumentChunk, DocumentStore


def _chunks(*texts: str) -> list[DocumentChunk]:
    return [DocumentChunk(text=t, embedding=[0.1, 0.2, 0.3]) for t in texts]


def test_ingest_returns_a_document_id_and_is_retrievable(tmp_path):
    store = DocumentStore(path=tmp_path / "docs.json")

    document_id = store.ingest("report.pdf", _chunks("chunk one", "chunk two"))

    document = store.get(document_id)
    assert document is not None
    assert document.filename == "report.pdf"
    assert len(document.chunks) == 2


def test_get_returns_none_for_unknown_document(tmp_path):
    store = DocumentStore(path=tmp_path / "docs.json")

    assert store.get("no-such-id") is None


def test_list_documents_returns_metadata_only(tmp_path):
    store = DocumentStore(path=tmp_path / "docs.json")
    store.ingest("a.pdf", _chunks("x"))
    store.ingest("b.pdf", _chunks("y", "z"))

    listing = store.list_documents()

    assert {d.filename for d in listing} == {"a.pdf", "b.pdf"}
    counts = {d.filename: d.chunk_count for d in listing}
    assert counts["b.pdf"] == 2


def test_forget_removes_a_document(tmp_path):
    store = DocumentStore(path=tmp_path / "docs.json")
    document_id = store.ingest("a.pdf", _chunks("x"))

    assert store.forget(document_id) is True
    assert store.get(document_id) is None


def test_forget_unknown_document_returns_false(tmp_path):
    store = DocumentStore(path=tmp_path / "docs.json")

    assert store.forget("no-such-id") is False


def test_persists_across_instances(tmp_path):
    path = tmp_path / "docs.json"
    store = DocumentStore(path=path)
    document_id = store.ingest("a.pdf", _chunks("x"))

    reloaded = DocumentStore(path=path)

    assert reloaded.get(document_id) is not None
