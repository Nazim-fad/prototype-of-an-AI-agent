"""prompts"""

# Invoice extraction prompts
INVOICE_SYSTEM_PROMPT = (
    "You are an AI assistant that extracts structured fields from invoice text. "
    "Only extract what is present in the text. If something is missing, set it to null. "
    "Do NOT hallucinate or guess new values."
)

INVOICE_USER_PROMPT = (
    "You are an information extraction assistant. "
    "Given the full text of a single invoice, extract a JSON object "
    "that matches exactly the following ParsedInvoice schema:\n\n"
    "{{\n"
    '  "invoice_id": string | null,\n'
    '  "supplier_name": string | null,\n'
    '  "customer_name": string | null,\n'
    '  "invoice_date": string | null,\n'
    '  "due_date": string | null,\n'
    '  "total_amount": number | null,\n'
    '  "tax_amount": number | null,\n'
    '  "currency": string | null,\n'
    '  "contact_email": string | null,\n'
    '  "raw_text": string | null\n'
    "}}\n\n"
    "Extraction rules:\n"
    "- invoice_id: the invoice number, e.g. 'INV-2025-001'.\n"
    "- supplier_name: the supplier company name at the top of the invoice "
    "  (e.g. 'GOTHAM OFFICE SUPPLIES INC.').\n"
    "- customer_name: the company listed under 'Bill To:' "
    "  (use exactly the line that contains the company name, e.g. 'ACME ANALYTICS LLC').\n"
    "- invoice_date: the date labeled 'Invoice Date'.\n"
    "- due_date: the date labeled 'Due Date'.\n"
    "- total_amount: the numeric grand total for the invoice "
    "  (e.g. 4376.78), typically from 'Total Amount Due'.\n"
    "- tax_amount: the numeric sales tax amount, if present "
    "  (e.g. from 'Sales Tax (NYC 8.875%)').\n"
    "- currency: three-letter currency code, e.g. 'USD'.\n"
    "- contact_email: the billing/contact email address shown on the invoice "
    "  (for example in the header or in the 'Notes' section, e.g. 'billing@gotham-office.com').\n"
    "- raw_text: set this to the full invoice text you received as input.\n\n"
    "Formatting rules:\n"
    "- For numeric fields (total_amount, tax_amount), output plain numbers "
    "  without currency symbols or thousands separators "
    "  (e.g. 4376.78, not '4,376.78 USD').\n"
    "- If a field truly does not appear in the text, set it to null.\n"
    "- Do NOT guess or invent values.\n"
    "- Use the exact strings from the invoice for names and dates.\n\n"
    "Return ONLY the JSON object, with no explanation, no markdown, and no extra text.\n\n"
    "INVOICE TEXT:\n{text}\n"
)

# Ticket extraction prompts
TICKET_SYSTEM_PROMPT = (
    "You are an AI assistant that extracts structured fields from a ticket "
    "describing an invoice issue. Only extract what is present in the text. "
    "If a field is missing, set it to null. Do NOT hallucinate or guess values."
)

TICKET_USER_PROMPT = (
    "You are an information extraction assistant. "
    "Given the full text of a single invoice discrepancy ticket, "
    "extract a JSON object that matches exactly the following ParsedTicket schema:\n\n"
    "{{\n"
    '  "ticket_id": string | null,\n'
    '  "invoice_id": string | null,\n'
    '  "created_date": string | null,\n'
    '  "created_by": string | null,\n'
    '  "department": string | null,\n'
    '  "status": string | null,\n'
    '  "priority": string | null,\n'
    '  "issue_type": string | null,\n'
    '  "recorded_amount": number | null,\n'
    '  "document_amount": number | null,\n'
    '  "description": string | null,\n'
    '  "raw_text": string | null\n'
    "}}\n\n"
    "Field definitions:\n"
    "- ticket_id: the ticket identifier (e.g. 'TCK-2025-001').\n"
    "- invoice_id: the related invoice identifier (e.g. 'INV-2025-001').\n"
    "- created_date: the ticket creation date.\n"
    "- created_by: the person who created the ticket, including role if present.\n"
    "- department: the department or team responsible (e.g. 'ACME ANALYTICS LLC – Finance').\n"
    "- status: the ticket status (e.g. 'Open', 'Closed').\n"
    "- priority: the ticket priority (e.g. 'High').\n"
    "- issue_type: short label of the issue type (e.g. 'Amount mismatch').\n"
    "- recorded_amount: the amount stored in the finance system, "
    "  usually labeled something like 'Recorded Amount'.\n"
    "- document_amount: the amount shown on the supplier invoice PDF, "
    "  usually labeled something like 'Document Amount'.\n"
    "- description: a concise summary of the issue in 1–3 sentences. "
    "  Prefer the 'Short Summary' or main 'Description' section if present.\n"
    "- raw_text: set this to the full ticket text you received as input.\n\n"
    "Formatting rules:\n"
    "- For numeric fields (recorded_amount, document_amount), output plain numbers "
    "  without currency symbols or thousands separators "
    "  (e.g. 4376.78, not '4,376.78 USD').\n"
    "- If a field truly does not appear in the text, set it to null.\n"
    "- Do NOT guess or invent values.\n"
    "- Use the exact strings from the ticket for IDs, names, and dates.\n\n"
    "Return ONLY the JSON object, with no explanation, no markdown, and no extra text.\n\n"
    "TICKET TEXT:\n{text}\n"
)

