export type LLMProvider = "anthropic" | "ollama";
export type ArtifactType = "markdown" | "html" | "ship30";
export type MessageRole = "user" | "assistant";
export type Skill = "ship30" | "artifact_markdown" | "artifact_html";

export interface Source {
  title: string;
  excerpt: string;
  chunk_index?: number;
}

export interface Message {
  id: string;
  session_id: string;
  role: MessageRole;
  content: string;
  sources?: Source[];
  created_at: string;
}

export interface Session {
  id: string;
  title?: string;
  created_at: string;
  updated_at: string;
  llm_provider: LLMProvider;
  llm_model?: string;
  message_count: number;
}

export interface Artifact {
  id: string;
  session_id: string;
  artifact_type: ArtifactType;
  title?: string;
  content: string;
  created_at: string;
  sources?: Source[];
}

export interface ChatStreamEvent {
  type: "token" | "sources" | "artifact" | "done" | "error";
  content?: string;
  sources?: Source[];
  artifact?: Artifact;
  error?: string;
}
