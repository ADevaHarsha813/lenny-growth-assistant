"""Chat API — SSE streaming endpoint."""
import json
import re
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.db import Session, Message, Artifact
from app.models.schemas import ChatRequest
from app.agents.orchestrator import run_agent
import structlog

log = structlog.get_logger()
router = APIRouter(prefix="/api/chat", tags=["chat"])


def _generate_title(message: str) -> str:
    """Generate a concise title from the first user message."""
    # Strip question marks and common filler words
    cleaned = re.sub(r'[?!]+$', '', message.strip())
    words = cleaned.split()
    # Take first 7 words max
    title = ' '.join(words[:7])
    if len(words) > 7:
        title += '…'
    # Capitalize first letter
    return title[:80].capitalize() if title else "New conversation"


@router.post("/{session_id}")
async def chat(
    session_id: str,
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    # Verify session exists
    result = await db.execute(
        select(Session).where(Session.id == uuid.UUID(session_id))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check if this is the first message (for auto-title)
    msg_count_result = await db.execute(
        select(func.count(Message.id)).where(Message.session_id == uuid.UUID(session_id))
    )
    is_first_message = (msg_count_result.scalar() or 0) == 0

    # Save user message
    user_msg = Message(
        id=uuid.uuid4(),
        session_id=uuid.UUID(session_id),
        role="user",
        content=body.message,
    )
    db.add(user_msg)

    # Auto-title on first message
    if is_first_message and session.title in ("New conversation", ""):
        session.title = _generate_title(body.message)

    await db.commit()

    # Load message history
    history_result = await db.execute(
        select(Message)
        .where(Message.session_id == uuid.UUID(session_id))
        .order_by(Message.created_at)
    )
    all_messages = history_result.scalars().all()
    messages = [
        {"role": m.role, "content": m.content}
        for m in all_messages
    ]

    async def event_stream():
        full_text = ""
        artifact_data = None

        try:
            async for chunk in run_agent(
                messages=messages,
                session_id=session_id,
                skill=body.skill,
            ):
                yield chunk
                if chunk.startswith("data: "):
                    try:
                        payload = json.loads(chunk[6:])
                        if payload.get("type") == "text":
                            full_text += payload.get("delta", "")
                        elif payload.get("type") == "artifact":
                            artifact_data = payload.get("artifact")
                    except Exception:
                        pass
        except Exception as e:
            log.error("stream_error", error=str(e))
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            return

        # Save assistant message and artifact to DB
        if full_text or artifact_data:
            from app.database import async_session_maker
            async with async_session_maker() as save_db:
                if full_text:
                    assistant_msg = Message(
                        id=uuid.uuid4(),
                        session_id=uuid.UUID(session_id),
                        role="assistant",
                        content=full_text,
                    )
                    save_db.add(assistant_msg)

                if artifact_data:
                    artifact = Artifact(
                        id=uuid.uuid4(),
                        session_id=uuid.UUID(session_id),
                        artifact_type=artifact_data.get("type", "markdown"),
                        title=artifact_data.get("title", "Artifact"),
                        content=artifact_data.get("content", ""),
                    )
                    save_db.add(artifact)

                await save_db.commit()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
