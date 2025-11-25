import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from llama_index.core.llms import ChatMessage

from src.agent.llm_client import get_llm
from src.config.prompts import DOCUMENT_PLANNER_SYSTEM_PROMPT, DOCUMENT_PLANNER_USER_PROMPT_TEMPLATE
from src.tools import (
    parse_document_tool,
    validate_invoice_math_tool,
    reconcile_invoice_with_db_tool,
    draft_email_tool,
    send_email_tool,
)
from src.db.db_client import DBClient


FALLBACK_ACTIONS: List[str] = [
    "parse_document",
    "validate_invoice_math",
    "get_db_invoice",
    "insert_invoice",
    "reconcile_invoice",
    "create_ticket",
]


class DocumentAgent:
    """
    LLM-powered agent for invoice/ticket workflows.

    Flows:

      Invoice with invalid math:
         - validate_invoice_math_tool => is_valid == False
         - ALWAYS draft + send email to supplier (or default recipient).

      Invoice with valid math but DB mismatch:
         - validate_invoice_math_tool => is_valid == True
         - get_db_invoice + reconcile_invoice_with_db_tool
         - if differences => create_ticket in DB.

      Invoice with valid math and NOT in DB:
         - validate_invoice_math_tool => is_valid == True
         - get_db_invoice => None
         - if auto_insert_new_invoices=True => insert_invoice (upsert into DB).

      Ticket document:
         - parse_document_tool => doc_type == "ticket"
         - insert a ticket row in DB using parsed_ticket fields.
    """

    def __init__(
        self,
        db_path: Path,
        auto_insert_new_invoices: bool = False,
        default_email_recipient: str = "nazimabc1@gmail.com",
    ) -> None:
        self.llm = get_llm()
        self.db = DBClient(db_path)
        self.db_path = Path(db_path)
        self.auto_insert_new_invoices = auto_insert_new_invoices
        self.default_email_recipient = default_email_recipient


    # Planning


    def _plan_document_workflow(
        self,
        user_instruction: str | None,
    ) -> Dict[str, Any]:
        """
        Use the LLM to produce a simple JSON plan of actions.

        The planner only decides high-level actions like:
          - parse_document
          - validate_invoice_math
          - get_db_invoice
          - insert_invoice
          - reconcile_invoice
          - create_ticket
          - draft_email
        """
        system_msg = ChatMessage(
            role="system",
            content=DOCUMENT_PLANNER_SYSTEM_PROMPT,
        )

        user_content = {
            "user_instruction": user_instruction or "",
            "settings": {
                "auto_insert_new_invoices": self.auto_insert_new_invoices,
                "default_email_recipient": self.default_email_recipient,
            },
        }

        user_msg = ChatMessage(
            role="user",
            content=DOCUMENT_PLANNER_USER_PROMPT_TEMPLATE.format(
                user_instruction=user_content["user_instruction"],
                settings_json=json.dumps(user_content["settings"], indent=2),
            ),
        )

        response = self.llm.chat([system_msg, user_msg])
        raw = response.message.content

        try:
            plan = json.loads(raw)
        except Exception:
            # Robust fallback: run the full invoice pipeline
            plan = {
                "actions": FALLBACK_ACTIONS.copy(),
                "notes": (
                    "Fallback plan: parse + math + db + reconcile + ticket "
                    "due to JSON parsing error."
                ),
            }

        actions: List[str] = plan.get("actions") or []

        # Always ensure parse_document is present and first
        if "parse_document" not in actions:
            actions.insert(0, "parse_document")
        else:
            # Move parse_document to the front if needed
            actions = ["parse_document"] + [
                a for a in actions if a != "parse_document"
            ]

        if "get_db_invoice" in actions:
            for extra in ("reconcile_invoice", "create_ticket", "insert_invoice"):
                if extra not in actions:
                    actions.append(extra)

        plan["actions"] = actions
        return plan


    # Main entrypoint 

    def handle_document(
        self,
        file_path: Path,
        user_instruction: str | None,
    ) -> Dict[str, Any]:
        """
        Main API called from Streamlit.

        Returns a dict with:
          - plan
          - doc_type
          - parsed_invoice / parsed_ticket
          - raw_text
          - math_check
          - db_invoice
          - reconciliation
          - ticket
          - email_draft
          - email_status
        """
        file_path = Path(file_path)

        plan = self._plan_document_workflow(
            user_instruction=user_instruction,
        )

        result: Dict[str, Any] = {
            "plan": plan,
            "doc_type": None,
            "parsed_invoice": None,
            "parsed_ticket": None,
            "raw_text": None,
            "math_check": None,
            "db_invoice": None,
            "reconciliation": None,
            "ticket": None,
            "email_draft": None,
            "email_status": None,
        }

        parsed: Optional[Dict[str, Any]] = None
        math_check: Optional[Dict[str, Any]] = None
        db_invoice: Optional[Dict[str, Any]] = None
        reconciliation: Optional[Dict[str, Any]] = None
        created_ticket: Optional[Dict[str, Any]] = None

        for action in plan["actions"]:
            # Always parse first time we see parse_document
            if action == "parse_document":
                if result["raw_text"] is None:  
                    parsed = parse_document_tool(str(file_path))
                    result["doc_type"] = parsed["doc_type"]
                    result["parsed_invoice"] = parsed["parsed_invoice"]
                    result["parsed_ticket"] = parsed["parsed_ticket"]
                    result["raw_text"] = parsed["raw_text"]
                # After parsing, continue to next action
                continue

            # From here on, only do invoice-specific actions if we actually have one
            if result["doc_type"] != "invoice":
                continue

            invoice = result["parsed_invoice"] or {}
            raw_text = result["raw_text"] or ""

            if action == "validate_invoice_math":
                math_check = validate_invoice_math_tool(invoice, raw_text)
                result["math_check"] = math_check

            elif action == "get_db_invoice":
                invoice_id = invoice.get("invoice_id")
                if invoice_id:
                    db_invoice = self.db.get_invoice(invoice_id)
                    result["db_invoice"] = db_invoice

            elif action == "insert_invoice":
                # auto_insert_new_invoices is True
                if not self.auto_insert_new_invoices:
                    continue

                invoice_id = invoice.get("invoice_id")
                if not invoice_id:
                    continue

                if db_invoice is not None:
                    continue

                is_valid = None if math_check is None else math_check.get("is_valid")
                if is_valid is False:
                    continue

                self.db.upsert_invoice(
                    invoice,
                    source_file=str(file_path),
                    status="recorded",
                )
                db_invoice = self.db.get_invoice(invoice_id)
                result["db_invoice"] = db_invoice

            elif action == "reconcile_invoice":
                # reconcile doc vs DB if we have both
                if invoice.get("invoice_id") and db_invoice is not None:
                    reconciliation = reconcile_invoice_with_db_tool(
                        invoice, db_invoice
                    )
                    result["reconciliation"] = reconciliation

            elif action == "create_ticket":
                # only create a ticket if reconciliation says there are differences
                if not reconciliation or not reconciliation.get("differences"):
                    continue

                invoice_id = invoice.get("invoice_id")
                if not invoice_id:
                    continue

                desc_lines = reconciliation["differences"]
                description = (
                    "Discrepancy between invoice document and DB:\n"
                    + "\n".join(f"- {line}" for line in desc_lines)
                )

                recorded_amount = None
                document_amount = invoice.get("total_amount")

                created_ticket = self.db.create_ticket(
                    invoice_id=invoice_id,
                    issue_type="Amount mismatch",
                    description=description,
                    recorded_amount=recorded_amount,
                    document_amount=document_amount,
                )
                result["ticket"] = created_ticket

            elif action == "draft_email":
                # Decide recipient
                recipient = invoice.get("contact_email") or self.default_email_recipient

                context = {
                    "doc_type": result["doc_type"],
                    "invoice": invoice,
                    "math_check": math_check,
                    "db_invoice": db_invoice,
                    "reconciliation": reconciliation,
                    "created_ticket": created_ticket,
                    "user_instruction": user_instruction,
                }

                email_body = draft_email_tool(recipient, context)
                result["email_draft"] = email_body

                inv_id = invoice.get("invoice_id") or "unknown invoice"
                subject = f"Discrepancy detected on {inv_id}"

                status = send_email_tool(recipient, subject, email_body)
                result["email_status"] = status

        # ticket documents 

        if (
            result["doc_type"] == "ticket"
            and result.get("parsed_ticket")
            and result.get("ticket") is None
        ):
            pt = result["parsed_ticket"] or {}
            invoice_id_for_ticket = pt.get("invoice_id") or "UNKNOWN"

            created_ticket = self.db.create_ticket(
                invoice_id=invoice_id_for_ticket,
                issue_type=pt.get("issue_type") or "Ticket from document",
                description=pt.get("description")
                or f"Ticket {pt.get('ticket_id') or ''} from document.",
                recorded_amount=pt.get("recorded_amount"),
                document_amount=pt.get("document_amount"),
            )
            result["ticket"] = created_ticket

        # Auto-email on invalid math

        if (
            result["doc_type"] == "invoice"
            and result.get("math_check")
            and result["math_check"].get("is_valid") is False
            and result.get("email_status") is None  
        ):
            invoice = result["parsed_invoice"] or {}
            recipient = invoice.get("contact_email") or self.default_email_recipient

            context = {
                "doc_type": result["doc_type"],
                "invoice": invoice,
                "math_check": result["math_check"],
                "db_invoice": result.get("db_invoice"),
                "reconciliation": result.get("reconciliation"),
                "created_ticket": result.get("ticket"),
                "user_instruction": user_instruction,
            }

            email_body = draft_email_tool(recipient, context)
            result["email_draft"] = email_body

            inv_id = invoice.get("invoice_id") or "unknown invoice"
            subject = f"Discrepancy detected on {inv_id}"

            status = send_email_tool(recipient, subject, email_body)
            result["email_status"] = status

        return result
