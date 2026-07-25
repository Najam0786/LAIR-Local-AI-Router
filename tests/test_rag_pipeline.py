"""
End-to-end RAG-lite test (I-08 acceptance criteria): ingest a 100+
page text PDF and confirm a section-specific question retrieves the
correct section, using the *real* local embedding model (no fakes) --
this is the one test in the RAG suite that isn't mocked, and the one
that actually proves the pipeline works, not just that its pieces are
individually wired correctly.

Slower than the rest of the suite (real ONNX embedding inference over
~100 chunks) -- kept in its own file so it's easy to skip separately
if ever needed, without weakening what it actually verifies.
"""

import io

import pytest
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from app.rag.chunking import chunk_text
from app.rag.embeddings import default_embedding_model
from app.rag.pdf_extractor import extract_pdf_text
from app.rag.retrieval import retrieve_relevant_chunks
from app.rag.store import DocumentChunk, DocumentStore

# Distinct, searchable "sections" spread across 105 pages so a
# section-specific question has exactly one right answer to find.
SECTIONS = {
    10: "The quarterly revenue for the widgets division was 4.2 million dollars.",
    45: "Employee onboarding requires completing the safety training module.",
    80: "The server migration is scheduled for the third weekend of March.",
}


def _build_pdf(page_count: int = 105) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)

    for page_number in range(1, page_count + 1):
        text = SECTIONS.get(
            page_number,
            f"This is filler content for page {page_number} of the report, "
            "discussing general administrative matters of no particular "
            "significance to any specific topic.",
        )
        c.drawString(72, 720, f"Page {page_number}")
        c.drawString(72, 700, text)
        c.showPage()

    c.save()
    return buffer.getvalue()


@pytest.mark.slow
def test_ingest_100_plus_page_pdf_and_retrieve_the_right_section(tmp_path):
    pdf_bytes = _build_pdf(page_count=105)

    text = extract_pdf_text(io.BytesIO(pdf_bytes))
    chunks_text = chunk_text(text, chunk_size_tokens=120, overlap_tokens=20)

    assert len(chunks_text) > 20  # a real, multi-chunk document

    embeddings = default_embedding_model.embed(chunks_text)
    chunks = [
        DocumentChunk(text=t, embedding=e) for t, e in zip(chunks_text, embeddings)
    ]

    store = DocumentStore(path=tmp_path / "docs.json")
    document_id = store.ingest("quarterly_report.pdf", chunks)

    # top_k=1: the single best match must be the right section --
    # a meaningful bar for real embeddings, unlike requiring every
    # *other* section to be excluded from a wider top-k list (which
    # would fail even on a correctly-working retriever whenever two
    # sections happen to be moderately similar in embedding space).
    def top_match(question: str) -> str:
        results = retrieve_relevant_chunks(
            document_id,
            question,
            top_k=1,
            token_budget=1500,
            store=store,
            embedding_model=default_embedding_model,
        )
        assert results
        return results[0]

    assert "4.2 million" in top_match(
        "What was the revenue for the widgets division?"
    )
    assert "safety training" in top_match(
        "What does employee onboarding require?"
    )
    assert "third weekend of March" in top_match(
        "When is the server migration scheduled?"
    )


@pytest.mark.slow
def test_retrieval_context_fits_a_small_models_context_budget(tmp_path):
    pdf_bytes = _build_pdf(page_count=105)
    text = extract_pdf_text(io.BytesIO(pdf_bytes))
    chunks_text = chunk_text(text, chunk_size_tokens=120, overlap_tokens=20)
    embeddings = default_embedding_model.embed(chunks_text)
    chunks = [
        DocumentChunk(text=t, embedding=e) for t, e in zip(chunks_text, embeddings)
    ]

    store = DocumentStore(path=tmp_path / "docs.json")
    document_id = store.ingest("quarterly_report.pdf", chunks)

    # A small (~4B-class) local model's realistic context budget.
    small_model_token_budget = 2048

    results = retrieve_relevant_chunks(
        document_id,
        "When is the server migration scheduled?",
        top_k=10,
        token_budget=small_model_token_budget,
        store=store,
        embedding_model=default_embedding_model,
    )

    from app.rag.chunking import estimate_chunk_tokens

    total_tokens = sum(estimate_chunk_tokens(chunk) for chunk in results)
    assert total_tokens <= small_model_token_budget
    assert any("third weekend of March" in chunk for chunk in results)
