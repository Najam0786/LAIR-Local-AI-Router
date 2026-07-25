import io

import app.api.documents as documents_module
from app.rag.embeddings import EmbeddingModel
from app.rag.store import DocumentStore


class _FakeEmbeddingModel(EmbeddingModel):
    def __init__(self):
        pass

    def embed(self, texts):
        return [[0.1, 0.2, 0.3] for _ in texts]

    def embed_one(self, text):
        return [0.1, 0.2, 0.3]


def _isolate(monkeypatch, tmp_path):
    store = DocumentStore(path=tmp_path / "docs.json")
    monkeypatch.setattr(documents_module, "default_document_store", store)
    monkeypatch.setattr(
        documents_module, "default_embedding_model", _FakeEmbeddingModel()
    )
    return store


def test_ingest_plain_text_document(client, monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)

    response = client.post(
        "/v1/lair/documents",
        files={"file": ("notes.txt", io.BytesIO(b"hello world " * 100), "text/plain")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "notes.txt"
    assert body["chunk_count"] >= 1
    assert body["document_id"]


def test_ingest_pdf_document(client, monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)

    from reportlab.lib.pagesizes import LETTER
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    c.drawString(72, 720, "Section one content about widgets")
    c.showPage()
    c.save()
    buffer.seek(0)

    response = client.post(
        "/v1/lair/documents",
        files={"file": ("report.pdf", buffer, "application/pdf")},
    )

    assert response.status_code == 200
    assert response.json()["filename"] == "report.pdf"


def test_ingest_empty_document_returns_400(client, monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)

    response = client.post(
        "/v1/lair/documents",
        files={"file": ("empty.txt", io.BytesIO(b""), "text/plain")},
    )

    assert response.status_code == 400


def test_list_documents(client, monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)

    client.post(
        "/v1/lair/documents",
        files={"file": ("a.txt", io.BytesIO(b"content a"), "text/plain")},
    )

    response = client.get("/v1/lair/documents")

    assert response.status_code == 200
    filenames = [d["filename"] for d in response.json()["documents"]]
    assert "a.txt" in filenames


def test_forget_document(client, monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)

    ingest = client.post(
        "/v1/lair/documents",
        files={"file": ("a.txt", io.BytesIO(b"content a"), "text/plain")},
    )
    document_id = ingest.json()["document_id"]

    response = client.delete(f"/v1/lair/documents/{document_id}")

    assert response.status_code == 200
    assert response.json()["forgotten"] is True


def test_forget_unknown_document_returns_404(client, monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)

    response = client.delete("/v1/lair/documents/no-such-id")

    assert response.status_code == 404
