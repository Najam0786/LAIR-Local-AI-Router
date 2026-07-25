from pathlib import Path

from pypdf import PdfReader


def extract_pdf_pages(source: Path | str | bytes) -> list[str]:
    """
    Extracts per-page text from a PDF, entirely locally (`pypdf`,
    no network calls). Returns one string per page, in order; an
    unreadable or image-only (scanned) page yields an empty string
    rather than raising or guessing at its content.

    Scanned-page OCR via a local vision model (mentioned in
    docs/INNOVATION_PLAN_2026.md I-08's design notes) is explicitly
    deferred -- I-08's acceptance criteria targets text PDFs, and
    rendering a PDF page to an image for OCR needs a PDF-rasterization
    dependency (e.g. poppler) this pass doesn't introduce.
    """

    reader = PdfReader(source)

    return [page.extract_text() or "" for page in reader.pages]


def extract_pdf_text(source: Path | str | bytes) -> str:
    return "\n\n".join(extract_pdf_pages(source))
