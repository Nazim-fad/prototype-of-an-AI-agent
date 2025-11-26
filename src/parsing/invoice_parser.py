import json
from pathlib import Path
from typing import Optional

from llama_index.core.bridge.pydantic import BaseModel, Field
from llama_index.core.llms import ChatMessage

from .base_parser import parse_pdf_to_markdown
from src.agent.llm_client import get_llm
from src.config.prompts import INVOICE_SYSTEM_PROMPT, INVOICE_USER_PROMPT


class ParsedInvoice(BaseModel):
    """Structured representation of an invoice."""

    invoice_id: Optional[str] = Field(
        None, description="Invoice identifier, e.g. INV-2025-001"
    )
    supplier_name: Optional[str] = Field(
        None, description="Supplier name, e.g. GOTHAM OFFICE SUPPLIES INC."
    )
    customer_name: Optional[str] = Field(
        None, description="Customer name, e.g. ACME ANALYTICS LLC"
    )
    invoice_date: Optional[str] = Field(
        None, description="Invoice date as it appears, e.g. 'January 15, 2025'"
    )
    due_date: Optional[str] = Field(
        None, description="Due date as it appears, e.g. 'February 14, 2025'"
    )
    total_amount: Optional[float] = Field(
        None, description="Total amount due, numeric (e.g. 4376.78)"
    )
    tax_amount: Optional[float] = Field(
        None, description="Tax amount, numeric (e.g. 356.78)"
    )
    currency: Optional[str] = Field(
        None, description="Currency code, e.g. 'USD'"
    )

    contact_email: Optional[str] = Field(
        None,
        description=(
            "Email address to contact about this invoice, typically found in a "
            "line like 'For questions regarding this invoice, contact: ...'"
        ),
    )

    raw_text: str = Field(
        "", description="Full parsed text of the invoice PDF"
    )


def _extract_invoice_fields_from_text(text: str) -> ParsedInvoice:
    """
    Use the local LLM (Ollama) to extract invoice fields as structured JSON.
    """
    llm = get_llm()
    sllm = llm.as_structured_llm(ParsedInvoice)

    system_msg = ChatMessage(
        role="system",
        content=INVOICE_SYSTEM_PROMPT,
    )

    user_msg = ChatMessage(
        role="user",
        content=INVOICE_USER_PROMPT.format(text=text),
    )

    response = sllm.chat([system_msg, user_msg])

    # response.message.content should be a dict or JSON string for ParsedInvoice
    content = response.message.content
    if isinstance(content, dict):
        data = content
    else:
        try:
            data = json.loads(content)
        except Exception:
            data = {}

    # raw_text
    data.setdefault("raw_text", "")

    return ParsedInvoice(**data)


def parse_invoice_text(text: str) -> ParsedInvoice:
    """
    Preferred helper when you already have the full invoice text.
    """
    parsed = _extract_invoice_fields_from_text(text)
    parsed.raw_text = text
    return parsed


def parse_invoice_pdf(file_path: Path) -> ParsedInvoice:
    """
    High-level helper: PDF -> markdown -> LLM extract -> ParsedInvoice.
    """
    text = parse_pdf_to_markdown(file_path)
    return parse_invoice_text(text)
