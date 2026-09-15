# Architecture Overview

## System Design

The Lenny Growth Assistant is a full-stack RAG application with an agentic tool-use loop.

## Components

### Backend (FastAPI)
- **Agentic Loop** (`orchestrator.py`): Runs a tool-use loop with up to 5 iterations. For Anthropic, uses native `tool_use` content blocks. For Ollama, parses text-based tool invocations.
- **RAG Layer**: ChromaDB vector store with Ollama `nomic-embed-text` embeddings. Transcripts chunked at ~1,800 chars with 300-char overlap.
- **Skills**: `ship30.py` generates 1,250-word essays; `artifact_gen.py` produces Markdown docs or self-contained HTML.
- **Database**: Async SQLAlchemy with asyncpg driver connecting to Supabase PostgreSQL.

### Frontend (Next.js 14)
- **Split-pane layout**: Chat on left, Artifact preview on right (slides in on artifact event).
- **SSE streaming**: `useChat` hook reads the event stream, accumulating text deltas and handling artifact events.
- **Sandboxed iframes**: HTML artifacts render in `<iframe sandbox="allow-scripts">`.

## Data Flow

```
User message → POST /api/chat/{session_id}
    → load message history from DB
    → run_agent() generator
        → LLM stream (SSE chunks to client)
        → tool_use detected → dispatch_tool()
            → ChromaDB search / essay / artifact
        → final LLM response
    → save assistant message + artifact to DB
```
