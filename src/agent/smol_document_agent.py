import json
from pathlib import Path
from typing import Any, Dict, Optional

from smolagents import CodeAgent, InferenceClientModel
from dotenv import load_dotenv
import os

from src.tools.parsing_tools import parse_document_tool
from src.tools.math_tools import validate_invoice_math_tool
from src.tools.reconciliation_tools import reconcile_invoice_with_db_tool
from src.tools.email_tools import draft_email_tool, send_email_tool
from src.tools.db_tools import (
    get_invoice_from_db_tool,
    upsert_invoice_in_db_tool,
    create_ticket_in_db_tool,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

HF_TOKEN = os.getenv("HF_TOKEN")

SMOL_SYSTEM_INSTRUCTIONS = """
You are an AI agent that processes supplier invoices and discrepancy tickets.

Your task is to process a PDF document end-to-end following a specific policy.

=== TOOLS AVAILABLE ===
You have access to the following tools (always use tools, never make up data):
- parse_document_tool: Extracts invoice/ticket data from PDF
- validate_invoice_math_tool: Checks if total = sum of items + tax
- reconcile_invoice_with_db_tool: Compares parsed amounts against DB records
- get_invoice_from_db_tool: Retrieves invoice from database
- upsert_invoice_in_db_tool: Inserts or updates invoice in database
- create_ticket_in_db_tool: Creates discrepancy ticket in database
- draft_email_tool: Composes email text
- send_email_tool: Sends email via Gmail
- final_answer: CALL THIS LAST with a complete summary dict

=== WORKFLOW POLICY ===
1. First, use parse_document_tool with the file_path to extract document data
2. For INVOICES:
   - Use validate_invoice_math_tool to check if math is correct
   - If math is WRONG: Draft and send email to supplier
   - If math is CORRECT: 
     - Use reconcile_invoice_with_db_tool to check for discrepancies
     - If is_match is None (new invoice): Use upsert_invoice_in_db_tool to add it
     - If is_match is False (discrepancies found): Use create_ticket_in_db_tool
     - If is_match is True (matches DB): No further action needed
3. For TICKETS: Use create_ticket_in_db_tool with parsed ticket data

=== FINAL ANSWER (CRITICAL) ===
ALWAYS end by calling final_answer() with a Python dict containing:
{
  "raw_text": "<full PDF text>",
  "doc_type": "invoice|ticket|unknown",
  "parsed_invoice": <dict or null>,
  "parsed_ticket": <dict or null>,
  "math_check": <result or null>,
  "db_invoice": <result or null>,
  "reconciliation": <result or null>,
  "ticket": <result or null>,
  "email_draft": "<text or null>",
  "email_status": "<status or null>"
}

DO NOT pass a string to final_answer. Pass the complete dict object above.
Your output will be parsed as JSON, so the dict must contain all required keys.
""".strip()


class SmolDocumentAgent:
    def __init__(self) -> None:
        self.model = InferenceClientModel(
            model_id="meta-llama/Meta-Llama-3.1-70B-Instruct",
            token=HF_TOKEN,
            temperature=0.1,  # deterministic
        )

        self.agent = CodeAgent(
            tools=[
                parse_document_tool,
                validate_invoice_math_tool,
                reconcile_invoice_with_db_tool,
                get_invoice_from_db_tool,
                upsert_invoice_in_db_tool,
                create_ticket_in_db_tool,
                draft_email_tool,
                send_email_tool,
            ],
            model=self.model,
            # domain-specific system instructions
            instructions=SMOL_SYSTEM_INSTRUCTIONS,
            add_base_tools=True,
            max_steps=20,
        )

    def run(
        self,
        file_path: Path,
        user_instruction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the full invoice/ticket workflow on a single PDF.

        Returns:
            A JSON-serializable dict summarizing the parsed document,
            math check, DB reconciliation, tickets and emails.
        """
        file_path_str = str(file_path)

        task = (
            "Process a single supplier document (invoice or discrepancy ticket) end-to-end.\n"
            "You are running inside a Python environment.\n"
            "You have the following Python variables already available:\n"
            f"- file_path = {file_path_str!r}\n"
            f"- user_instruction = {user_instruction or ''!r}\n\n"
            "Use the tools to parse the document, validate math, reconcile with the DB,\n"
            "and send emails or create tickets as needed, following your instructions.\n\n"
            "When you are done, call final_answer(summary_dict) where summary_dict is a Python dict\n"
            "with the structure described in your instructions."
        )

        # Plan how to solve the task
        raw_result = self.agent.run(
            task,
            additional_args={
                "file_path": file_path_str,
                "user_instruction": user_instruction or "",
            },
        )

        # Try to parse as JSON, but fall back to the raw output in case of errors.
        if isinstance(raw_result, dict):
            return raw_result

        try:
            return json.loads(raw_result)
        except (json.JSONDecodeError, TypeError) as e:
            # Agent returned invalid JSON - log the raw result for debugging
            return {
                "error": f"Agent returned invalid JSON: {str(e)}",
                "raw_output": str(raw_result),
                "doc_type": "error",
                "parsed_invoice": None,
                "parsed_ticket": None,
            }
