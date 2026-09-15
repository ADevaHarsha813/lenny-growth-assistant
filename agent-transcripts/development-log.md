# Agent-Assisted Development Log
## The Lenny Growth Assistant

**Author:** Deva Harsha Annamreddy  
**AI Partner:** Claude Sonnet (Anthropic)  
**Project Duration:** September 12–15, 2026  
**Assignment:** Forward Deployed Engineer Take-Home — Oogway Labs

---

## Overview

This log documents the key decisions, trade-offs, corrections, and architectural choices made during the development of the Lenny Growth Assistant. It captures the authentic back-and-forth between the developer and the AI assistant that shaped the final product.

---

## Session 1 — Project Architecture and Stack Selection

**Date:** September 12, 2026

### Initial prompt to Claude:
> "I need to build a RAG-powered chatbot over Lenny's Podcast transcripts. It should support streaming responses, artifact generation, and work with both Anthropic and Ollama. I have 4 days."

### Key decisions made:

**Decision: FastAPI over Django/Flask**

Claude recommended FastAPI for three reasons: async-first design (critical for SSE streaming), automatic OpenAPI docs, and Pydantic validation built in. The evaluation criterion for SSE streaming made this the clear choice. Django's sync-first model would have required workarounds.

**Decision: ChromaDB over Pinecone/Weaviate**

Claude proposed ChromaDB as the vector store. Rationale: it runs locally in Docker with no external API key required, persists to a mounted volume, and is Python-native. For a demo tool that needs to work offline (Ollama mode), ChromaDB being local was essential. Pinecone would add another cloud dependency and potential point of failure in a demo.

**Decision: SQLAlchemy async + Supabase over raw Supabase client**

Initial suggestion was to use the Supabase Python client directly. Claude pointed out that the async Supabase client has limited query capabilities. Instead, SQLAlchemy with asyncpg provides full ORM capability, async session management, and connection pooling — while Supabase provides the hosted PostgreSQL. This combination gave full control without running a local Postgres.

**Correction:** The first pass at `database.py` used `create_engine` (sync). Claude caught this immediately — async endpoints with a sync engine would block the event loop. Fixed to `create_async_engine` with `asyncpg` driver.

---

## Session 2 — RAG Pipeline and Chunking Strategy

**Date:** September 12–13, 2026

### Key decisions made:

**Decision: Chunk size 1,800 chars with 300-char overlap**

