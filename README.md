# 🌱 The Lenny Growth Assistant

> AI-powered conversational assistant grounded in Lenny's Podcast transcripts. Ask product and growth questions, generate Ship 30 for 30 essays, and create rendered Markdown/HTML artifacts — all from a single clean interface.

## Quick Start

```bash
# 1. Clone
git clone https://github.com/ADevaHarsha813/lenny-growth-assistant
cd lenny-growth-assistant

# 2. Set up environment
cp .env.example .env
# Edit .env — add your DATABASE_URL and LLM config

# 3. Start Ollama (required for local demo)
ollama pull llama3.1:8b
ollama pull nomic-embed-text

# 4. Run (requires Docker Desktop)
docker compose up --build

# 5. Open
# Frontend: http://localhost:3000
# API docs: http://localhost:8000/docs
# Health:   http://localhost:8000/health
```

## Architecture

- **Frontend:** Next.js 14 (App Router) + Tailwind CSS + shadcn/ui
- **Backend:** FastAPI (Python 3.11) + SQLAlchemy async
- **Database:** Supabase (PostgreSQL)
- **Vector Store:** ChromaDB (in-process)
- **LLM:** Anthropic Claude (cloud) or Ollama (local)
- **Agent:** Anthropic `tool_use` agentic loop (3 tools)

See [docs/architecture.md](docs/architecture.md) for full details.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LLM_PROVIDER` | Yes | `anthropic` or `ollama` |
| `ANTHROPIC_API_KEY` | If cloud | Your Anthropic API key |
| `OLLAMA_MODEL` | If local | Default: `llama3.1:8b` |
| `DATABASE_URL` | Yes | Supabase PostgreSQL connection string |

See [.env.example](.env.example) for all variables.

## Documentation

- [PRD](docs/PRD.md) — Product requirements and discovery brief
- [Architecture](docs/architecture.md) — System design and API reference
- [Design](docs/design.md) — UI/UX decisions and interaction model
- [Agent Transcripts](agent-transcripts/) — AI-assisted coding session logs
