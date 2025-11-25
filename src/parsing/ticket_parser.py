import json
from pathlib import Path
from typing import Optional

from llama_index.core.bridge.pydantic import BaseModel, Field
from llama_index.core.llms import ChatMessage

from .base_parser import parse_pdf_to_markdown
from src.agent.llm_client import get_llm
from src.config.prompts import TICKET_SYSTEM_PROMPT, TICKET_USER_PROMPT


class ParsedTicket(BaseModel):
    """Structured representation of an internal invoice issue ticket."""

    ticket_id: Optional[str] = Field(
        None, description="Ticket identifier, e.g. TCK-2025-001"
    )
    invoice_id: Optional[str] = Field(
        None, description="Related invoice id, e.g. INV-2025-001"
    )
    created_date: Optional[str] = Field(
        None, description="Ticket creation date, as text"
    )
    created_by: Optional[str] = Field(
        None, description="Name of the person who created the ticket"
    )
    department: Optional[str] = Field(
        None, description="Department raising the ticket"
    )
    status: Optional[str] = Field(
        None, description="Ticket status (Open / In Progress / Resolved / Closed)"
    )
    priority: Optional[str] = Field(
        None, description="Ticket priority (Low / Medium / High)"
    )
    issue_type: Optional[str] = Field(
        None,
        description="Short description of issue type (amount mismatch, tax issue, etc.)",
    )
    recorded_amount: Optional[float] = Field(
        None, description="Amount recorded in finance system (if mentioned)"
    )
    document_amount: Optional[float] = Field(
        None, description="Amount shown on invoice document (if mentioned)"
    )
    description: Optional[str] = Field(
        None, description="Longer free-text description of the issue"
    )

    raw_text: str = Field(
        "", description="Full parsed text of the ticket PDF"
    )


def _extract_ticket_fields_from_text(text: str) -> ParsedTicket:
    """Use the local LLM (Ollama) to extract ticket fields as structured JSON."""
    llm = get_llm()
    sllm = llm.as_structured_llm(ParsedTicket)

    system_msg = ChatMessage(
        role="system",
        content=TICKET_SYSTEM_PROMPT,
    )

    user_msg = ChatMessage(
        role="user",
        content=TICKET_USER_PROMPT.format(text=text),
    )

    response = sllm.chat([system_msg, user_msg])
    content = response.message.content

    if isinstance(content, dict):
        data = content
    else:
        try:
            data = json.loads(content)
        except Exception:
            data = {}

    # raw_text may not be correctly set by the LLM, ensure it exists
    data.setdefault("raw_text", "")

    return ParsedTicket(**data)


def parse_ticket_text(text: str) -> ParsedTicket:
    """
    Preferred helper when you already have the full ticket text.
    """
    parsed = _extract_ticket_fields_from_text(text)
    parsed.raw_text = text
    return parsed


def parse_ticket_pdf(file_path: Path) -> ParsedTicket:
    """
    High-level helper: PDF -> markdown -> LLM extract -> ParsedTicket.
    """
    text = parse_pdf_to_markdown(file_path)
    return parse_ticket_text(text)