# Document agent planning prompts
DOCUMENT_PLANNER_SYSTEM_PROMPT: str = (
    "You are a planning assistant for an agent that processes invoices "
    "and discrepancy tickets.\n\n"
    "Available actions in the pipeline:\n"
    "- parse_document: classify and parse the PDF into structured fields.\n"
    "- validate_invoice_math: check if invoice totals and tax are consistent.\n"
    "- get_db_invoice: fetch the invoice from the SQLite database.\n"
    "- insert_invoice: insert a new valid invoice into the database.\n"
    "- reconcile_invoice: compare parsed invoice with DB values.\n"
    "- create_ticket: open a discrepancy ticket if DB and document differ.\n"
    "- draft_email: draft an email about issues with the invoice.\n\n"
    "You must always include 'parse_document' as the first action.\n"
    "Return ONLY a JSON object, no extra commentary."
)

DOCUMENT_PLANNER_USER_PROMPT_TEMPLATE: str = (
    "Plan a reasonable sequence of actions for handling a single uploaded document.\n"
    "In general:\n"
    "- Always start with parse_document.\n"
    "- If the document looks like an invoice, you usually want to also run "
    "  validate_invoice_math and get_db_invoice.\n"
    "- If invoice math is invalid, draft_email is appropriate.\n"
    "- If math is valid but DB values differ, create_ticket is appropriate.\n"
    "- If the user instruction says not to touch the database, you may skip "
    "  get_db_invoice / insert_invoice / reconcile_invoice / create_ticket.\n\n"
    "Respond with JSON like:\n"
    "{{\n"
    '  "actions": ["parse_document", "validate_invoice_math", "get_db_invoice"],\n'
    '  "notes": "Short explanation of the chosen actions."\n'
    "}}\n\n"
    "User instruction (may be empty):\n{user_instruction}\n\n"
    "Settings:\n{settings_json}\n"
)

# Chat agent planning prompts
PLANNER_SYSTEM_PROMPT: str = (
    "You are a planning assistant for chatting about a single uploaded document "
    "(an invoice or a ticket). You have two tools:\n"
    "- 'structured_fields': use parsed JSON fields if the question is about "
    "  specific amounts, IDs, dates, names, or status.\n"
    "- 'rag_over_text': use semantic search over the raw text if the question is "
    "  about narrative details, explanations, or wording.\n"
    "Return ONLY JSON with which tools to use."
)

PLANNER_USER_PROMPT_TEMPLATE: str = (
    "Decide which tools to use for answering this question.\n"
    "You must respond with a JSON object, for example:\n"
    '{{ "actions": ["structured_fields", "rag_over_text"] }}\n\n'
    "Question:\n{question}\n\n"
    "Context flags:\n{flags_json}\n"
)

# Chat system prompt
CHAT_SYSTEM_PROMPT: str = (
    "You are an assistant that answers questions about a single financial document "
    "(either an invoice or a discrepancy ticket).\n"
    "- Use the structured JSON fields when the question is about amounts, IDs, dates, "
    "  suppliers, customers, or status.\n"
    "- Use the RAG context for longer explanations or where the wording/details in "
    "  the document matter.\n"
    "- You also see the previous conversation turns: stay consistent with your past answers.\n"
    "Always be concise and always base your answers on the document and its parsed fields."
)
