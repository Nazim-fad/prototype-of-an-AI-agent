# Invoice & Ticket Reconciliation Agent

An AI-powered agent that processes invoices and support tickets using local LLMs (Ollama) and LlamaParse.

## What it does

- **Parse PDFs** → Converts invoices/tickets to structured data using LlamaParse
- **Classify documents** → Detects whether input is invoice or ticket
- **Validate invoices** → Checks math (total = sum + tax)
- **Reconcile with DB** → Compares parsed data against SQLite database
- **Create tickets** → Auto-generates discrepancy tickets when DB values don't match
- **Draft emails** → Composes responses for issues found
- **Chat interface** → Ask questions about uploaded documents via Streamlit UI

## Quick Start

### Prerequisites

```bash
ollama pull qwen2.5:0.5b
ollama pull all-minilm
```

### Setup

```bash
conda create -n dataiku
conda activate dataiku
pip install -r requirements.txt
python src/db/init_db.py
```

### Run

```bash
conda activate dataiku
 python -m streamlit run streamlit_app.py
```

## Architecture

```
src/
├── parsing/       # PDF→text, classification, extraction
├── db/            # SQLite client & schema
├── agent/         # DocumentAgent (workflows), ChatAgent (RAG)
├── tools/         # LLM tools (parse, validate, reconcile, email)
└── tests/         # Basic parsing tests
```

## Tech Stack

- **LLM**: Ollama (local Qwen)
- **Embeddings**: all-minilm (local)
- **PDF parsing**: LlamaParse
- **Framework**: LlamaIndex, Streamlit
- **DB**: SQLite
- **Schema validation**: Pydantic

## Key Files

- `streamlit_app.py` — UI entry point
- `src/agent/document_agent.py` — Main workflow orchestrator
- `src/tools/` — LLM tools (parse, validate, reconcile)
- `src/db/schema.sql` — Invoice & ticket tables
