# Product Requirements Document
# The Lenny Growth Assistant

*Status: Draft — v1.0*
*Author: Deva Harsha Annamreddy*
*Date: 2026-09-14*

---

## Discovery Brief

### User & Problem
**Primary user:** Product managers, growth leads, and founders at early- to mid-stage B2B SaaS companies who rely on Lenny's Podcast for product and growth guidance.

**Job to be done:** Get fast, grounded answers to specific product and growth questions — without manually searching through hundreds of hours of podcast transcripts.

**Pain removed:** Hours spent re-listening to episodes to find a specific framework, quote, or strategy. The assistant surfaces relevant transcript content instantly, cites the source, and turns it into reusable written content.

### Success Metric
- **Primary:** ≥80% of answers cite a specific transcript source (measurable via source field presence in responses)
- **Secondary:** Session creation to first grounded answer in < 10 seconds on local Ollama

### Assumptions
1. Transcripts in the ChatPRD/lennys-podcast-transcripts repo are accurate and complete enough for retrieval
2. Users are internal team members — no public auth/login required for this engagement
3. Local Ollama (llama3.1:8b) is sufficient quality for product Q&A within the transcript corpus
4. Markdown and basic HTML/CSS are the two artifact formats the team needs most

### Scope

**In scope:**
- Grounded conversational Q&A from transcript knowledge base
- Session management with persistent history
- Ship 30 for 30 essay generation skill
- Markdown and HTML artifact generation with in-app viewer
- Dual LLM configuration (cloud + local Ollama)
- Docker Compose one-command startup

**Out of scope:**
- User authentication and multi-tenancy
- Image/audio/video handling
- Cloud deployment (local Docker only for this engagement)
- Real-time collaboration

### Risks & Trade-offs

| Risk | Mitigation |
|------|------------|
| Hallucination on out-of-corpus questions | System prompt instructs model to acknowledge when material doesn't support an answer |
| Ollama latency (local hardware dependent) | Streaming SSE so user sees progress; health endpoint exposes model status |
| HTML artifact XSS | Sandboxed iframe with restricted permissions — documented in architecture.md |
| Transcript quality variance | Chunking with overlap preserves context across poor-quality segments |
| ChromaDB vs pgvector | ChromaDB chosen for zero-config Docker setup; trade-off documented |

---

*Full spec, acceptance criteria, and flows to be completed during Phase 5.*
