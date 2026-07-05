# Research Agent

Terminal-first AI research assistant scaffold with a Gemini-backed chat layer.

## Current behavior

- Accept a user query in the terminal
- Enhance the query
- Run starter tool stubs
- Run in-memory vector search over local PDFs when documents are available
- Build a cumulative report from tool outputs
- Evaluate the report
- Use Gemini to turn the current conversation, report, and evaluation into a chatbot response
- Save the conversation and run artifacts to local text files
- Save step-by-step execution logs to local text files

## Runtime files

- `runtime_data/sessions/<session_id>/conversation.txt`
- `runtime_data/sessions/<session_id>/research_runs.txt`
- `runtime_data/sessions/<session_id>/tool_calls.txt`
- `runtime_data/sessions/<session_id>/reports.txt`
- `runtime_data/sessions/<session_id>/evaluations.txt`
- `runtime_logs/execution_log.txt`
- `runtime_logs/session_<session_id>.txt`

## Environment variables

- `OPEN_ROUTER_API`: required for chat responses and document embeddings through OpenRouter
- `OPEN_ROUTER_MODEL`: optional, defaults to `nvidia/nemotron-3-ultra-550b-a55b:free`
- `EMBEDDING_MODEL`: optional, defaults to `openai/text-embedding-3-small`
- `RESEARCH_AGENT_DATA_DIR`: optional runtime artifact directory
- `RESEARCH_AGENT_LOG_DIR`: optional log directory
- `VECTOR_SEARCH_DOCUMENTS_DIR`: local PDF folder for ingestion
- `VECTOR_SEARCH_CACHE_DIR`: local cache for parsed chunks and embeddings
- `VECTOR_SEARCH_CHUNK_SIZE`: chunk size in characters
- `VECTOR_SEARCH_CHUNK_OVERLAP`: overlap in characters
- `VECTOR_SEARCH_TOP_K`: number of retrieved chunks to return
- `RESEARCH_AGENT_SYSTEM_PROMPT`: optional system prompt override

## Setup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
```

Set your Gemini API key in PowerShell:

```powershell
$env:GEMINI_API_KEY="your-api-key"
```

Optional chat model override:

```powershell
$env:OPEN_ROUTER_MODEL="nvidia/nemotron-3-ultra-550b-a55b:free"
```

Put PDFs you want indexed inside the configured `documents` folder before running the app.

## Run

```powershell
research-agent
```
