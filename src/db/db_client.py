import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

JSONDict = Dict[str, Any]


class DBClient:
    """
    Small helper class around SQLite for the agent.

    Responsibilities:
      - fetch / upsert invoices in the `invoices` table
      - fetch / create tickets in the `tickets` table
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        """Create SQLite connection with Row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _row_to_dict(row: sqlite3.Row | None) -> Optional[JSONDict]:
        """Convert sqlite3.Row to dict."""
        if row is None:
            return None
        return {k: row[k] for k in row.keys()}



    def get_invoice(self, invoice_id: str) -> Optional[JSONDict]:
        """
        Fetch a single invoice by its ID from the 'invoices' table.
        """
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM invoices WHERE invoice_id = ?",
                (invoice_id,),
            )
            row = cur.fetchone()
            return self._row_to_dict(row)

    def upsert_invoice(
        self,
        invoice: JSONDict,
        source_file: Optional[str] = None,
        status: str = "recorded",
    ) -> None:
        """
        Insert or update an invoice row.

        Expected keys in `invoice`:
          - invoice_id (required)
          - supplier_name
          - customer_name
          - invoice_date
          - due_date
          - total_amount
          - tax_amount
          - currency
        """
        if "invoice_id" not in invoice or not invoice["invoice_id"]:
            raise ValueError("invoice_id required")

        data = {
            "invoice_id": invoice.get("invoice_id"),
            "supplier_name": invoice.get("supplier_name"),
            "customer_name": invoice.get("customer_name"),
            "invoice_date": invoice.get("invoice_date"),
            "due_date": invoice.get("due_date"),
            "total_amount": invoice.get("total_amount"),
            "tax_amount": invoice.get("tax_amount"),
            "currency": invoice.get("currency"),
            "status": status,
            "source_file": source_file,
        }

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO invoices (
                    invoice_id, supplier_name, customer_name,
                    invoice_date, due_date, total_amount, tax_amount,
                    currency, status, source_file
                )
                VALUES (
                    :invoice_id, :supplier_name, :customer_name,
                    :invoice_date, :due_date, :total_amount, :tax_amount,
                    :currency, :status, :source_file
                )
                ON CONFLICT(invoice_id) DO UPDATE SET
                    supplier_name = excluded.supplier_name,
                    customer_name = excluded.customer_name,
                    invoice_date = excluded.invoice_date,
                    due_date = excluded.due_date,
                    total_amount = excluded.total_amount,
                    tax_amount = excluded.tax_amount,
                    currency = excluded.currency,
                    status = excluded.status,
                    source_file = excluded.source_file
                """,
                data,
            )
            conn.commit()

    # Ticket operations

    def get_ticket(self, ticket_id: str) -> Optional[JSONDict]:
        """
        Fetch a single ticket by its ID from the 'tickets' table.
        """
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM tickets WHERE ticket_id = ?",
                (ticket_id,),
            )
            row = cur.fetchone()
            return self._row_to_dict(row)

    def list_tickets_for_invoice(self, invoice_id: str) -> List[JSONDict]:
        """
        List all tickets associated with a given invoice, newest first.
        """
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT * FROM tickets WHERE invoice_id = ? "
                "ORDER BY created_date DESC",
                (invoice_id,),
            )
            rows = cur.fetchall()
            return [self._row_to_dict(r) for r in rows if r is not None]  # type: ignore[arg-type]

    def create_ticket(
        self,
        invoice_id: str,
        issue_type: str,
        description: str,
        recorded_amount: Optional[float] = None,
        document_amount: Optional[float] = None,
        priority: str = "High",
        status: str = "Open",
        created_by: str = "AI Agent",
        department: str = "Finance",
    ) -> JSONDict:
        """
        Create a new ticket row for an invoice discrepancy.

        Returns the created ticket as a dict.
        """
        # Generate a simple ticket ID, e.g. TCK-2025-ABCD
        year = datetime.now(timezone.utc).year
        short_id = uuid.uuid4().hex[:4].upper()
        ticket_id = f"TCK-{year}-{short_id}"

        created_date = datetime.now(timezone.utc).isoformat(timespec="seconds")

        data: JSONDict = {
            "ticket_id": ticket_id,
            "invoice_id": invoice_id,
            "created_date": created_date,
            "created_by": created_by,
            "department": department,
            "status": status,
            "priority": priority,
            "issue_type": issue_type,
            "recorded_amount": recorded_amount,
            "document_amount": document_amount,
            "description": description,
        }

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO tickets (
                    ticket_id, invoice_id, created_date, created_by, department,
                    status, priority, issue_type, recorded_amount, document_amount,
                    description
                )
                VALUES (
                    :ticket_id, :invoice_id, :created_date, :created_by, :department,
                    :status, :priority, :issue_type, :recorded_amount, :document_amount,
                    :description
                )
                """,
                data,
            )
            conn.commit()

        return data
