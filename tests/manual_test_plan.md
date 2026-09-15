# Manual Test Plan
## The Lenny Growth Assistant

**Version:** 1.0  
**Author:** Deva Harsha Annamreddy  
**Date:** September 2026

---

## Prerequisites

Before running these tests, ensure the stack is running:

```bash
docker compose up --build
```

- Frontend accessible at `http://localhost:3000`
- Backend health check passes: `curl http://localhost:8000/health`
- ChromaDB has been populated: `docker compose exec backend python scripts/ingest_transcripts.py`
- `.env` contains a valid `DATABASE_URL` and `LLM_PROVIDER`

---

## MT-1: Health Check

**Goal:** Verify the backend is running and connected.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1.1 | `GET http://localhost:8000/health` | Status 200, body contains `"status": "ok"` |
| 1.2 | Check `provider` field in response | Value is `"anthropic"` or `"ollama"` (matching `.env`) |
| 1.3 | Check `db` field | Value is `"connected"` |
| 1.4 | Check `chroma_count` field | Integer > 0 (transcripts ingested) |

---

## MT-2: Welcome Screen

**Goal:** Verify the initial landing state is correct.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 2.1 | Open `http://localhost:3000` | Page loads, dark background visible |
| 2.2 | Observe center of screen | Turtle avatar visible with pulsing halo |
| 2.3 | Read heading | "Ask Lenny anything about growth." |
| 2.4 | Observe below heading | Composer input visible, no suggestion chips present |
| 2.5 | Click inside textarea | Green glow border animates in |
| 2.6 | Type a question | Send button turns green/active |

---

## MT-3: First Message and Streaming (AC-1)

**Goal:** Verify streaming chat response with source grounding.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 3.1 | Type: `"What is product-led growth?"` and press Enter | Welcome screen transitions to chat screen |
| 3.2 | Observe immediately | Three bouncing dots appear (thinking state) |
| 3.3 | Within 3–5 seconds | Text starts streaming character by character |
| 3.4 | After response completes | Source chips appear below the response |
| 3.5 | Read source chips | Each chip shows an episode title (e.g., "Episode 42: ...") |
| 3.6 | Hover over a message | Action bar fades in below (copy, regenerate, 👍, 👎, share) |

**Pass criteria:** At least one source chip appears. Response references Lenny's Podcast content.

---

## MT-4: Multi-turn Conversation (AC-2)

**Goal:** Verify session context persists across turns.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 4.1 | Ask a first question about PLG | Receive response |
| 4.2 | Ask a follow-up: `"Can you elaborate on the first point?"` | Response references the previous answer (context retained) |
| 4.3 | Note the session title in sidebar | Title auto-generated or "New Chat" |
| 4.4 | Refresh the browser | Same session selected, full message history visible |
| 4.5 | Verify content is identical | All messages intact, source chips still showing |

---

## MT-5: New Session Independence (AC-2)

**Goal:** Two sessions maintain independent context.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 5.1 | Ask a question in Session A about "churn" | Receive response about churn |
| 5.2 | Click "+ New Chat" in sidebar | Fresh empty chat appears |
| 5.3 | Ask `"What were we just discussing?"` in Session B | Model says it has no prior context (not about churn) |
| 5.4 | Click Session A in sidebar | Churn conversation fully preserved |

---

## MT-6: Ship 30 Essay Generation (AC-3)

**Goal:** Verify essay skill produces correctly formatted output.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 6.1 | Click the `✍️ Essay` format button in composer | Button shows "Essay" as active, green border |
| 6.2 | Type: `"Write an essay about reducing churn in B2B SaaS"` and send | Bot begins streaming |
| 6.3 | After completion | Artifact panel slides open on the right side |
| 6.4 | Read the artifact | Contains a hook opening, at least 2 headings, bullet points |
| 6.5 | Check word count (estimate) | Approximately 1,100–1,400 words |
| 6.6 | Check for source citation | At least one Lenny's Podcast episode title mentioned |

**Pass criteria:** Essay is in the artifact panel, has the required structure, cites an episode.

---

## MT-7: Markdown Artifact Generation (AC-4)

**Goal:** Verify Markdown artifact rendering.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 7.1 | Select `📄 Markdown` format in composer | Active state shown |
| 7.2 | Ask: `"Summarise the key PLG metrics as a structured document"` | Artifact panel opens |
| 7.3 | Inspect artifact panel | Markdown rendered with formatted headings, lists, code blocks |
| 7.4 | Verify not raw Markdown | `# Heading` not visible; styled `<h1>` rendered instead |
| 7.5 | Close artifact panel | Panel slides out, chat returns to full width |
| 7.6 | Open a new artifact | Panel slides in again |

---

## MT-8: HTML Artifact Generation (AC-4)

**Goal:** Verify HTML artifact security sandboxing and rendering.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 8.1 | Select `</> HTML` format in composer | Active state shown |
| 8.2 | Ask: `"Create an interactive PLG metrics dashboard in HTML"` | Artifact panel opens |
| 8.3 | Observe artifact | HTML renders visually (not raw code) inside the panel |
| 8.4 | Open browser DevTools → inspect iframe | `sandbox="allow-scripts"` attribute present |
| 8.5 | Check sandbox does NOT have | `allow-same-origin`, `allow-forms`, `allow-top-navigation` |
| 8.6 | Attempt in console: `frames[0].document.cookie` | Throws cross-origin error (expected, proves sandbox) |

---

## MT-9: Artifact Panel Behaviour (AC-4)

