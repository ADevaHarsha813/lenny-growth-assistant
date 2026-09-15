# Product Requirements Document
## The Lenny Growth Assistant

**Version:** 1.0  
**Author:** Deva Harsha Annamreddy  
**Date:** September 2026  
**Role:** Forward Deployed Engineer Take-Home Assignment

---

## 1. Discovery Brief

### 1.1 User and Problem

**Primary User:** Product managers, growth leads, and founders at early-to-mid-stage startups who regularly listen to Lenny's Podcast for growth and product strategy insights.

**Job to be done:** "When I face a growth or product challenge, I want to instantly query everything Lenny has ever discussed — without rewatching dozens of hours of podcast episodes — so I can get a grounded, specific answer I can act on today."

**Pain removed:**
- Manually scrubbing through 500+ hours of podcast audio to find a relevant insight
- Losing context switching between episodes, notes, and Notion docs
- Getting generic AI answers not grounded in Lenny's actual frameworks and guest conversations
- Spending hours writing Ship 30-style essays to share learnings with their team

---

### 1.2 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Answer grounding rate | ≥ 90% of responses cite at least one transcript source | Source chip appears on response |
| Session completion rate | ≥ 70% of sessions contain ≥ 3 turns | DB session analytics |
| Ship 30 essay generation | Essay produced in < 15 seconds | Backend latency logging |
| Artifact render success | ≥ 95% of generated HTML artifacts render without error | Frontend error boundary tracking |
| Ollama local demo success | Assistant responds within 30s on local model | Response time logging |

---

### 1.3 Assumptions

1. **Transcripts are sufficient ground truth.** Lenny's podcast transcripts are representative of his views and the advice of his guests. We do not need the audio or video.
2. **Users are English-speaking professionals.** No multi-language support required in v1.
3. **Single-tenant deployment.** This is an internal tool, not a public SaaS. Authentication and multi-user isolation are out of scope for v1.
4. **Supabase free tier is sufficient.** For the evaluation demo, row counts and connection limits on the free tier are acceptable.
5. **Ollama runs on the evaluator's machine.** The evaluator has Ollama installed with `llama3.1:8b` and `nomic-embed-text` models available.
6. **Transcripts are already cleaned text.** The ingestion pipeline does not need to handle audio transcription — the ChatPRD transcript repository is the source of truth.
7. **No real-time indexing needed.** Transcripts are ingested once as a batch; incremental ingestion is a future enhancement.

---

### 1.4 Scope

**In scope (v1):**
- RAG-powered conversational assistant answering product and growth questions
- Grounded answers citing Lenny's podcast episode sources
- Ship 30 for 30 essay generation skill
- Markdown and HTML artifact generation with in-app split-pane viewer
- Session persistence (multiple independent conversations)
- Dual LLM support: Anthropic Claude (cloud) and Ollama (local)
- Docker Compose one-command deployment
- Streaming responses via SSE

**Intentionally excluded (v1):**
- User authentication and multi-user accounts
- Real-time transcript ingestion / webhook updates
- Audio or video playback
- Mobile native app
- Semantic search UI (outside chat)
- Rate limiting and billing
- Episode browsing / library view
- Feedback loop to improve retrieval quality

**Why excluded:** Each excluded item adds significant complexity (auth, infra, mobile frameworks) with marginal value for the evaluation use case. The goal is depth over breadth — a working, polished, defensible product that a small team could actually use today.

---

### 1.5 Risks and Trade-offs

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Hallucination** — LLM invents transcript content | High | RAG system grounds every answer; prompt instructs model to say "the transcripts don't cover this" when no relevant chunks are found |
| **Retrieval quality** — wrong chunks returned | High | ChromaDB cosine similarity with `nomic-embed-text`; top-5 chunks per query; source shown to user for verification |
| **Local model quality** — Ollama answers are weaker | Medium | Clearly documented in README; Anthropic Claude is the recommended provider; Ollama serves the demo requirement |
| **Latency on local model** — llama3.1:8b is slow | Medium | SSE streaming masks latency with incremental output; user sees tokens immediately |
| **Unsafe artifact rendering** — XSS via generated HTML | High | All HTML artifacts rendered in sandboxed iframe with `sandbox="allow-scripts"` — no `allow-same-origin`, no cookie/localStorage access, no parent DOM access |
| **Database connection failure** | Medium | SQLAlchemy connection pool with retry; health endpoint; graceful 503 response |
| **API key not set** | Low | `.env.example` with clear required/optional labels; startup validation logs warning |
| **Transcript data quality** | Low | Source repository is well-maintained; ingest script skips malformed files |

