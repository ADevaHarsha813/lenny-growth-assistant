export type LLMProvider = "anthropic" | "ollama";
export type ArtifactType = "markdown" | "html" | "ship30";
export type MessageRole = "user" | "assistant";
export type Skill = "ship30" | "artifact_markdown" | "artifact_html";

export interface Source {
  episode_title: string;
  source_file: string;
  chunk_index: number;
  distance?: number;
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
  title: string;
  created_at: string;
  updated_at: string;
  llm_provider: LLMProvider;
  llm_model: string;
}

export interface Artifact {
  id: string;
  session_id: string;
  artifact_type: ArtifactType;
  title: string;
  content: string;
  created_at: string;
}

export interface ChatStreamEvent {
  type: "text" | "tool_start" | "tool_end" | "artifact" | "error" | "done";
  delta?: string;
  tool?: string;
  input?: Record<string, unknown>;
  artifact?: Artifact;
  message?: string;
}
