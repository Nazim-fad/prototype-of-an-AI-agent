import json
from typing import Any, Dict, Optional

from llama_index.core.llms import ChatMessage
from llama_index.tools.google import GmailToolSpec

from src.agent.llm_client import get_llm


# Type alias for clarity
ContextDict = Dict[str, Any]

# Singleton GmailToolSpec instance
_GMAIL_SPEC: Optional[GmailToolSpec] = None

# Prompts
EMAIL_SYSTEM_PROMPT = (
    "You are an assistant that drafts professional but concise emails "
    "about invoice discrepancies or issues.\n\n"
    "IMPORTANT CONSTRAINTS:\n"
    "- Write a FINAL email that can be sent directly, not a template.\n"
    "- Do NOT include any placeholders such as [Name], [Tour Name], [Company], "
    "[insert X], or similar bracketed text.\n"
    "- Do NOT ask the user to fill in missing information.\n"
    "- If some details are missing in the context, use neutral phrases like "
    "'the invoice', 'your company', or 'the finance system' instead of placeholders.\n"
    "- Do NOT include any JSON, metadata, or comments.\n"
    "- Use a clear, polite tone and keep the email focused on the concrete issue."
)

EMAIL_USER_PROMPT_TEMPLATE = (
    "Draft an email to the following recipient about the issues described in this context.\n\n"
    "Recipient: {recipient}\n\n"
    "Context (JSON):\n{context_json}\n\n"
    "The email should:\n"
    "- briefly explain the issue,\n"
    "- mention the relevant invoice or ticket identifiers if present,\n"
    "- clearly state what clarification or action is needed from the recipient,\n"
    "- be ready to send as-is, with NO placeholders or 'fill in' instructions.\n"
    "Start directly with an email greeting such as 'Hello,' or 'Dear Sir or Madam,' "
    "depending on what is appropriate from the context.\n"
)


def _get_gmail_spec() -> GmailToolSpec:
    """
    Return a singleton GmailToolSpec instance (handles OAuth and Gmail API).

    GmailToolSpec expects `credentials.json` (client secrets) and will create
    `token.json` on first use after the OAuth flow.
    """
    global _GMAIL_SPEC
    if _GMAIL_SPEC is None:
        _GMAIL_SPEC = GmailToolSpec()
    return _GMAIL_SPEC


def draft_email_tool(
    recipient: str,
    context: ContextDict,
) -> str:
    """
    Name:
        draft_email

    Tool description:
        Draft a professional but concise email body about an issue with
        an invoice or ticket, based on the provided context. This tool
        does NOT send the email; it only generates the body text.

    Input types and descriptions:
        recipient (str):
            Email address of the intended recipient.
        context (dict):
            JSON-serializable dictionary containing information about the
            document, math check, database values, reconciliation, and/or
            tickets. This is used by the LLM to write a specific email.

    Output type:
        str:
            The email body as plain text.
    """
    llm = get_llm()

    system_msg = ChatMessage(
        role="system",
        content=EMAIL_SYSTEM_PROMPT,
    )

    user_msg = ChatMessage(
        role="user",
        content=EMAIL_USER_PROMPT_TEMPLATE.format(
            recipient=recipient,
            context_json=json.dumps(context, indent=2),
        ),
    )

    response = llm.chat([system_msg, user_msg])
    return str(response.message.content)


def send_email_tool(
    recipient: str,
    subject: str,
    body: str,
) -> str:
    """
    Name:
        send_email

    Tool description:
        Send a plain-text email via Gmail using LlamaIndex's GmailToolSpec.
        Under the hood this uses the Gmail API OAuth flow (credentials.json /
        token.json) managed by LlamaIndex.

    Input types and descriptions:
        recipient (str):
            Email address of the recipient.
        subject (str):
            Subject line of the email.
        body (str):
            Plain-text email body.

    Output type:
        str:
            A short status message indicating success and the Gmail draft id.
    """
    gmail_spec = _get_gmail_spec()

    # Create a draft email
    draft = gmail_spec.create_draft(
        to=[recipient],
        subject=subject,
        message=body,
    )

    draft_id = draft.get("id")
    if not draft_id:
        raise RuntimeError("Gmail draft did not return an 'id' field.")

    # Send the draft
    gmail_spec.send_draft(draft_id=draft_id)

    return f"Email sent to {recipient} via Gmail draft {draft_id}"