**Goal:** Verify side-by-side panel opens and closes correctly.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 9.1 | With no artifact active | Chat panel fills full main area |
| 9.2 | After generating any artifact | Panel slides in from right (~45% width) |
| 9.3 | During slide-in | Smooth 300ms ease animation, chat compresses |
| 9.4 | Click close (×) on artifact panel | Panel slides out, chat expands back to full width |
| 9.5 | Click artifact tab while panel is open | Content remains visible, no page reload |

---

## MT-10: Dual LLM Provider Switch (AC-5)

**Goal:** Verify both Anthropic and Ollama providers work.

**Test A — Anthropic (cloud):**

| Step | Action | Expected Result |
|------|--------|-----------------|
| 10.1 | Set `.env`: `LLM_PROVIDER=anthropic`, restart containers | Health shows `"provider": "anthropic"` |
| 10.2 | Ask a question | Response streams correctly |
| 10.3 | Check backend logs | `[CHAT] provider=anthropic` log line |

**Test B — Ollama (local):**

| Step | Action | Expected Result |
|------|--------|-----------------|
| 10.4 | Ensure Ollama is running locally with `llama3.1:8b` | `ollama list` shows the model |
| 10.5 | Set `.env`: `LLM_PROVIDER=ollama`, restart containers | Health shows `"provider": "ollama"` |
| 10.6 | Ask a question | Response streams (may be slower, but streams) |
| 10.7 | Verify SSE | Response arrives via SSE, not a single payload |

**Test C — Ollama unavailable:**

| Step | Action | Expected Result |
|------|--------|-----------------|
| 10.8 | Stop Ollama, keep `LLM_PROVIDER=ollama` | Ask a question |
| 10.9 | Observe UI | Error banner appears, not a silent hang |
| 10.10 | Check error message | Clear description (not a timeout with no feedback) |

---

## MT-11: Action Bar Interactions

**Goal:** Verify all action buttons in the response action bar are functional.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 11.1 | Hover over a bot message | Action bar fades in with 5 buttons |
| 11.2 | Click Copy icon | Toast "Copied!" appears for 2s; clipboard contains message text |
| 11.3 | Click 👍 | Icon turns green with pop animation; "👍 Helpful!" toast appears |
| 11.4 | Click 👍 again | Deselects (returns to neutral) |
| 11.5 | Click 👎 | Icon turns orange; feedback textarea slides open below |
| 11.6 | Type in feedback area and click "Send feedback" | Textarea closes, thank-you state shown |
| 11.7 | Click Share | Toast "Copied!" appears; clipboard contains message + "— Oogway AI" |

---

## MT-12: Session Sidebar

**Goal:** Verify session management in the sidebar.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 12.1 | Create 3 separate chat sessions | All 3 appear in sidebar |
| 12.2 | Hover over a session | Rename (pencil) and delete (trash) icons appear |
| 12.3 | Click pencil icon | Inline rename input appears |
| 12.4 | Type new name and press Enter | Session renamed in sidebar and DB |
| 12.5 | Click trash icon | Confirmation or immediate deletion |
| 12.6 | Click a different session | Chat panel switches to that session's history |
| 12.7 | Active session indicator | Left green border on active session |

---

## MT-13: One-Command Startup (AC-6)

**Goal:** Verify the Docker Compose setup works from a clean clone.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 13.1 | Clone repo fresh: `git clone https://github.com/ADevaHarsha813/lenny-growth-assistant.git` | Success |
| 13.2 | Copy `.env.example` to `.env`, fill DATABASE_URL | `.env` file ready |
| 13.3 | Run `docker compose up --build` | Both services build and start |
| 13.4 | Within 60 seconds | `http://localhost:3000` loads |
| 13.5 | Check health endpoint | `{"status": "ok"}` |

---

## MT-14: Responsive Layout

**Goal:** Verify the UI adapts to smaller viewports.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 14.1 | Open DevTools → set viewport to 768px wide | Sidebar collapses or becomes drawer |
| 14.2 | Set viewport to 390px (mobile) | Sidebar becomes off-canvas drawer |
| 14.3 | Tap hamburger/menu icon | Drawer opens from left |
| 14.4 | Tap outside drawer | Drawer closes |
| 14.5 | Generate an artifact on mobile | Artifact renders as modal/overlay, not squished panel |

---

## MT-15: No Hallucination / Graceful Out-of-Scope

**Goal:** Verify the RAG grounding prompt strategy works.

| Step | Action | Expected Result |
|------|--------|-----------------|
| 15.1 | Ask: `"What is the best recipe for chocolate chip cookies?"` | Model responds it doesn't have relevant transcript coverage |
| 15.2 | Ask a real growth question | At least one source chip citing a real episode |
| 15.3 | Verify model doesn't invent episode titles | Source chip titles match actual files in `data/transcripts/` |

---

## Test Summary Checklist

| Test | Area | Status |
|------|------|--------|
| MT-1 | Health endpoint | ☐ |
| MT-2 | Welcome screen | ☐ |
| MT-3 | Streaming + sources | ☐ |
| MT-4 | Session persistence | ☐ |
| MT-5 | Session isolation | ☐ |
| MT-6 | Ship 30 essay | ☐ |
| MT-7 | Markdown artifact | ☐ |
| MT-8 | HTML artifact + sandbox | ☐ |
| MT-9 | Artifact panel UX | ☐ |
| MT-10 | Dual LLM provider | ☐ |
| MT-11 | Action bar buttons | ☐ |
| MT-12 | Session sidebar | ☐ |
| MT-13 | One-command startup | ☐ |
| MT-14 | Responsive layout | ☐ |
| MT-15 | RAG grounding | ☐ |
