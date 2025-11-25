from pathlib import Path

import streamlit as st

from src.agent.document_agent import DocumentAgent


def save_uploaded_file(uploaded_file, upload_dir: Path) -> Path | None:
    if uploaded_file is None:
        return None
    safe_name = uploaded_file.name.replace(" ", "_")
    file_path = upload_dir / safe_name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def render_workflow_tab(data_dir: Path, upload_dir: Path) -> None:
    st.subheader("Upload document")

    uploaded_file = st.file_uploader(
        "Drop an invoice or ticket PDF here",
        type=["pdf"],
        accept_multiple_files=False,
    )

    with st.expander("Agent settings", expanded=False):
        auto_insert = st.checkbox(
            "Auto-insert new valid invoices into DB", value=True
        )
        default_email_recipient = st.text_input(
            "Default email recipient (for drafted emails)",
            value="ap@acme-analytics.com",
        )
        st.caption(f"Database path: `{data_dir / 'finance.db'}`")

    user_instruction = st.text_area(
        "Optional instruction to the agent",
        placeholder=(
            "e.g. Do not actually send emails, just draft them."
        ),
    )

    run_clicked = st.button(
        "Run agent",
        type="primary",
        disabled=uploaded_file is None,
    )

    if not run_clicked:
        return

    if uploaded_file is None:
        st.warning("Please upload a PDF first.")
        return

    file_path = save_uploaded_file(uploaded_file, upload_dir)
    st.info(f"Uploaded file saved to `{file_path}`")

    agent = DocumentAgent(
        db_path=data_dir / "finance.db",
        auto_insert_new_invoices=auto_insert,
        default_email_recipient=default_email_recipient,
    )

    result = agent.handle_document(
        file_path=file_path,
        user_instruction=user_instruction,
    )

    st.session_state["doc_context"] = {
        "raw_text": result.get("raw_text"),
        "parsed_invoice": result.get("parsed_invoice"),
        "parsed_ticket": result.get("parsed_ticket"),
    }

    st.markdown("### Agent plan")
    st.json(result.get("plan", {}))

    st.markdown("### Detected document type")
    st.write(result.get("doc_type"))

    if result.get("parsed_invoice"):
        st.markdown("### Parsed invoice")
        st.json(result["parsed_invoice"])

    if result.get("parsed_ticket"):
        st.markdown("### Parsed ticket")
        st.json(result["parsed_ticket"])

    if result.get("math_check") is not None:
        st.markdown("### Math check")
        st.json(result["math_check"])

    if result.get("db_invoice") is not None:
        st.markdown("### Matching invoice in DB")
        st.json(result["db_invoice"])

    if result.get("reconciliation"):
        st.markdown("### Reconciliation result")
        st.json(result["reconciliation"])

    if result.get("ticket"):
        st.markdown("### Created ticket")
        st.json(result["ticket"])

    if result.get("email_draft"):
        st.markdown("### Draft email")
        st.code(result["email_draft"], language="markdown")

    if result.get("email_status"):
        st.markdown("### Email send status")
        st.write(result["email_status"])

    with st.expander("Show raw parsed text (first 1000 chars)"):
        raw = result.get("raw_text") or ""
        st.text(raw[:1000])
