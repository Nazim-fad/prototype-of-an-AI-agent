from pathlib import Path
from typing import Any, Dict, Optional

from smolagents import tool
from src.db.db_client import DBClient


DB_PATH = Path("data/finance.db") 


@tool
def get_invoice_from_db_tool(invoice_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a single invoice by its ID from the database.

    Args:
        invoice_id: The unique identifier of the invoice to fetch.

    Returns:
        The invoice record as a dictionary, or `None` if not found.
    """
    db = DBClient(DB_PATH)
    return db.get_invoice(invoice_id)


@tool
def upsert_invoice_in_db_tool(invoice: Dict[str, Any]) -> str:
    """
    Insert or update an invoice record in the database.

    Args:
        invoice: The invoice data to upsert. Must include an 'invoice_id' key.

    Returns:
        A short status message indicating the invoice was upserted.
    """
    db = DBClient(DB_PATH)
    db.upsert_invoice(invoice)
    return f"Invoice {invoice.get('invoice_id')} upserted successfully."


@tool
def create_ticket_in_db_tool(
    invoice_id: str,
    issue_type: str,
    description: str,
    recorded_amount: float | None = None,
    document_amount: float | None = None,
) -> Dict[str, Any]:
    """
    Create a new ticket in the database for a given invoice issue.

    Args:
        invoice_id: The ID of the invoice related to the ticket.
        issue_type: The type/category of the issue (e.g., "math_error").
        description: A detailed description of the issue.
        recorded_amount: The amount recorded in the system, if applicable.
        document_amount: The amount found in the document, if applicable.

    Returns:
        The created ticket record as a dictionary.
    """
    db = DBClient(DB_PATH)
    ticket = db.create_ticket(
        invoice_id=invoice_id,
        issue_type=issue_type,
        description=description,
        recorded_amount=recorded_amount,
        document_amount=document_amount,
    )
    return ticket


