"""Sessions API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.db import Session, Message, Artifact
from app.models.schemas import SessionCreate, SessionResponse, MessageResponse, ArtifactResponse
from pydantic import BaseModel
import uuid

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class SessionUpdate(BaseModel):
    title: str


@router.post("", response_model=SessionResponse)
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)):
    session = Session(
        id=uuid.uuid4(),
        title=body.title or "New conversation",
        llm_provider=body.llm_provider or "ollama",
        llm_model=body.llm_model or "llama3.1:8b",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("", response_model=list[SessionResponse])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Session).order_by(desc(Session.updated_at)).limit(50)
    )
    return result.scalars().all()


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).where(Session.id == uuid.UUID(session_id)))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/{session_id}", response_model=SessionResponse)
async def rename_session(session_id: str, body: SessionUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).where(Session.id == uuid.UUID(session_id)))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    session.title = title[:120]
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/{session_id}/messages", response_model=list[MessageResponse])
async def get_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Message)
        .where(Message.session_id == uuid.UUID(session_id))
        .order_by(Message.created_at)
    )
    return result.scalars().all()


@router.get("/{session_id}/artifacts", response_model=list[ArtifactResponse])
async def get_session_artifacts(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Artifact)
        .where(Artifact.session_id == uuid.UUID(session_id))
        .order_by(desc(Artifact.created_at))
    )
    return result.scalars().all()


@router.delete("/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).where(Session.id == uuid.UUID(session_id)))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
    await db.commit()
    return {"ok": True}
