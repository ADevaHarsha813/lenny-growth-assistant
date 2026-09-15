# Architecture Overview
## The Lenny Growth Assistant

**Version:** 1.0  
**Author:** Deva Harsha Annamreddy  
**Date:** September 2026

---

## 1. System Topology

```
┌─────────────────────────────────────────────────────────────┐
│                        Docker Compose                        │
│                                                              │
│  ┌──────────────┐        ┌──────────────────────────────┐   │
│  │   Frontend   │        │          Backend              │   │
│  │  Next.js 14  │◄─SSE──►│  FastAPI + Agentic Loop      │   │
│  │  Port: 3000  │        │  Port: 8000                  │   │
│  └──────────────┘        └──────┬───────────────┬───────┘   │
│                                 │               │            │
│                    ┌────────────▼──┐   ┌────────▼────────┐  │
│                    │  ChromaDB     │   │   Supabase DB   │  │
│                    │  (vectors)    │   │  (PostgreSQL)   │  │
│                    │  Local volume │   │  Cloud-hosted   │  │
│                    └───────────────┘   └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
           │                                    │
    ┌──────▼──────┐                    ┌────────▼──────┐
    │  Ollama     │                    │  Anthropic    │
    │  (local)    │                    │  API (cloud)  │
    │  llama3.1   │                    │  Claude Haiku │
    └─────────────┘                    └───────────────┘
```

---

## 2. Database Schema

All tables stored in Supabase PostgreSQL. SQLAlchemy async ORM with asyncpg driver.

### 2.1 `sessions` table

