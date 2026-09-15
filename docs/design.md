# Design Document
## The Lenny Growth Assistant

**Version:** 1.0  
**Author:** Deva Harsha Annamreddy  
**Date:** September 2026

---

## 1. Design Philosophy

The interface is built on three principles:

**1. Content over chrome.** The user is here for Lenny's insights, not UI decoration. Every visual element either carries information or creates space for information to breathe. Nothing is decorative without purpose.

**2. Familiar confidence.** Power users of AI tools (Claude, ChatGPT) arrive with strong mental models. We match those models — chat on left, artifacts on right, sidebar for history — so the tool feels immediately familiar, letting users focus on the task rather than learning a new UI.

**3. Signal through restraint.** The dark background makes the green accent system highly visible. Green means "active", "AI", "success". A single accent colour used consistently carries more meaning than many colours used arbitrarily.

---

## 2. Visual Design System

### 2.1 Colour Tokens

| Token | Value | Use |
|-------|-------|-----|
| `--bg` | `#0a0a0a` | App background |
| `--bg-2` | `#111111` | Sidebar background |
| `--surface` | `#161616` | Cards, bubbles, inputs |
| `--surface-2` | `#1f1f1f` | User message pill, hover states |
| `--surface-3` | `#282828` | Pressed states |
| `--border` | `#232323` | Default borders |
| `--border-2` | `#333333` | Hover/focus borders |
| `--green` | `#4ade80` | Primary accent — AI indicator, CTA, active states |
| `--green-dim` | `rgba(74,222,128,0.12)` | Subtle green fills |
| `--text` | `#ffffff` | Primary text |
| `--text-soft` | `#cccccc` | Secondary text |
| `--text-muted` | `#888888` | Timestamps, labels |
| `--text-dim` | `#444444` | Placeholder text |

**Rationale:** Near-black backgrounds with a single saturated green accent is inspired by terminal aesthetics and tools like Linear and Vercel — environments where developers and power users feel at home. Green specifically was chosen because it reads as "growth" (on-brand for a growth assistant) and "go/active/healthy".

### 2.2 Typography

**Font:** Inter (Google Fonts — 400, 500, 600, 700, 800, 900)

| Role | Size | Weight | Usage |
|------|------|--------|-------|
| Welcome heading | 52px | 800 | Welcome screen H1 |
| Section heading | 18px | 700 | Artifact headings |
| Body | 14.5px | 400 | Chat messages, prose |
| UI labels | 13px | 500 | Button text, chips |
| Timestamps | 11px | 400 | Message time |
| Code | 13px | 400 | `JetBrains Mono` |

**Rationale:** Inter at heavy weights (800+) creates the "bold editorial" feel seen in modern AI products. Generous line-height (1.7) in chat makes long AI responses scannable without fatigue.

### 2.3 Spacing and Radius

- Base spacing unit: 4px
- Border radius: `8px` (small), `12px` (default), `16px` (large), `24px` (pill/composer)
- Message max-width: 760px — matches Claude.ai's reading line length, prevents ultra-wide lines

---

## 3. Information Architecture

```
App Shell
├── Sidebar (280px, collapsible)
│   ├── Logo + collapse toggle
│   ├── + New Chat button
│   ├── Search sessions
│   └── Session list (grouped by TODAY / YESTERDAY / EARLIER)
└── Main Area (flex: 1)
    ├── Chat Panel
    │   ├── [Welcome Screen]  — shown when no messages
    │   │   ├── Turtle avatar + heading
    │   │   └── Composer (textarea + format picker)
    │   └── [Chat Screen]  — shown when conversation active
    │       ├── Messages list (scrollable)
    │       │   ├── User messages (right-aligned pill)
    │       │   └── Bot messages (plain text, left, with source chips + action bar)
    │       └── Chat input bar (fixed bottom)
    └── Artifact Panel (slides in from right, 45% width)
        ├── Tab bar (filename + type)
        ├── Sandboxed iframe (HTML artifacts)
        └── Markdown renderer (MD artifacts)
```

---

## 4. Key Interaction States

### 4.1 Welcome Screen
- **Default:** Turtle avatar floating with halo pulse, centered heading, composer with placeholder text
- **Composer focused:** Green border glow animates in, placeholder fades
- **Typing:** Send button activates (green fill), Format picker available
- **Streaming (after first send):** Welcome screen unmounts, chat screen mounts with smooth transition

### 4.2 Chat Screen — Message States

| State | Visual |
|-------|--------|
| User message sent | Pill slides in from right (`slideInRight` 240ms) |
| Bot thinking (no text yet) | Three bouncing dots with stagger delay |
| Bot streaming | Text renders incrementally, no bubble border — plain on dark |
| Bot response complete | Action bar fades in below message on hover |
| Error | Red-tinted error banner with ⚠ icon |
| Scrolled up | Scroll-to-bottom chevron button appears |

