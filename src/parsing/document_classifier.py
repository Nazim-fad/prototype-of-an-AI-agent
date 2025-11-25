from pathlib import Path
from typing import Literal, TypedDict

from .base_parser import parse_pdf_to_markdown

DocType = Literal["invoice", "ticket", "unknown"]


class ClassifiedDocument(TypedDict):
    """Simple classification result for a parsed document."""

    doc_type: DocType
    text: str  # full text / markdown of the document


def classify_document_from_text(full_text: str) -> ClassifiedDocument:
    """
    Classify a document based on its text content.

    We only inspect the first ~2000 characters for speed, since the header
    and initial sections are usually enough to distinguish between an
    invoice and a discrepancy ticket.
    """
    # Only the beginning is needed 
    head = full_text[:2000].lower()

    if "invoice discrepancy ticket" in head or "ticket id" in head:
        doc_type: DocType = "ticket"
    elif "invoice" in head and "invoice #" in head:
        doc_type = "invoice"
    else:
        doc_type = "unknown"

    return ClassifiedDocument(doc_type=doc_type, text=full_text)


def classify_document(file_path: Path) -> ClassifiedDocument:
    """
    Convenience helper: parse the PDF with LlamaParse, then classify.

    This *will* call LlamaParse internally. In the main agent workflow we
    prefer classify_document_from_text(full_text) to avoid parsing twice.
    """
    full_text = parse_pdf_to_markdown(file_path)
    return classify_document_from_text(full_text)
