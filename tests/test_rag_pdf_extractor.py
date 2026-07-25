import io

from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

from app.rag.pdf_extractor import extract_pdf_pages, extract_pdf_text


def _make_pdf(page_texts: list[str]) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)

    for text in page_texts:
        c.drawString(72, 720, text)
        c.showPage()

    c.save()
    return buffer.getvalue()


def test_extract_pdf_pages_returns_one_string_per_page():
    pdf_bytes = _make_pdf(["Page one content", "Page two content", "Page three"])

    pages = extract_pdf_pages(io.BytesIO(pdf_bytes))

    assert len(pages) == 3
    assert "Page one content" in pages[0]
    assert "Page two content" in pages[1]
    assert "Page three" in pages[2]


def test_extract_pdf_text_joins_all_pages():
    pdf_bytes = _make_pdf(["Alpha section", "Beta section"])

    text = extract_pdf_text(io.BytesIO(pdf_bytes))

    assert "Alpha section" in text
    assert "Beta section" in text
