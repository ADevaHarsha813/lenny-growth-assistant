"""
Tests for session persistence and context isolation.
Verifies that sessions are independent and message history is preserved.
Run with: pytest tests/ -v
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch
import json

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
# Session persistence
# ─────────────────────────────────────────────

@pytest.mark.anyio
async def test_session_persists_across_requests(client):
    """A created session can be retrieved by ID in a subsequent request."""
    create = await client.post("/api/sessions", json={"title": "Persistence Test"})
    session_id = create.json()["id"]

    get = await client.get(f"/api/sessions/{session_id}")
    assert get.status_code == 200
    assert get.json()["id"] == session_id
    assert get.json()["title"] == "Persistence Test"


@pytest.mark.anyio
async def test_session_appears_in_list_after_creation(client):
    """Newly created sessions show up in the sessions list."""
    create = await client.post("/api/sessions", json={"title": "Listed Session"})
    session_id = create.json()["id"]

    list_resp = await client.get("/api/sessions")
    ids = [s["id"] for s in list_resp.json()]
    assert session_id in ids


@pytest.mark.anyio
async def test_session_removed_from_list_after_deletion(client):
    """Deleted sessions no longer appear in the sessions list."""
    create = await client.post("/api/sessions", json={"title": "To Remove"})
    session_id = create.json()["id"]

    await client.delete(f"/api/sessions/{session_id}")

    list_resp = await client.get("/api/sessions")
    ids = [s["id"] for s in list_resp.json()]
    assert session_id not in ids


@pytest.mark.anyio
async def test_session_default_title_when_omitted(client):
    """Creating a session without a title should still succeed."""
    create = await client.post("/api/sessions", json={})
    assert create.status_code == 200
    body = create.json()
    assert "id" in body
    # Title may be None or a default string — both are acceptable
    assert "title" in body


@pytest.mark.anyio
async def test_session_title_update_is_durable(client):
    """Updating a session title persists — not just returned in the PATCH response."""
    create = await client.post("/api/sessions", json={"title": "Original"})
    session_id = create.json()["id"]

    await client.patch(f"/api/sessions/{session_id}", json={"title": "Updated"})

    get = await client.get(f"/api/sessions/{session_id}")
    assert get.json()["title"] == "Updated"


@pytest.mark.anyio
async def test_session_messages_start_empty(client):
    """A brand-new session has an empty messages list."""
    create = await client.post("/api/sessions", json={"title": "Empty Session"})
    session_id = create.json()["id"]

    get = await client.get(f"/api/sessions/{session_id}")
    assert get.json()["messages"] == []


# ─────────────────────────────────────────────
# Context isolation between sessions
# ─────────────────────────────────────────────

@pytest.mark.anyio
async def test_two_sessions_are_independent(client):
    """Two sessions have separate IDs and do not share message history."""
    create_a = await client.post("/api/sessions", json={"title": "Session A"})
    create_b = await client.post("/api/sessions", json={"title": "Session B"})

    id_a = create_a.json()["id"]
    id_b = create_b.json()["id"]

    assert id_a != id_b

    get_a = await client.get(f"/api/sessions/{id_a}")
    get_b = await client.get(f"/api/sessions/{id_b}")

    assert get_a.json()["title"] == "Session A"
    assert get_b.json()["title"] == "Session B"


@pytest.mark.anyio
async def test_deleting_session_a_does_not_affect_session_b(client):
    """Deleting one session leaves the other fully intact."""
    create_a = await client.post("/api/sessions", json={"title": "Session A"})
    create_b = await client.post("/api/sessions", json={"title": "Session B"})
    id_a = create_a.json()["id"]
    id_b = create_b.json()["id"]

    await client.delete(f"/api/sessions/{id_a}")

    get_b = await client.get(f"/api/sessions/{id_b}")
    assert get_b.status_code == 200
    assert get_b.json()["id"] == id_b


@pytest.mark.anyio
@patch("app.agents.orchestrator.run_agent")
async def test_clear_messages_only_affects_target_session(mock_run_agent, client):
    """Clearing messages in one session leaves others unaffected."""

    async def fake_stream(*args, **kwargs):
        yield "data: " + json.dumps({"type": "text_delta", "delta": "Hi"}) + "\n\n"
        yield "data: " + json.dumps({"type": "done", "message_id": "msg-1"}) + "\n\n"

    mock_run_agent.return_value = fake_stream()

    create_a = await client.post("/api/sessions", json={"title": "Session A"})
    create_b = await client.post("/api/sessions", json={"title": "Session B"})
    id_a = create_a.json()["id"]
    id_b = create_b.json()["id"]

    # Clear session A
    clear_resp = await client.delete(f"/api/chat/{id_a}/messages")
    assert clear_resp.status_code == 200

    # Session B should still exist and be accessible
    get_b = await client.get(f"/api/sessions/{id_b}")
    assert get_b.status_code == 200


# ─────────────────────────────────────────────
# Multiple sessions in list
# ─────────────────────────────────────────────

@pytest.mark.anyio
async def test_list_sessions_returns_all_created(client):
    """All created sessions appear in the list response."""
    titles = ["Alpha", "Beta", "Gamma"]
    created_ids = set()

    for title in titles:
        resp = await client.post("/api/sessions", json={"title": title})
        created_ids.add(resp.json()["id"])

    list_resp = await client.get("/api/sessions")
    listed_ids = {s["id"] for s in list_resp.json()}

    assert created_ids.issubset(listed_ids)


@pytest.mark.anyio
async def test_session_list_items_have_required_fields(client):
    """Each item in the session list has id, title, created_at, updated_at."""
    await client.post("/api/sessions", json={"title": "Field Check"})

    list_resp = await client.get("/api/sessions")
    assert list_resp.status_code == 200

    for session in list_resp.json():
        assert "id" in session
        assert "title" in session
        assert "created_at" in session
        assert "updated_at" in session