```sql
CREATE TABLE sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title       VARCHAR(200),
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2.2 `messages` table

```sql
CREATE TABLE messages (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role        VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content     TEXT NOT NULL,
    sources     JSONB,          -- array of {episode_title, source_file, score}
    skill       VARCHAR(50),    -- 'ship30' | 'artifact_markdown' | 'artifact_html' | NULL
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_messages_session ON messages(session_id, created_at);
```

### 2.3 `artifacts` table

```sql
CREATE TABLE artifacts (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id  UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    message_id  UUID REFERENCES messages(id),
    type        VARCHAR(20) NOT NULL CHECK (type IN ('markdown', 'html')),
    title       VARCHAR(200),
    content     TEXT NOT NULL,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_artifacts_session ON artifacts(session_id);
```

---

## 3. API Endpoints

Base URL: `http://localhost:8000`

### 3.1 Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Returns `{"status": "ok", "provider": "anthropic\|ollama"}` |

### 3.2 Sessions

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/sessions` | List all sessions (id, title, created_at, updated_at) |
| `POST` | `/api/sessions` | Create new session `{title?: string}` → `{id, title, created_at}` |
| `GET` | `/api/sessions/{id}` | Get session with full message history |
| `PATCH` | `/api/sessions/{id}` | Update session title `{title: string}` |
| `DELETE` | `/api/sessions/{id}` | Delete session and all messages |

### 3.3 Chat

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/chat/{session_id}` | Send message, returns SSE stream |
| `DELETE` | `/api/chat/{session_id}/messages` | Clear message history for session |

**Request body** (`POST /api/chat/{session_id}`):
```json
{
  "message": "What's the best PLG strategy for B2B SaaS?",
  "skill": "ship30 | artifact_markdown | artifact_html | null"
}
```

**SSE Event types:**
```
event: text_delta    → {"delta": "string"}
event: artifact      → {"type": "html|markdown", "title": "...", "content": "..."}
event: sources       → [{"episode_title": "...", "source_file": "...", "score": 0.87}]
event: done          → {"message_id": "uuid"}
event: error         → {"detail": "string"}
```

### 3.4 Artifacts

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/artifacts/{session_id}` | List artifacts for a session |
| `GET` | `/api/artifacts/{session_id}/{artifact_id}` | Get single artifact content |

---

## 4. Component Boundaries

### 4.1 Backend

```
backend/app/
├── main.py              # FastAPI app factory, CORS, lifespan
├── database.py          # SQLAlchemy async engine, session factory
├── models/
│   ├── db.py            # ORM models: Session, Message, Artifact
│   └── schemas.py       # Pydantic request/response schemas
├── api/
│   ├── sessions.py      # Session CRUD endpoints
│   ├── chat.py          # SSE streaming chat endpoint
│   └── artifacts.py     # Artifact retrieval endpoints
├── agents/
│   ├── orchestrator.py  # Agentic loop: tool dispatch + LLM streaming
│   ├── tools.py         # Tool definitions: search, essay, artifact
│   └── provider.py      # LLM abstraction: AnthropicProvider / OllamaProvider
├── rag/
│   └── retriever.py     # ChromaDB query + chunk metadata
└── skills/
    ├── ship30.py        # Ship 30 for 30 essay generation
    └── artifact_gen.py  # HTML/Markdown artifact generation
```

### 4.2 Frontend

```
frontend/
├── app/
│   ├── layout.tsx       # Root layout: fonts, metadata
│   └── page.tsx         # App shell: sidebar + chat + artifact pane
├── components/
│   ├── layout/
│   │   └── SessionSidebar.tsx   # Session list, new chat, search
│   ├── chat/
│   │   ├── ChatPanel.tsx        # Message list, scroll, streaming display
│   │   ├── ChatInput.tsx        # Composer: textarea, send, format picker
│   │   ├── WelcomeScreen.tsx    # Initial state with turtle + composer
│   │   └── MessageBubble.tsx    # Single message with action bar
│   └── artifact/
│       ├── ArtifactPane.tsx     # Split-pane container + tab bar
│       ├── SandboxedFrame.tsx   # Sandboxed iframe for HTML artifacts
│       └── MarkdownViewer.tsx   # react-markdown renderer
├── hooks/
│   ├── useChat.ts        # SSE stream management, message state
│   └── useSession.ts     # Session CRUD, active session state
└── lib/
    ├── api.ts            # Typed fetch wrappers for all endpoints
    └── types.ts          # Shared TypeScript interfaces
```

---

## 5. Ingestion and Retrieval Flow

### 5.1 Ingestion (one-time batch)

```
scripts/ingest_transcripts.py
  1. Clone ChatPRD/lennys-podcast-transcripts to data/transcripts/
  2. Walk all .txt / .md files
  3. For each file:
     a. Read raw text
     b. Chunk at ~1,800 chars with 300-char overlap (sliding window)
     c. Embed each chunk via Ollama nomic-embed-text
     d. Store in ChromaDB with metadata:
        {source_file, episode_title, chunk_index}
  4. Log total chunks ingested
```

### 5.2 Retrieval (per query)

```
retriever.py → query(text, n_results=5)
  1. Embed query text via nomic-embed-text
  2. ChromaDB cosine similarity search
  3. Return top-5 chunks with:
     {content, episode_title, source_file, distance_score}
  4. Chunks passed to LLM in system prompt as grounding context
```

### 5.3 Grounding prompt strategy

```
System prompt:
  "You are the Lenny Growth Assistant. Answer ONLY using the provided
   transcript excerpts. If the excerpts do not contain relevant
   information, say so clearly. Cite the episode title in your answer."

Context injection:
  "Here are the relevant transcript excerpts:\n
   [EXCERPT 1 — {episode_title}]\n{content}\n
   [EXCERPT 2 — {episode_title}]\n{content}\n..."
```

---

## 6. Agent Routing

The orchestrator runs a tool-use loop (max 5 iterations):

```
User message + skill hint
         ↓
  Determine tools to offer:
    - Always available: search_transcripts
    - If skill == "ship30":         add generate_ship30_essay
    - If skill in ["html","markdown"]: add generate_artifact
         ↓
  LLM decides which tool to call
         ↓
  Tool dispatch:
    search_transcripts   → retriever.query()
    generate_ship30_essay → ship30.generate()
    generate_artifact    → artifact_gen.generate()
         ↓
  Tool result injected back into conversation
         ↓
  LLM produces final response (streamed via SSE)
         ↓
  If artifact in response → emit SSE "artifact" event
  Sources extracted → emit SSE "sources" event
```

---

## 7. Model Toggle

Controlled by `LLM_PROVIDER` environment variable:

```python
# provider.py
if settings.LLM_PROVIDER == "anthropic":
    provider = AnthropicProvider(
        model="claude-3-5-haiku-20241022",
        api_key=settings.ANTHROPIC_API_KEY
    )
elif settings.LLM_PROVIDER == "ollama":
    provider = OllamaProvider(
        base_url=settings.OLLAMA_BASE_URL,   # http://host.docker.internal:11434
        model=settings.OLLAMA_MODEL          # llama3.1:8b
    )
```

Both providers implement the same async interface:
```python
async def stream(messages, tools) -> AsyncGenerator[str, None]
```

**Fallback behaviour:** If Anthropic API key is missing and provider is set to `anthropic`, startup logs a warning and the chat endpoint returns a 503 with `{"detail": "LLM provider not configured"}`.

---

## 8. Security

### 8.1 HTML Artifact Sandboxing

All user-facing HTML artifacts are rendered inside:
```html
<iframe
  sandbox="allow-scripts"
  srcdoc="{html_content}"
  style="border:none; width:100%; height:100%;"
/>
```

**What `sandbox="allow-scripts"` allows:**
- JavaScript execution inside the iframe

**What it blocks (no additional sandbox flags):**
- `allow-same-origin` — iframe has null origin, cannot access parent DOM, cookies, or localStorage
- `allow-forms` — no form submission to external URLs
- `allow-top-navigation` — cannot redirect the parent page
- `allow-popups` — cannot open new windows/tabs

**Why:** Generated HTML is LLM output and inherently untrusted. Without `allow-same-origin`, even if the generated script calls `window.parent.document`, the browser throws a cross-origin error. This provides defence-in-depth against prompt injection attacks that attempt to exfiltrate session data.

### 8.2 API Security

- CORS configured to allow only `http://localhost:3000` in production Docker setup
- No authentication in v1 (internal tool assumption — see PRD scope)
- Secrets managed via `.env` file; `.env.example` committed, never the real `.env`
- `DATABASE_URL` contains credentials — never logged

### 8.3 Input Validation

- All request bodies validated by Pydantic schemas
- `message` field: max 4,000 characters
- `skill` field: enum-validated, rejects unknown values
- SQL injection: not possible via SQLAlchemy ORM parameterised queries

---

## 9. Observability

### 9.1 Structured Logging

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
```

Key log events:
- `[STARTUP]` LLM provider loaded, ChromaDB connected, DB connected
- `[CHAT]` session_id, message length, skill, provider
- `[RETRIEVAL]` query, n_results, top score
- `[TOOL]` tool name, duration_ms
- `[ARTIFACT]` type, title, content length
- `[ERROR]` exception type, endpoint, session_id

### 9.2 Health Endpoint

`GET /health` returns:
```json
{
  "status": "ok",
  "provider": "anthropic",
  "chroma_collections": 1,
  "chroma_count": 12847,
  "db": "connected"
}
```

---

## 10. Deployment

### 10.1 Docker Compose Services

```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment: [from .env]
    volumes: [chroma_data:/app/chroma_db]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]
```

### 10.2 Prerequisites on Host Machine

- Docker Desktop (Mac/Windows) or Docker Engine (Linux)
- Ollama with `llama3.1:8b` and `nomic-embed-text` (for local LLM mode)
- Supabase project with connection string

### 10.3 Environment Variables

See `.env.example` in the repository root. Required variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | ✅ | Supabase PostgreSQL connection string |
| `LLM_PROVIDER` | ✅ | `anthropic` or `ollama` |
| `ANTHROPIC_API_KEY` | If provider=anthropic | Claude API key |
| `OLLAMA_BASE_URL` | If provider=ollama | Default: `http://host.docker.internal:11434` |
| `OLLAMA_MODEL` | No | Default: `llama3.1:8b` |
| `OLLAMA_EMBED_MODEL` | No | Default: `nomic-embed-text` |
| `CHROMA_PERSIST_DIR` | No | Default: `/app/chroma_db` |
