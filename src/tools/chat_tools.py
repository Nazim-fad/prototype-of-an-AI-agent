import json
from typing import Any, Dict, Optional

from smolagents import tool
from llama_index.core import Document, VectorStoreIndex
from llama_index.embeddings.ollama import OllamaEmbedding


RAG_TOP_K: int = 4


def create_structured_fields_tool(
    parsed_invoice: Optional[Dict[str, Any]] = None,
    parsed_ticket: Optional[Dict[str, Any]] = None,
) -> tool:
    """
    Create a tool to retrieve structured parsed fields from the document.

    Args:
        parsed_invoice: Parsed invoice data (if available)
        parsed_ticket: Parsed ticket data (if available)

    Returns:
        A smolagents tool function
    """

    @tool
    def get_structured_fields() -> str:
        """
        Retrieve parsed structured fields from the document.
        Returns invoice or ticket fields as JSON.
        """
        ctx: Dict[str, Any] = {}
        if parsed_invoice:
            ctx["parsed_invoice"] = parsed_invoice
        if parsed_ticket:
            ctx["parsed_ticket"] = parsed_ticket

        if not ctx:
            return "No structured data available."

        return json.dumps(ctx, indent=2)

    return get_structured_fields


def create_rag_search_tool(
    raw_text: str,
    embed_model_name: str = "all-minilm",
    top_k: int = RAG_TOP_K,
) -> tuple[tool, Optional[VectorStoreIndex]]:
    """
    Create a tool to perform semantic search over document text.

    Args:
        raw_text: The document text to index
        embed_model_name: Name of the embedding model (default: all-minilm)
        top_k: Number of top results to return (default: 4)

    Returns:
        A tuple of (tool function, vector_index or None if text is empty)
    """
    # Build index if we have text
    index: Optional[VectorStoreIndex] = None
    if raw_text and raw_text.strip():
        embed_model = OllamaEmbedding(model_name=embed_model_name)
        docs = [Document(text=raw_text)]
        index = VectorStoreIndex.from_documents(
            docs,
            embed_model=embed_model,
        )

    @tool
    def search_document(query: str) -> str:
        """
        Search the document text semantically for relevant chunks.
        Use this to find specific information in the document.

        Args:
            query: The search query
        """
        if index is None or not raw_text:
            return "Document text is not available for search."

        retriever = index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(query)

        if not nodes:
            return f"No relevant sections found for: {query}"

        # Concatenate the most relevant chunks
        context = "\n\n-----\n\n".join(
            n.get_content(metadata_mode="all") for n in nodes
        )
        return f"Found relevant sections:\n\n{context}"

    return search_document, index
