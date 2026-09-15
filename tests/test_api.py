"""
Tests for FastAPI endpoints — sessions, chat, artifacts, health.
Run with: pytest tests/ -v
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
import json

# Import the FastAPI app
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


# ─────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────

@pytest.mark.anyio
async def test_health_returns_ok(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "provider" in body


# ─────────────────────────────────────────────
# Sessions
# ─────────────────────────────────────────────

@pytest.mark.anyio
async def test_create_session(client):
    resp = await client.post("/api/sessions", json={"title": "Test Session"})
    assert resp.status_code == 200
    body = resp.json()
    assert "id" in body
    assert body["title"] == "Test Session"


@pytest.mark.anyio
async def test_list_sessions(client):
    # Create a session first
    await client.post("/api/sessions", json={"title": "List Test"})
    resp = await client.get("/api/sessions")
    assert resp.status_code == 200
    sessions = resp.json()
    assert isinstance(sessions, list)


@pytest.mark.anyio
async def test_get_session_not_found(client):
    resp = await client.get("/api/sessions/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_create_and_get_session(client):
    create_resp = await client.post("/api/sessions", json={"title": "Get Test"})
    session_id = create_resp.json()["id"]

    get_resp = await client.get(f"/api/sessions/{session_id}")
    assert get_resp.status_code == 200
    body = get_resp.json()
    assert body["id"] == session_id
    assert "messages" in body


@pytest.mark.anyio
async def test_update_session_title(client):
    create_resp = await client.post("/api/sessions", json={"title": "Old Title"})
    session_id = create_resp.json()["id"]

    patch_resp = await client.patch(
        f"/api/sessions/{session_id}", json={"title": "New Title"}
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["title"] == "New Title"


@pytest.mark.anyio
async def test_delete_session(client):
    create_resp = await client.post("/api/sessions", json={"title": "To Delete"})
    session_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/sessions/{session_id}")
    assert del_resp.status_code == 200

    # Verify gone
    get_resp = await client.get(f"/api/sessions/{session_id}")
    assert get_resp.status_code == 404


# ─────────────────────────────────────────────
# Chat
# ─────────────────────────────────────────────

@pytest.mark.anyio
async def test_chat_missing_session(client):
    resp = await client.post(
        "/api/chat/00000000-0000-0000-0000-000000000000",
        json={"message": "Hello", "skill": None},
    )
    assert resp.status_code == 404


@pytest.mark.anyio
@patch("app.agents.orchestrator.run_agent")
async def test_chat_streams_sse(mock_run_agent, client):
    """Chat endpoint should return SSE stream with text_delta events."""

    async def fake_stream(*args, **kwargs):
        yield "data: " + json.dumps({"type": "text_delta", "delta": "Hello"}) + "\n\n"
        yield "data: " + json.dumps({"type": "done", "message_id": "test-id"}) + "\n\n"

    mock_run_agent.return_value = fake_stream()

    create_resp = await client.post("/api/sessions", json={"title": "Chat Test"})
    session_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/chat/{session_id}",
        json={"message": "What is PLG?", "skill": None},
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")


@pytest.mark.anyio
async def test_chat_validates_message_length(client):
    create_resp = await client.post("/api/sessions", json={"title": "Validation Test"})
    session_id = create_resp.json()["id"]

    # Message too long (>4000 chars)
    resp = await client.post(
        f"/api/chat/{session_id}",
        json={"message": "x" * 5000, "skill": None},
    )
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_chat_invalid_skill(client):
    create_resp = await client.post("/api/sessions", json={"title": "Skill Test"})
    session_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/chat/{session_id}",
        json={"message": "test", "skill": "invalid_skill_name"},
    )
    assert resp.status_code == 422


# ─────────────────────────────────────────────
# Artifacts
# ─────────────────────────────────────────────

@pytest.mark.anyio
async def test_list_artifacts_empty(client):
    create_resp = await client.post("/api/sessions", json={"title": "Artifact Test"})
    session_id = create_resp.json()["id"]

    resp = await client.get(f"/api/artifacts/{session_id}")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.anyio
async def test_get_artifact_not_found(client):
    create_resp = await client.post("/api/sessions", json={"title": "ArtTest"})
    session_id = create_resp.json()["id"]

    resp = await client.get(
        f"/api/artifacts/{session_id}/00000000-0000-0000-0000-000000000000"
    )
    assert resp.status_code == 404
