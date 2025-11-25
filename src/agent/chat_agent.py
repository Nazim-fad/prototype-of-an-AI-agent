import json
from typing import Any, Dict, List, Optional, Tuple

from llama_index.core import Document, VectorStoreIndex
from llama_index.core.llms import ChatMessage
from llama_index.embeddings.ollama import OllamaEmbedding

from src.agent.llm_client import get_llm
from src.config.prompts import PLANNER_SYSTEM_PROMPT, PLANNER_USER_PROMPT_TEMPLATE, CHAT_SYSTEM_PROMPT


EMBED_MODEL_NAME: str = "all-minilm"
RAG_TOP_K: int = 4


class DocumentChatAgent:
    """
    Agentic RAG over a single uploaded document (invoice or ticket).

    - Uses a VectorStoreIndex with local Ollama embeddings (all-minilm).
    - Planning step decides:
        - 'structured_fields': use parsed JSON fields,
        - 'rag_over_text': use semantic search over the document.
    """

    def __init__(
        self,
        raw_text: str,
        parsed_invoice: Optional[Dict[str, Any]] = None,
        parsed_ticket: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.llm = get_llm()
        self.raw_text = raw_text or ""
        self.parsed_invoice = parsed_invoice
        self.parsed_ticket = parsed_ticket

        # Embeddings: local via Ollama 
        # Make sure you ran: `ollama pull all-minilm`
        self.embed_model = OllamaEmbedding(model_name=EMBED_MODEL_NAME)

        # Build a vector index over the document (or disable RAG if no text)
        self.index: Optional[VectorStoreIndex] = None
        if self.raw_text.strip():
            docs = [Document(text=self.raw_text)]
            self.index = VectorStoreIndex.from_documents(
                docs,
                embed_model=self.embed_model,
            )

   
    # Planner

    def _plan(self, question: str) -> Dict[str, Any]:
        """
        Decide which tools to use for this question:
          - structured_fields
          - rag_over_text
        """
        system_msg = ChatMessage(
            role="system",
            content=PLANNER_SYSTEM_PROMPT,
        )

        flags = {
            "has_parsed_invoice": self.parsed_invoice is not None,
            "has_parsed_ticket": self.parsed_ticket is not None,
            "has_index": self.index is not None,
        }

        user_msg = ChatMessage(
            role="user",
            content=PLANNER_USER_PROMPT_TEMPLATE.format(
                question=question,
                flags_json=json.dumps(flags, indent=2),
            ),
        )

        resp = self.llm.chat([system_msg, user_msg])
        raw = resp.message.content

        try:
            plan = json.loads(raw)
        except Exception:
            # Fallback: at least use RAG if we have an index
            if self.index is not None:
                plan = {"actions": ["rag_over_text"]}
            else:
                plan = {"actions": ["structured_fields"]}

        actions = plan.get("actions") or []
        if not actions:
            # Default choice if LLM returns an empty list
            actions = ["rag_over_text"] if self.index is not None else ["structured_fields"]
        plan["actions"] = actions
        return plan


    # Main method


    def chat(
        self,
        question: str,
        history: Optional[List[Tuple[str, str]]] = None,
    ) -> str:
        """
        Answer a natural-language question about the current document.

        `history` is a list of (user_question, agent_answer) tuples representing
        the past conversation turns.
        """
        plan = self._plan(question)
        actions = plan["actions"]

        # Structured context from parsed invoice/ticket
        structured_context = ""
        if "structured_fields" in actions:
            ctx: Dict[str, Any] = {}
            if self.parsed_invoice:
                ctx["parsed_invoice"] = self.parsed_invoice
            if self.parsed_ticket:
                ctx["parsed_ticket"] = self.parsed_ticket
            if ctx:
                structured_context = json.dumps(ctx, indent=2)

        # RAG context from the document text using embeddings (retrieved chunks)
        rag_context = ""
        if "rag_over_text" in actions and self.index is not None and self.raw_text:
            retriever = self.index.as_retriever(similarity_top_k=RAG_TOP_K)
            nodes = retriever.retrieve(question)
            # Concatenate the most relevant chunks
            rag_context = "\n\n-----\n\n".join(
                n.get_content(metadata_mode="all") for n in nodes
            )

        # Conversation history (for multi-turn chat)
        history_text = ""
        if history:
            lines: List[str] = []
            for i, (q_prev, a_prev) in enumerate(history, start=1):
                lines.append(f"Turn {i} - User: {q_prev}")
                lines.append(f"Turn {i} - Agent: {a_prev}")
            history_text = "\n".join(lines)

        # Final answer using both the structured context and RAG context
        system_msg = ChatMessage(
            role="system",
            content=CHAT_SYSTEM_PROMPT,
        )

        user_msg = ChatMessage(
            role="user",
            content=(
                f"Previous conversation (may be empty):\n{history_text}\n\n"
                f"New user question:\n{question}\n\n"
                f"Structured JSON (may be empty):\n{structured_context}\n\n"
                f"RAG context (from semantic search over the document, may be empty):\n{rag_context}"
            ),
        )

        final = self.llm.chat([system_msg, user_msg])
        return str(final.message.content)
