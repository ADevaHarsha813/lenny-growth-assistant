"""Artifacts API routes."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.db import Artifact
from app.models.schemas import ArtifactResponse

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


@router.get("", response_model=list[ArtifactResponse])
async def list_artifacts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Artifact).order_by(desc(Artifact.created_at)).limit(100)
    )
    return result.scalars().all()


@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(artifact_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Artifact).where(Artifact.id == uuid.UUID(artifact_id))
    )
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return artifact


@router.delete("/{artifact_id}")
async def delete_artifact(artifact_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Artifact).where(Artifact.id == uuid.UUID(artifact_id))
    )
    artifact = result.scalar_one_or_none()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    await db.delete(artifact)
    await db.commit()
    return {"ok": True}
