from pathlib import Path
from typing import Any, Dict, Optional
from smolagents import tool


from src.parsing.base_parser import parse_pdf_to_markdown
from src.parsing.document_classifier import classify_document_from_text
from src.parsing.invoice_parser import parse_invoice_text, ParsedInvoice
from src.parsing.ticket_parser import parse_ticket_text, ParsedTicket

@tool
def parse_document_tool(file_path: str) -> Dict[str, Any]:
    """
    Classify and parse a financial PDF document (invoice or ticket).

    Args:
        file_path: Path to the PDF file on disk. Must exist and be a
            readable PDF, typically in the uploads directory.

    Returns:
        A dictionary with:
            doc_type: String label for the detected document type
                ("invoice", "ticket", or "unknown").
            raw_text: Full markdown/text content of the document as
                returned by the PDF parser.
            parsed_invoice: Parsed invoice fields as a dictionary, or
                None if the document is not an invoice.
            parsed_ticket: Parsed ticket fields as a dictionary, or
                None if the document is not a ticket.
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
