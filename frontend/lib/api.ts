const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BACKEND}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || err.detail || res.statusText);
  }
  return res.json();
}

export const api = {
  createSession: (body: { title?: string; llm_provider?: string }) =>
    apiFetch<any>("/api/sessions", { method: "POST", body: JSON.stringify(body) }),

  getSessions: () => apiFetch<any[]>("/api/sessions"),

  getSession: (id: string) => apiFetch<any>(`/api/sessions/${id}`),

  renameSession: (id: string, title: string) =>
    apiFetch<any>(`/api/sessions/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    }),

  getMessages: (sessionId: string) =>
    apiFetch<any[]>(`/api/sessions/${sessionId}/messages`),

  getArtifacts: (sessionId: string) =>
    apiFetch<any[]>(`/api/sessions/${sessionId}/artifacts`),

  deleteSession: (id: string) =>
    apiFetch<any>(`/api/sessions/${id}`, { method: "DELETE" }),

  getHealth: () => apiFetch<any>("/health"),

  streamChat: (sessionId: string, body: { message: string; skill?: string }) =>
    fetch(`${BACKEND}/api/chat/${sessionId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
};