---

## 2. User Flows

### 2.1 Primary Flow — Ask a Growth Question

```
[Landing Screen]
  → User types question in composer
  → (Optional) User selects output format: Essay / Markdown / HTML
  → User presses Send
  → [Chat Screen]
      → Streaming bot response appears with typing animation
      → Source chips appear below response showing episode titles
      → User asks follow-up question
      → Session context maintained across turns
```

### 2.2 Artifact Generation Flow

```
[Chat Screen]
  → User selects "HTML" or "Markdown" format in Format picker
  → User sends message
  → Bot generates artifact + streams explanation
  → Artifact panel slides open on right side
  → HTML renders in sandboxed iframe / Markdown rendered with syntax highlighting
  → User can expand, copy, or close the artifact panel
```

### 2.3 Ship 30 Essay Flow

```
[Chat Screen]
  → User selects "✍️ Essay" format
  → User asks: "Write a Ship 30 essay about reducing churn"
  → Backend routes to ship30 skill
  → ~1,250-word essay generated with hook, headings, bullets, takeaway
  → Essay rendered in artifact viewer as Markdown
  → User can copy full essay text
```

### 2.4 New Session Flow

```
[Any Screen]
  → User clicks "+ New Chat" in sidebar
  → Fresh session created with new session_id
  → Previous session preserved in sidebar history
  → User can switch between sessions
```

### 2.5 Model Switch Flow

```
[.env configuration]
  → Set LLM_PROVIDER=ollama or LLM_PROVIDER=anthropic
  → Restart containers: docker compose up -d
  → UI continues working; model handles requests via provider abstraction
```

---

## 3. Acceptance Criteria

### AC-1: Grounded Answers
- [ ] Every assistant response to a growth/product question includes at least one source chip citing a Lenny's Podcast episode
- [ ] When no relevant transcript exists, the assistant responds: "I don't have transcript coverage of that topic" rather than hallucinating

### AC-2: Session Persistence
- [ ] Starting a new chat creates a new row in the `sessions` table
- [ ] Refreshing the browser and selecting a previous session restores full message history
- [ ] Two sessions maintain independent context (question in session A does not affect session B)

### AC-3: Ship 30 Essay
- [ ] Essay is 1,100–1,400 words
- [ ] Essay contains a hook, at least 2 headings, bullet points, and a specific takeaway
- [ ] Essay cites at least one Lenny's Podcast transcript insight

### AC-4: Artifact Viewer
- [ ] HTML artifact renders inside a sandboxed iframe, not as raw code
- [ ] Markdown artifact renders with formatted headings, code blocks, and lists
- [ ] Artifact panel opens alongside chat without replacing it
- [ ] Closing the artifact panel returns to full-width chat

### AC-5: Dual LLM
- [ ] Setting `LLM_PROVIDER=anthropic` uses the Anthropic API
- [ ] Setting `LLM_PROVIDER=ollama` routes all requests to local Ollama
- [ ] Both providers produce streaming responses via SSE
- [ ] If Ollama is unavailable, a clear error message is returned (not a silent hang)

### AC-6: One-Command Startup
- [ ] `docker compose up --build` starts the full stack from a clean clone
- [ ] The application is accessible at `http://localhost:3000` within 60 seconds
- [ ] The health endpoint `GET /health` returns `{"status": "ok"}`

---

## 4. Implementation Plan

### Phase 1 — Foundation (Day 1)
- FastAPI project scaffold with health endpoint
- SQLAlchemy models: Session, Message, Artifact
- Supabase PostgreSQL connection and migration
- Docker Compose with backend + frontend services

### Phase 2 — Knowledge Base (Day 1–2)
- Transcript ingestion script (clone, chunk, embed, store in ChromaDB)
- Retriever with cosine similarity search
- Source metadata attached to every retrieved chunk

### Phase 3 — Agent Layer (Day 2)
- Provider abstraction: AnthropicProvider, OllamaProvider behind common interface
- Tool definitions: search_transcripts, generate_ship30_essay, generate_artifact
- Agentic loop with tool dispatch and SSE streaming

### Phase 4 — Frontend (Day 3)
- Next.js chat UI with session sidebar
- SSE streaming hook (useChat)
- Artifact viewer (split-pane, sandboxed iframe, Markdown renderer)
- Ship 30 / Format selector in composer

### Phase 5 — Polish & Deployment (Day 4)
- UI design system (dark theme, animations, responsive layout)
- Error handling, loading states, typing indicators
- README, PRD, architecture.md, design.md
- Tests and manual test plan
- Demo video recording
