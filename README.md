# Research Agent

Terminal-first AI research assistant scaffold with a Gemini-backed chat layer.

## Current behavior

- Accept a user query in the terminal
- Enhance the query
- Run starter tool stubs
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

- `GEMINI_API_KEY`: required for Gemini responses
- `GEMINI_MODEL`: optional, defaults to `gemini-2.0-flash`
- `RESEARCH_AGENT_DATA_DIR`: optional runtime artifact directory
- `RESEARCH_AGENT_LOG_DIR`: optional log directory
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

Optional model override:

```powershell
$env:GEMINI_MODEL="gemini-2.0-flash"
```

## Run

```powershell
research-agent
```
