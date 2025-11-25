CREATE TABLE IF NOT EXISTS invoices (
    invoice_id      TEXT PRIMARY KEY,
    supplier_name   TEXT,
    customer_name   TEXT,
    invoice_date    TEXT,   -- date string like 2025-01-15
    due_date        TEXT,
    total_amount    REAL,
    tax_amount      REAL,
    currency        TEXT,
    status          TEXT,   -- recorded / paid / pending
    source_file     TEXT    -- path to the PDF
);

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id       TEXT PRIMARY KEY,
    invoice_id      TEXT,
    created_date    TEXT,
    created_by      TEXT,
    department      TEXT,
    status          TEXT,   -- Open / In Progress / Resolved / Closed
    priority        TEXT,   -- Low / Medium / High
    issue_type      TEXT,   -- Amount mismatch / Tax issue / etc.
    recorded_amount REAL,   -- amount in system (according to ticket)
    document_amount REAL,   -- amount on invoice (according to ticket)
    description     TEXT
);
