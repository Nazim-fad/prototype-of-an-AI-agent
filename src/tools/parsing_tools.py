from pathlib import Path
from typing import Any, Dict, Optional

from src.parsing.base_parser import parse_pdf_to_markdown
from src.parsing.document_classifier import classify_document_from_text
from src.parsing.invoice_parser import parse_invoice_text, ParsedInvoice
from src.parsing.ticket_parser import parse_ticket_text, ParsedTicket


def parse_document_tool(file_path: str) -> Dict[str, Any]:
    """
    Parse a PDF document into structured invoice or ticket data.
    
    Uses LlamaParse to convert PDF to markdown, classifies the document type,
    and extracts structured fields accordingly.
    
    Args:
        file_path: Path to the PDF file.
    
    Returns:
        Dict with keys:
            - doc_type: "invoice", "ticket", or "unknown"
            - raw_text: Full markdown content
            - parsed_invoice: Extracted invoice fields (if invoice), else None
            - parsed_ticket: Extracted ticket fields (if ticket), else None
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Parse with LlamaParse
    full_text = parse_pdf_to_markdown(path)

    # Classify
    classified = classify_document_from_text(full_text)
    doc_type = classified["doc_type"]

    parsed_invoice: Optional[ParsedInvoice] = None
    parsed_ticket: Optional[ParsedTicket] = None

    # Parse according to doc_type
    if doc_type == "invoice":
        parsed_invoice = parse_invoice_text(full_text)
    elif doc_type == "ticket":
        parsed_ticket = parse_ticket_text(full_text)

    return {
        "doc_type": doc_type,
        "raw_text": full_text,
        "parsed_invoice": parsed_invoice.model_dump() if parsed_invoice else None,
        "parsed_ticket": parsed_ticket.model_dump() if parsed_ticket else None,
    }