### 4.3 Action Bar (Bot Messages)
Appears on hover below each bot message:

| Button | Behaviour |
|--------|-----------|
| Copy | Copies raw text; icon swaps to ✓ for 2s |
| Regenerate | Re-sends previous user message (last message only) |
| 👍 Thumbs Up | Turns green with pop animation; "Helpful!" toast |
| 👎 Thumbs Down | Turns orange; inline feedback textarea slides open |
| Share | Copies message text + "— Oogway AI" attribution; ✓ toast |

### 4.4 Artifact Panel
- **Closed:** Chat occupies full main area
- **Opening:** Artifact panel slides in from right (300ms ease), chat area compresses
- **HTML artifact:** Rendered in `<iframe sandbox="allow-scripts">` — no parent DOM access
- **Markdown artifact:** Rendered with `react-markdown` + `remark-gfm` with syntax highlighting
- **Close:** Artifact panel slides out, chat expands back

### 4.5 Format Picker
- Collapsed: Shows "+ Format" with chevron
- Expanded: Popup above with three options (Essay, Markdown, HTML) with descriptions
- Selected: Button shows selected format name; "Clear" link appears
- Active selection: Green border on footer button

### 4.6 Sidebar
- Session items animate in with `sidebarSlide` on load
- Active session: Left green accent border + subtle inner glow
- Hover: Background lightens, left border animates in
- Session actions (rename/delete): Appear on hover, hidden otherwise

---

## 5. Responsive Behaviour

### Desktop (≥ 1024px)
- Full layout: sidebar + chat + optional artifact panel
- Sidebar always visible (collapsible but not hidden)
- Artifact panel opens beside chat (45% width)

### Tablet (768px–1023px)
- Sidebar collapses to icon rail or hidden behind hamburger
- Artifact panel renders as bottom sheet or full overlay
- Message max-width scales to 90% viewport

### Mobile (< 768px)
- Sidebar becomes a full-height drawer (off-canvas, z-index overlay)
- Artifact panel renders as modal overlay
- Composer stays fixed at bottom with safe-area insets
- Suggestion chips stack to single column

---

## 6. Accessibility Considerations

- **Colour contrast:** All text on `--surface` backgrounds meets WCAG AA (minimum 4.5:1 for normal text). Green accent `#4ade80` on `#0a0a0a` = 7.2:1.
- **Keyboard navigation:** All interactive elements are reachable via Tab. Composer captures Enter to send (Shift+Enter for newline). Escape closes popups.
- **ARIA labels:** Action buttons have `aria-label` attributes (`aria-label="Copy message"`, `aria-pressed` for toggle states).
- **Motion:** Animations use `cubic-bezier(0.22,1,0.36,1)` spring curves — fast in, slow settle. No looping animations on chat messages (only entrance). Users who prefer reduced motion: `@media (prefers-reduced-motion)` disables entrance animations.
- **Focus indicators:** Browser focus ring preserved on all interactive elements; not suppressed globally.
- **Screen reader:** Message list has `role="log"` with `aria-live="polite"` so screen readers announce new messages without interrupting.

---

## 7. Design Decisions and Trade-offs

### Decision 1: No avatar icons in chat
**Chose:** Plain text bot responses with no avatar bubble background (matching Claude.ai)  
**Alternative:** Avatar circles with bot icon next to each message  
**Reason:** Avatars add visual noise without information value. Clean plain text is more readable for long responses and mirrors the most-used AI chat interfaces users already know.

### Decision 2: Green as the sole accent colour
**Chose:** Single `#4ade80` green for all active/AI states  
**Alternative:** Multiple accent colours (blue for user, green for bot, orange for warnings)  
**Reason:** One accent used consistently creates a stronger visual identity. "Green = Oogway/AI" becomes a reliable signal. Orange is reserved for warnings/thumbs-down only to preserve meaning.

### Decision 3: Artifact panel rather than modal
**Chose:** Side-by-side split pane for artifacts  
**Alternative:** Modal overlay, new tab  
**Reason:** Side-by-side allows the user to read the artifact and continue the conversation simultaneously — the core use case for generated content. Modals break conversation flow; new tabs lose context.

### Decision 4: Inline feedback (thumbs down) rather than toast-only
**Chose:** Thumbs down opens a feedback textarea below the message  
**Alternative:** Just visual confirmation with no text input  
**Reason:** Qualitative feedback is far more useful for improving the system than binary signals. The textarea is low-friction — completely optional, submits inline without navigation.

### Decision 5: Welcome screen with no suggestion chips (final)
**Chose:** Clean welcome screen with just turtle + heading + composer  
**Alternative:** Suggestion chips grid below composer  
**Reason:** Chips create cognitive load and telegraph the system's limited scope. An empty composer with a confident heading ("Ask anything about growth") signals broader capability and invites genuine exploration. Chips were removed after user testing feedback.
