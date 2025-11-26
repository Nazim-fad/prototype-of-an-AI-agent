import streamlit as st

from src.agent.chat_agent import DocumentChatAgent


def render_chat_tab() -> None:
    st.subheader("Ask questions about invoices / tickets")

    doc_ctx = st.session_state.get("doc_context")

    if not doc_ctx or not doc_ctx.get("raw_text"):
        st.info(
            "First upload a document and run the agent in the "
            "'Document workflow' tab. Then you can chat with that document here."
        )
        return

    question = st.text_input(
        "Ask a question about the last processed document",
        placeholder="For example: 'What is the total amount and due date?'",
    )

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    if (
        "chat_agent" not in st.session_state
        or st.session_state.get("chat_agent_doc_id") != hash(doc_ctx["raw_text"])
    ):
        # Create new chat agent for this document
        # The agent maintains conversation history internally
        st.session_state["chat_agent"] = DocumentChatAgent(
            raw_text=doc_ctx["raw_text"],
            parsed_invoice=doc_ctx.get("parsed_invoice"),
            parsed_ticket=doc_ctx.get("parsed_ticket"),
        )
        st.session_state["chat_agent_doc_id"] = hash(doc_ctx["raw_text"])
        st.session_state["chat_history"] = []  # Reset history for new document

    if st.button("Ask", key="ask_button") and question.strip():
        agent_chat = st.session_state["chat_agent"]
        # The agent handles conversation history internally
        answer = agent_chat.chat(question)
        st.session_state["chat_history"].append((question, answer))

    for q, a in st.session_state.get("chat_history", []):
        st.markdown(f"**You:** {q}")
        st.markdown(f"**Agent:** {a}")
        st.markdown("---")