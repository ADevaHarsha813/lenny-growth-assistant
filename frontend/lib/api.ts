const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BACKEND}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || `API error ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Sessions
  createSession: (data: { title?: string; llm_provider?: string }) =>
    apiFetch("/api/sessions", { method: "POST", body: JSON.stringify(data) }),
  
  getSessions: () =>
    apiFetch("/api/sessions"),

  getSession: (id: string) =>
    apiFetch(`/api/sessions/${id}`),

  // Artifacts
  getArtifacts: (sessionId: string) =>
    apiFetch(`/api/artifacts/${sessionId}`),

  // Health
  getHealth: () =>
    apiFetch("/health"),

  // Streaming chat — returns raw Response for SSE parsing
  streamChat: (payload: { session_id: string; message: string; skill?: string }) =>
    fetch(`${BACKEND}/api/chat/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
};
