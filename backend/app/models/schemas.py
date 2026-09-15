"""Pydantic v2 request/response schemas."""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import uuid


class SessionCreate(BaseModel):
    title: Optional[str] = "New conversation"
    llm_provider: Optional[str] = "ollama"
    llm_model: Optional[str] = "llama3.1:8b"


class SessionResponse(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime
    llm_provider: Optional[str]
    llm_model: Optional[str]

    model_config = {"from_attributes": True}


class Source(BaseModel):
    episode_title: str
    source_file: str
    chunk_index: int
    distance: Optional[float] = None


class MessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    sources: Optional[list[Source]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    skill: Optional[Literal["ship30", "artifact_markdown", "artifact_html"]] = None


class ArtifactResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    artifact_type: str
    title: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    status: str
    environment: str
    llm_provider: str
    llm_model: str
    database: str
    vector_store: str
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
