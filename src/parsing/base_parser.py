import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from llama_parse import LlamaParse

# env 
load_dotenv()

LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")


def _get_llamaparse() -> LlamaParse:
    """
    Initialize a LlamaParse client.
    """
    if not LLAMA_CLOUD_API_KEY:
        raise RuntimeError(
            "LLAMA_CLOUD_API_KEY is not set. "
            "Add it to your .env file or environment variables."
        )

    parser = LlamaParse(
        api_key=LLAMA_CLOUD_API_KEY,
        result_type="markdown",  # it is better for llm to work with markdown
    )
    return parser


def parse_pdf_to_markdown(file_path: Path) -> str:
    """
    Parse a PDF file with LlamaParse and return concatenated markdown text.

    This is the low-level parser used by invoice_parser and ticket_parser.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    parser = _get_llamaparse()

    # LlamaParse returns a list of Document objects
    documents = parser.load_data([str(file_path)])

    text_chunks: List[str] = [doc.text for doc in documents]
    full_text = "\n\n".join(text_chunks)

    return full_text




