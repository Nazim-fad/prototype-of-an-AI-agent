# Invoice & Ticket Reconciliation Agent

An AI-powered agent that processes invoices and support tickets using LLMs.

## What it does

- **Autonomous Document Processing** → Parses invoices/tickets to structured data, validates math, reconciles with database
- **Math Validation** → Checks invoice arithmetic 
- **Database Reconciliation** → Compares parsed data against SQLite database, flags discrepancies
- **Auto Ticket Creation** → Generates discrepancy tickets when amounts don't match
- **Email Generation** → Drafts responses to suppliers and sends via Gmail
- **Interactive Chat** → Ask follow-up questions about uploaded documents with RAG-powered semantic search

You can find a better description in the presentation slides.

## Quick Start

### Prerequisites

```bash
ollama pull qwen2.5:0.5b
ollama pull all-minilm
```

### Setup

```bash
pip install -r requirements.txt
python src/db/init_db.py
```

### Run

```bash
streamlit run streamlit_app.py
```

The app opens two tabs:
1. **Document workflow** — Upload a PDF and run the agent end-to-end
2. **Ask about invoices/tickets** — Chat interface for follow-up questions

## Architecture

The project uses two complementary agents powered by `smolagents.CodeAgent`:

### SmolDocumentAgent

Autonomous end-to-end workflow that:

1. Parses PDF into structured invoice/ticket data
2. Validates invoice math
3. Reconciles against SQLite database
4. Creates discrepancy tickets if amounts mismatch
5. Drafts/sends emails to suppliers
6. Returns structured summary

Uses 8 specialized tools and runs with `max_steps=20`.

### DocumentChatAgent

Interactive agent for follow-up questions that:

1. Performs RAG
2. Accesses structured invoice/ticket fields
3. Returns natural language answers


### Project Structure

```text
src/
├── agent/
│   ├── smol_document_agent.py    # document workflow
│   ├── chat_agent.py             
│   └── llm_client.py             # OLLama
├── tools/                        # agent tools : extraction + math validation + DB comparison + Email + Database op       
├── parsing/                      # parsing scripts for Invoice + Ticket and a Doc type detection script
├── db/                           # files to init the db and an SQLite wrapper      
├── config/                       # System/user prompts and LLM & chat agent config (model name ...)
├── ui/                           # UI files 
└── tests/
    └── test_parsing.py           # Parsing unit tests
```

## Tech Stack

- **Agent Framework**: `smolagents` (CodeAgent) with HuggingFace InferenceClient
- **LLM**: meta-llama/Meta-Llama-3.1-70B-Instruct (HuggingFace) and Qwen2.5 0.5B (Ollama, local) 
- **Embeddings**: all-minilm (Ollama, local)
- **Vector Search**: LlamaIndex with VectorStoreIndex
- **PDF Parsing**: LlamaParse (commercial) for high-quality extraction
- **UI**: Streamlit
- **Database**: SQLite
- **Configuration**: YAML + Python

## Key Files

- `streamlit_app.py` — UI entry point with tab routing
- `src/agent/smol_document_agent.py` — Autonomous workflow orchestrator
- `src/agent/chat_agent.py` — Interactive agent with RAG
- `src/tools/chat_tools.py` — Tool factory functions
- `src/config/config.yaml` — Centralized LLM configuration
- `src/config/prompts.py` — System instructions and extraction prompts
- `src/db/schema.sql` — Database schema for invoices and tickets
