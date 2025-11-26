import json
from typing import Any, Dict, Optional
from smolagents import tool
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
    "- Write a FINAL email that can be sent directly, the user will not edit it further.\n"
    "- If some details are missing in the context, use neutral phrases like "
    "'the invoice', 'your company', or 'the finance system' instead of placeholders.\n"
    "- Do NOT include any JSON, metadata, or comments.\n"
    "- Use a clear, polite tone and keep the email focused on the concrete issue."
)

EMAIL_USER_PROMPT_TEMPLATE = (
    "Write an email to the following recipient about the issues described in this context.\n\n"
    "Recipient: {recipient}\n\n"
    "Context (JSON):\n{context_json}\n\n"
    "The email should:\n"
    "- briefly explain the issue,\n"
    "- mention the relevant invoice or ticket identifiers if present,\n"
    "- clearly state what clarification or action is needed from the recipient,\n"
    "- the email should be ready to send as-is without further editing,\n"
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

@tool
def draft_email_tool(
    recipient: str,
    context: ContextDict,
) -> str:
    """
    Draft a professional email describing an invoice or ticket issue.

    Args:
        recipient: Email address that the message is intended for.
        context: JSON-serializable dictionary containing information
            about the document and checks performed, such as parsed
            invoice or ticket data, math validation result, database
            reconciliation result, any created tickets, and user
            instructions.

    Returns:
        A plain-text email body that can be sent as-is to the recipient.
        The text is intended to be clear, concise, and business-appropriate.
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

@tool
def send_email_tool(
    recipient: str,
    subject: str,
    body: str,
) -> str:
    """
    Send an email via Gmail using the configured OAuth credentials.

    Args:
        recipient: Email address to send the message to.
        subject: Subject line for the email.
        body: Plain-text body of the email.

    Returns:
        A short status message describing the result of the send
        operation, usually including a draft or message identifier
        returned by the Gmail API.
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


