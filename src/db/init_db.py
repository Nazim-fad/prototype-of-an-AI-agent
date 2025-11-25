import sqlite3
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).resolve().parents[2]  
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "finance.db"
SCHEMA_PATH = ROOT_DIR / "src" / "db" / "schema.sql"

def init_db():
    DATA_DIR.mkdir(exist_ok=True)

    print(f"Creating / updating DB at: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Create tables
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    cur.executescript(schema_sql)

    # Sample data

    # Example invoice data,
    invoices = [
        {
            "invoice_id": "INV-2025-000",
            "supplier_name": "GOTHAM OFFICE SUPPLIES INC.",
            "customer_name": "ACME ANALYTICS LLC",
            "invoice_date": "2025-01-10",
            "due_date": "2025-02-09",
            "total_amount": 4376.78,   
            "tax_amount": 356.78,
            "currency": "USD",
            "status": "recorded",
            "source_file": "data/sample_invoices/INV-2025-000.pdf",
        },
        
    ]

    # tickets = [
    #     {
    #         "ticket_id": "TCK-2025-000",
    #         "invoice_id": "INV-2025-000",
    #         "created_date": "2025-01-15",
    #         "created_by": "JANE SMITH",
    #         "department": "ACME ANALYTICS LLC - Finance",
    #         "status": "Open",
    #         "priority": "High",
    #         "issue_type": "Amount mismatch",
    #         "recorded_amount": 4300.00,   # what the system thinks
    #         "document_amount": 4376.78,   # what the pdf shows
    #         "description": (
    #             "System shows 4,300.00 USD for INV-2025-000, but the supplier "
    #             "invoice total is 4,376.78 USD including NYC sales tax."
    #         ),
    #     }
    # ]

    # Insert invoices
    cur.executemany(
        """
        INSERT OR REPLACE INTO invoices (
            invoice_id, supplier_name, customer_name,
            invoice_date, due_date, total_amount, tax_amount,
            currency, status, source_file
        )
        VALUES (
            :invoice_id, :supplier_name, :customer_name,
            :invoice_date, :due_date, :total_amount, :tax_amount,
            :currency, :status, :source_file
        )
        """,
        invoices,
    )

    # Insert tickets
    # cur.executemany(
    #     """
    #     INSERT OR REPLACE INTO tickets (
    #         ticket_id, invoice_id, created_date, created_by, department,
    #         status, priority, issue_type, recorded_amount, document_amount,
    #         description
    #     )
    #     VALUES (
    #         :ticket_id, :invoice_id, :created_date, :created_by, :department,
    #         :status, :priority, :issue_type, :recorded_amount, :document_amount,
    #         :description
    #     )
    #     """,
    #     tickets,
    # )

    conn.commit()
    conn.close()
    print("Database init and seeded with sample data.")

if __name__ == "__main__":
    init_db()
