from pydantic import BaseModel, Field
from typing import Optional, Literal, Any
from datetime import datetime
from uuid import UUID


# ─── Session ─────────────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    title: Optional[str] = None
    llm_provider: Literal["anthropic", "ollama"] = "ollama"


class SessionResponse(BaseModel):
    id: UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    llm_provider: str
    llm_model: Optional[str]
    message_count: int = 0

    model_config = {"from_attributes": True}


# ─── Message ──────────────────────────────────────────────────────────────────

class Source(BaseModel):
    title: str
    excerpt: str
    chunk_index: Optional[int] = None


class MessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    sources: Optional[list[Source]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: UUID
    message: str = Field(..., min_length=1, max_length=4000)
    skill: Optional[Literal["ship30", "artifact_markdown", "artifact_html"]] = None


# ─── Artifact ─────────────────────────────────────────────────────────────────

class ArtifactResponse(BaseModel):
    id: UUID
    session_id: UUID
    artifact_type: str
    title: Optional[str]
    content: str
    created_at: datetime
    sources: Optional[list[Source]] = None

    model_config = {"from_attributes": True}


# ─── Health ───────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    environment: str
    llm_provider: str
    llm_model: str
    database: str
    vector_store: str


# ─── Error ────────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[Any] = None
    code: Optional[str] = None
