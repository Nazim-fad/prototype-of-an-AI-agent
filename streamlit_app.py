import streamlit as st
from pathlib import Path

from src.ui.header import inject_custom_header
from src.ui.workflow_tab import render_workflow_tab
from src.ui.chat_tab import render_chat_tab


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
STATIC_DIR = PROJECT_ROOT / "static"
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    st.set_page_config(
        page_title="Invoice Agent",
        layout="wide",
    )

    if "doc_context" not in st.session_state:
        st.session_state["doc_context"] = {
            "raw_text": None,
            "parsed_invoice": None,
            "parsed_ticket": None,
        }

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    if "chat_agent" not in st.session_state:
        st.session_state["chat_agent"] = None
        st.session_state["chat_agent_doc_id"] = None

    logo_path = STATIC_DIR / "dataiku.png"
    inject_custom_header(logo_path, "Invoice & Ticket Reconciliation Agent")

    st.write(
        "This prototype AI agent ingests supplier invoices and discrepancy tickets, "
        "parses them with LLM-based extraction, checks invoice arithmetic, reconciles "
        "against a small SQLite finance database, and can send emails to suppliers "
        "when inconsistencies are detected."
    )

    doc_tab, query_tab = st.tabs(
        ["Document workflow", "Ask about invoices/tickets"]
    )

    with doc_tab:
        render_workflow_tab(DATA_DIR, UPLOAD_DIR)

    with query_tab:
        render_chat_tab()


if __name__ == "__main__":
    main()