Claude proposed several chunking strategies. The 1,800/300 approach was chosen because:
- 1,800 chars (~450 tokens) fits comfortably within context windows while being large enough to contain a complete argument or insight
- 300-char overlap prevents losing context at chunk boundaries (a guest making a point that starts at char 1,790 won't be lost)
- Smaller chunks (e.g., 500 chars) lose narrative context; larger chunks (3,000+) fill too much of the LLM prompt

**Decision: nomic-embed-text over OpenAI embeddings**

Evaluated: OpenAI `text-embedding-3-small` vs. `nomic-embed-text` (Ollama). Chose nomic because it runs locally alongside llama3.1:8b — meaning the entire stack can run without internet in Ollama mode. This was a deliberate trade-off: nomic is slightly lower quality than OpenAI's embeddings, but the demo requirement of a fully local stack outweighed the marginal quality difference.

**Correction: Cosine similarity vs. L2 distance**

First implementation used raw ChromaDB L2 distances as scores. A lower L2 distance = more similar, but the UI was displaying it as a similarity score — so high-quality matches showed as "0.12" which looked like a low score. Claude corrected this: convert distance to a `[0, 1]` similarity via `1 / (1 + distance)`. This made the source chips show meaningful scores.

**Decision: Top-5 retrieval per query**

Claude's recommendation: 3–5 chunks are the sweet spot. Fewer than 3 risks missing relevant context if the first retrieved chunk is marginally relevant. More than 5 starts filling the prompt context with noise and slows the LLM. 5 was chosen as the conservative maximum.

---

## Session 3 — Agentic Loop Design

**Date:** September 13, 2026

### Key decisions made:

**Decision: Tool-use loop (max 5 iterations) over direct prompt**

Two approaches were considered:
1. Always inject retrieved chunks and generate directly
2. Let the LLM decide when to search (agentic tool use)

Claude argued for option 2: the tool-use loop allows the model to decide whether a question needs retrieval at all, and to call multiple tools in sequence (e.g., search first, then generate a Ship 30 essay using the search results). A fixed "always inject" approach would add unnecessary tokens to simple responses.

Max 5 iterations was chosen as a safety ceiling — prevents infinite loops in edge cases while allowing enough depth for the essay + artifact workflows.

**Decision: Skill routing via `skill` hint parameter**

The chat request body carries an optional `skill` field (`"ship30"`, `"artifact_markdown"`, `"artifact_html"`). Claude's design: rather than using a separate endpoint per skill, a single chat endpoint with a skill hint lets the orchestrator offer the appropriate tools.

**Correction: Streaming SSE format**

Initial implementation used `yield json.dumps(event)` without the `data: ` prefix. This is not valid SSE. Claude caught this: SSE format requires `data: {payload}\n\n`. The fix was applied across the orchestrator's streaming generator.

**Decision: Include sources as a separate SSE event type**

Options considered: (a) embed source citations inline in the text, (b) emit them as a dedicated `sources` event after the text is done. Chose (b) because it lets the frontend render source chips independently of the text stream, without regex parsing. The UI can show sources below the completed message without interrupting streaming.

---

## Session 4 — Frontend Architecture

**Date:** September 13–14, 2026

### Key decisions made:

**Decision: React state for SSE handling, not React Query**

Claude recommended a custom `useChat` hook that manages the `EventSource` connection directly. React Query's SSE support requires workarounds; a custom hook is simpler and gives full control over incremental text accumulation (appending `text_delta` events to a string).

**Decision: CSS custom properties design system over Tailwind utilities for layout**

Tailwind was already installed but Claude suggested using CSS custom properties for the design tokens (colours, radii, spacing). The reasoning: utility-first Tailwind works well for component styling but the animation keyframes and complex state transitions (e.g., hover action bars, glow effects) were cleaner in a single `globals.css` file with CSS variables.

**Correction: Flex scroll bug — `min-height: 0`**

The chat panel's message list wasn't scrolling. The root cause: a flex child with `overflow-y: auto` won't scroll unless it has `min-height: 0` — otherwise the parent flexbox gives it as much space as its content needs, which means it's never actually overflowing. This is a well-known CSS flex quirk. Adding `min-height: 0` to `.messages-list` fixed the scroll immediately.

**Decision: Sandboxed iframe for HTML artifacts**

The HTML artifact sandboxing decision (covered in architecture.md) came from a Claude suggestion. The key insight: without `sandbox="allow-scripts"` but without `allow-same-origin`, JavaScript can run inside the iframe but cannot access the parent DOM, cookies, or localStorage. This is defence-in-depth against prompt injection via generated HTML.

**Correction: `Skill` TypeScript type narrowing**

The initial TypeScript type for the `skill` field in ChatInput was `string | null`. This was too broad — it allowed invalid strings to reach the API. Claude tightened it to `"ship30" | "artifact_markdown" | "artifact_html" | null`, which provides compile-time safety and matches the Pydantic enum on the backend.

---

## Session 5 — UI Polish and Animation System

**Date:** September 14, 2026

### Key decisions made:

**Decision: Claude.ai layout reference**

The message layout (user messages as right-aligned pills, bot responses as plain left-aligned text with no bubble background) was modeled directly on Claude.ai's UI. This was a deliberate choice — the target users are power users of AI tools who arrive with a strong mental model of chat interfaces. Matching that model reduces cognitive overhead.

**Decision: Single green accent colour**

Design token `--green: #4ade80` is the only accent colour. Claude recommended this after reviewing several options: a single well-chosen accent creates a stronger signal than multiple colours. Green reads as "growth" and "active" — directly on-brand for a growth assistant. Orange is reserved exclusively for warning/thumbs-down states.

**Correction: Turtle avatar positioning on welcome screen**

The original layout had the turtle avatar, heading, and composer in a fixed column. On wide viewports, this felt off-centre. The fix: use `text-align: center; gap: 28px` on `.welcome-content-centered` and switch the composer from `position: fixed` bottom to an inline element below the heading. This made the entire welcome state feel properly centred.

**Decision: Remove suggestion chips from welcome screen**

An initial design had 6 suggestion chips below the composer. After discussing with the AI assistant, these were removed because they create cognitive load and telegraph the system's limited scope. An empty composer with a confident heading invites more genuine exploration. Claude's reasoning: chips work well for narrow-scope chatbots (like customer support); for a general growth assistant, they artificially constrain the user's imagination.

---

## Session 6 — Testing Strategy

**Date:** September 15, 2026

### Key decisions made:

**Decision: pytest-asyncio with httpx AsyncClient for API tests**

Flask's test client doesn't work with FastAPI's async endpoints. Claude recommended `httpx.AsyncClient` with `ASGITransport` — this lets tests run against the actual FastAPI app in-process without a running server, using real async semantics.

**Decision: Mock at the orchestrator boundary for chat tests**

The chat endpoint's SSE streaming involves an async generator. To test it without a real LLM call, Claude suggested mocking `app.agents.orchestrator.run_agent` to return a fake async generator. This isolates the HTTP/SSE layer from the LLM layer cleanly.

**Decision: Mock ChromaDB for retrieval tests**

Running retrieval tests against a real ChromaDB collection would require ingested data and Ollama for embeddings — too heavy for unit tests. Claude proposed mocking both `chroma_collection` (the ChromaDB client) and `embed_text` (the embedding function) to test the retrieval logic in isolation.

---

## Key Lessons and Trade-offs

### 1. Local-first demo requirement shapes every decision
The requirement to support Ollama locally wasn't just a feature — it was an architectural constraint. Every dependency choice (ChromaDB over Pinecone, nomic-embed-text over OpenAI embeddings, Docker Compose over hosted infra) flows from this.

### 2. SSE streaming masks latency
The biggest UX win was SSE streaming. Users on Ollama (llama3.1:8b, ~15 tokens/second) would find the 30-45 second wait intolerable as a blocking response. Streaming makes the first tokens appear within 2–3 seconds, and the incremental output keeps the user engaged.

### 3. RAG grounding is the product
The system prompt that instructs the LLM to "answer ONLY using the provided transcript excerpts" and explicitly say when it doesn't have coverage is what makes this product trustworthy. Without strict grounding, a generic LLM answer would be indistinguishable from any other chatbot.

### 4. Scope discipline
The explicit exclusion list in the PRD (no auth, no real-time ingestion, no mobile native app) kept the project shippable in 4 days. Each excluded item was tempting — but would have added 1–3 days of work without improving the core value proposition of "query Lenny's brain instantly."

### 5. The CSS flex `min-height: 0` bug
This stumped development for about 45 minutes. The symptom (messages overflow instead of scroll) and the fix (`min-height: 0`) are non-obvious. It's worth documenting explicitly because it affects any chat UI built with CSS flexbox.

---

## Files Generated with AI Assistance

| File | AI contribution |
|------|----------------|
| `backend/app/main.py` | Scaffold and lifespan events |
| `backend/app/agents/orchestrator.py` | Agentic loop design and SSE streaming |
| `backend/app/agents/provider.py` | Dual-provider abstraction pattern |
| `backend/app/rag/retriever.py` | Chunking strategy, score normalisation |
| `backend/scripts/ingest_transcripts.py` | Ingestion pipeline structure |
| `frontend/hooks/useChat.ts` | SSE EventSource management pattern |
| `frontend/components/chat/MessageBubble.tsx` | Action bar interaction state |
| `frontend/app/globals.css` | Animation keyframes, design token system |
| `docs/PRD.md` | Discovery brief, success metrics, acceptance criteria |
| `docs/architecture.md` | System topology, API specification |
| `docs/design.md` | Design system, interaction states, decisions |
| `tests/test_api.py` | FastAPI endpoint tests |
| `tests/test_retrieval.py` | RAG retrieval unit tests |
| `tests/test_sessions.py` | Session persistence tests |
| `tests/manual_test_plan.md` | UI test scenarios |
