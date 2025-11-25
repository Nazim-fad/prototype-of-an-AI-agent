from pathlib import Path

from src.parsing.base_parser import parse_pdf_to_markdown
from src.parsing import (
    classify_document_from_text,
    parse_invoice_text,
    parse_ticket_text,
)


def test_invoice():
    invoice_path = Path("data/sample_invoices/INV_2025_001.pdf")  
    print(f"Testing invoice parsing on: {invoice_path}")

    full_text = parse_pdf_to_markdown(invoice_path) 
    classified = classify_document_from_text(full_text)
    print("Detected doc_type:", classified["doc_type"])

    if classified["doc_type"] != "invoice":
        print("Classifier did not detect 'invoice' — check your doc.")
        return

    parsed_invoice = parse_invoice_text(full_text)
    print("\nParsedInvoice:")
    print(parsed_invoice.model_dump())


def test_ticket():
    ticket_path = Path("data/sample_tickets/TCK_2025_001.pdf") 
    if not ticket_path.exists():
        print("\nNo sample ticket PDF found at:", ticket_path)
        print("Skipping ticket test.\n")
        return

    print(f"\nTesting ticket parsing on: {ticket_path}")

    full_text = parse_pdf_to_markdown(ticket_path)
    classified = classify_document_from_text(full_text)
    print("Detected doc_type:", classified["doc_type"])

    if classified["doc_type"] != "ticket":
        print("Classifier did not detect 'ticket' — check your doc.")
        return

    parsed_ticket = parse_ticket_text(full_text)
    print("\nParsedTicket:")
    print(parsed_ticket.model_dump())


if __name__ == "__main__":
    test_invoice()
    test_ticket()
