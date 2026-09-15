# 🐢 Lenny Growth Assistant

> An AI-powered growth advisor trained on hundreds of episodes from [Lenny's Podcast](https://www.lennyspodcast.com/).

Built as a take-home assignment for Oogway Labs — Forward Deployed Engineer role.

## ✨ Features

- **RAG-powered chat** — answers product/growth questions using real transcript insights
- **Dual LLM** — Anthropic Claude 3.5 Haiku (cloud) or Ollama llama3.1:8b (local)
- **Agentic tool loop** — search_transcripts, generate_ship30_essay, generate_artifact
- **Ship 30 for 30 essays** — ~1,250-word atomic essays with podcast evidence
- **Artifact generation** — Markdown docs and interactive HTML with split-pane preview
- **SSE streaming** — real-time response streaming
- **Persistent sessions** — Supabase (PostgreSQL) via SQLAlchemy async
- **Light/dark mode** — system-aware with manual toggle

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI 0.115, Python 3.11 |
| LLM | Anthropic Claude 3.5 Haiku / Ollama llama3.1:8b |
| Embeddings | nomic-embed-text via Ollama |
| Vector Store | ChromaDB (persistent) |
| Database | Supabase (PostgreSQL) + SQLAlchemy async |
| Frontend | Next.js 14 (App Router) + TypeScript |
| Styling | Tailwind CSS + custom design tokens |
| Font | Geist (400 + 600) |
| Streaming | Server-Sent Events (SSE) |

## 🚀 Quick Start

### Prerequisites
- Docker Desktop
- Ollama with `llama3.1:8b` and `nomic-embed-text` models
- Supabase project (for database)

### 1. Clone and configure

```bash
git clone https://github.com/ADevaHarsha813/lenny-growth-assistant.git
cd lenny-growth-assistant
cp .env.example .env
# Edit .env with your DATABASE_URL and optionally ANTHROPIC_API_KEY
```

### 2. Ingest transcripts

```bash
git clone https://github.com/ChatPRD/lennys-podcast-transcripts data/transcripts
docker compose up backend --build -d
docker compose exec backend python scripts/ingest_transcripts.py
```

### 3. Start the app

```bash
docker compose up --build
```

Open [http://localhost:3000](http://localhost:3000)

## 🔑 Environment Variables

| Variable | Description |
|----------|-------------|
| `LLM_PROVIDER` | `ollama` or `anthropic` |
| `ANTHROPIC_API_KEY` | Claude API key (if using Anthropic) |
| `OLLAMA_BASE_URL` | Ollama endpoint (default: `http://host.docker.internal:11434`) |
| `OLLAMA_MODEL` | Chat model (default: `llama3.1:8b`) |
| `OLLAMA_EMBED_MODEL` | Embedding model (default: `nomic-embed-text`) |
| `DATABASE_URL` | Supabase PostgreSQL connection string |
| `CHROMA_PERSIST_DIR` | ChromaDB storage path |

## 📁 Project Structure

```
lenny-growth-assistant/
├── backend/
│   ├── app/
│   │   ├── agents/          # orchestrator + tools + LLM provider
│   │   ├── api/             # FastAPI routes (sessions, chat, artifacts)
│   │   ├── models/          # SQLAlchemy ORM + Pydantic schemas
│   │   ├── rag/             # ChromaDB chunker + retriever + ingest
│   │   └── skills/          # ship30 + artifact_gen
│   └── scripts/ingest_transcripts.py
├── frontend/
│   ├── app/                 # Next.js App Router pages
│   ├── components/          # React UI components
│   ├── hooks/               # useChat, useSession
│   └── lib/                 # types, api client
├── docker-compose.yml
└── .env.example
```

## 🎯 Architecture

```
User → Next.js → FastAPI → Agentic Loop
                              ↓
                    ┌─────────────────┐
                    │  Tool Dispatch  │
                    ├────────┬────────┤
                    │ Search │ Essay  │ HTML/MD
                    │  RAG   │Ship30  │Artifact
                    └────┬───┴────────┘
                         ↓
                    ChromaDB (vectors)
                    Supabase (messages)
```

## 📺 Demo

[Demo Video](https://youtube.com/...)

---

Built with ❤️ by Deva Harsha Annamreddy for Oogway Labs
