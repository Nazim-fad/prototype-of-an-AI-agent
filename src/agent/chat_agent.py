import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

from smolagents import CodeAgent, InferenceClientModel
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex

from src.tools.chat_tools import create_structured_fields_tool, create_rag_search_tool
from src.config.prompts import CHAT_AGENT_SYSTEM_INSTRUCTIONS

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

HF_TOKEN = os.getenv("HF_TOKEN")

# Load configuration
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"
with open(CONFIG_PATH) as f:
    _config = yaml.safe_load(f)

CHAT_MODEL_ID = _config["chat_agent"]["model_id"]
CHAT_TEMPERATURE = _config["chat_agent"]["temperature"]


class DocumentChatAgent:
    """
    agentic RAG over a single uploaded document (invoice or ticket).

    Uses smolagents CodeAgent with tools to:
    - retrieve structured fields from parsed invoice/ticket
    - perform semantic search (RAG) over the document text
    - maintain conversation history
    - answer natural-language questions autonomously
    """

    def __init__(
        self,
        raw_text: str,
        parsed_invoice: Optional[Dict[str, Any]] = None,
        parsed_ticket: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.raw_text = raw_text or ""
        self.parsed_invoice = parsed_invoice
        self.parsed_ticket = parsed_ticket
        self.conversation_history: list = []

        # Build vector index for RAG 
        self.index: Optional[VectorStoreIndex] = None

        # Create tools for the agent
        structured_fields_tool = create_structured_fields_tool(
            parsed_invoice=parsed_invoice,
            parsed_ticket=parsed_ticket,
        )

        rag_search_tool, self.index = create_rag_search_tool(
            raw_text=self.raw_text,
        )

        # Initialize the LLM model
        self.model = InferenceClientModel(
            model_id=CHAT_MODEL_ID,
            token=HF_TOKEN,
            temperature=CHAT_TEMPERATURE,
        )

        # Create the CodeAgent with the tools
        self.agent = CodeAgent(
            tools=[structured_fields_tool, rag_search_tool],
            model=self.model,
            instructions=CHAT_AGENT_SYSTEM_INSTRUCTIONS,
            add_base_tools=True,
            max_steps=5,
        )

    def chat(
        self,
        question: str,
    ) -> str:
        """
        Answer a natural-language question about the current document.
        The LLM agent decides which tools to use autonomously.
        
        Args:
            question: User's question about the document
            
        Returns:
            Agent's response
        """
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": question})

        # Build task with conversation context
        history_text = ""
        if len(self.conversation_history) > 1:
            lines = []
            for i, msg in enumerate(self.conversation_history[:-1], start=1):
                if msg["role"] == "user":
                    lines.append(f"Turn {i} - User: {msg['content']}")
                else:
                    lines.append(f"Turn {i} - Assistant: {msg['content']}")
            history_text = "\n".join(lines) + "\n\n"

        task = (
            f"{history_text}"
            f"Current question: {question}\n\n"
            f"Use the available tools to find relevant information and answer the question."
        )

        # Run the agent
        raw_result = self.agent.run(task)
        answer = str(raw_result) if raw_result else "I couldn't generate an answer."

        # Add to conversation history
        self.conversation_history.append({"role": "assistant", "content": answer})

        return answer
