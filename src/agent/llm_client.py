from llama_index.llms.ollama import Ollama
import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "config.yaml"

with open(CONFIG_PATH) as f:
    _config = yaml.safe_load(f)

LLM_MODEL = _config["llm"]["model"]
LLM_REQUEST_TIMEOUT = _config["llm"]["request_timeout"]

def get_llm() -> Ollama:
    """
    Returns a local Ollama LLM instance.
    """
    return Ollama(
        model=LLM_MODEL,
        timeout=LLM_REQUEST_TIMEOUT,
    )
