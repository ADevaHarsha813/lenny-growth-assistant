"""
Tests for RAG retrieval layer (ChromaDB vector search).
These tests mock ChromaDB to run without a live vector store.
Run with: pytest tests/ -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ─────────────────────────────────────────────
# Helpers / fixtures
# ─────────────────────────────────────────────

def make_chroma_result(n=5, score_start=0.12):
    """Return a fake ChromaDB query result dict."""
    ids = [[f"chunk-{i}" for i in range(n)]]
    documents = [[f"Transcript excerpt {i} about PLG and growth." for i in range(n)]]
    metadatas = [[
        {
            "source_file": f"ep{100+i}.txt",
            "episode_title": f"Episode {100+i}: Growth Tactics with Guest {i}",
            "chunk_index": i,
        }
        for i in range(n)
    ]]
    # ChromaDB returns L2 distances; lower = more similar
    distances = [[score_start + i * 0.05 for i in range(n)]]
    return {
        "ids": ids,
        "documents": documents,
        "metadatas": metadatas,
        "distances": distances,
    }


# ─────────────────────────────────────────────
# Import the retriever under test
# ─────────────────────────────────────────────

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


# ─────────────────────────────────────────────
# Basic retrieval
# ─────────────────────────────────────────────

@patch("app.rag.retriever.chroma_collection")
@patch("app.rag.retriever.embed_text")
def test_query_returns_n_results(mock_embed, mock_collection):
    """Retriever returns exactly n_results chunks."""
    from app.rag.retriever import query

    mock_embed.return_value = [0.1] * 768
    mock_collection.query.return_value = make_chroma_result(n=5)

    results = query("What is PLG?", n_results=5)

    assert len(results) == 5
    mock_collection.query.assert_called_once()


@patch("app.rag.retriever.chroma_collection")
@patch("app.rag.retriever.embed_text")
def test_query_result_has_required_fields(mock_embed, mock_collection):
    """Each result chunk includes content, episode_title, source_file, score."""
    from app.rag.retriever import query

    mock_embed.return_value = [0.1] * 768
    mock_collection.query.return_value = make_chroma_result(n=3)

    results = query("PLG strategy", n_results=3)

    for r in results:
        assert "content" in r, "Missing 'content' field"
        assert "episode_title" in r, "Missing 'episode_title' field"
        assert "source_file" in r, "Missing 'source_file' field"
        assert "score" in r, "Missing 'score' field"


@patch("app.rag.retriever.chroma_collection")
@patch("app.rag.retriever.embed_text")
def test_query_score_is_similarity_not_distance(mock_embed, mock_collection):
    """Score should be a similarity measure in [0, 1] (higher = more similar)."""
    from app.rag.retriever import query

    mock_embed.return_value = [0.1] * 768
    mock_collection.query.return_value = make_chroma_result(n=3, score_start=0.1)

    results = query("churn reduction", n_results=3)

    for r in results:
        assert 0.0 <= r["score"] <= 1.0, f"Score {r['score']} out of range"

    # First result should have highest score (closest match)
    assert results[0]["score"] >= results[-1]["score"]


@patch("app.rag.retriever.chroma_collection")
@patch("app.rag.retriever.embed_text")
def test_query_returns_fewer_when_collection_small(mock_embed, mock_collection):
    """If fewer chunks exist than n_results, return what's available."""
    from app.rag.retriever import query

    mock_embed.return_value = [0.1] * 768
    mock_collection.query.return_value = make_chroma_result(n=2)

    results = query("retention", n_results=5)

    assert len(results) == 2


# ─────────────────────────────────────────────
# Edge cases
# ─────────────────────────────────────────────

@patch("app.rag.retriever.chroma_collection")
@patch("app.rag.retriever.embed_text")
def test_empty_query_handled_gracefully(mock_embed, mock_collection):
    """Empty string query should not raise; returns empty list or minimal results."""
    from app.rag.retriever import query

    mock_embed.return_value = [0.0] * 768
    mock_collection.query.return_value = make_chroma_result(n=0)

    results = query("", n_results=5)

    assert isinstance(results, list)


@patch("app.rag.retriever.chroma_collection")
@patch("app.rag.retriever.embed_text")
def test_query_propagates_episode_title_from_metadata(mock_embed, mock_collection):
    """Episode title in metadata is correctly passed through to result."""
    from app.rag.retriever import query

    mock_embed.return_value = [0.1] * 768
    fake_result = {
        "ids": [["chunk-0"]],
        "documents": [["Transcript text about activation rates."]],
        "metadatas": [[{
            "source_file": "ep42.txt",
            "episode_title": "Episode 42: Activation with Leah Tharin",
            "chunk_index": 0,
        }]],
        "distances": [[0.15]],
    }
    mock_collection.query.return_value = fake_result

    results = query("activation", n_results=1)

    assert results[0]["episode_title"] == "Episode 42: Activation with Leah Tharin"
    assert results[0]["source_file"] == "ep42.txt"
    assert "activation" in results[0]["content"].lower()


@patch("app.rag.retriever.chroma_collection")
@patch("app.rag.retriever.embed_text")
def test_query_calls_embed_with_exact_text(mock_embed, mock_collection):
    """The query text is passed verbatim to the embedding model."""
    from app.rag.retriever import query

    mock_embed.return_value = [0.1] * 768
    mock_collection.query.return_value = make_chroma_result(n=1)

    query("How do I improve NPS scores?", n_results=3)

    mock_embed.assert_called_once_with("How do I improve NPS scores?")


@patch("app.rag.retriever.chroma_collection")
@patch("app.rag.retriever.embed_text")
def test_query_n_results_passed_to_chroma(mock_embed, mock_collection):
    """n_results value is forwarded to ChromaDB."""
    from app.rag.retriever import query

    mock_embed.return_value = [0.1] * 768
    mock_collection.query.return_value = make_chroma_result(n=3)

    query("growth loops", n_results=3)

    call_kwargs = mock_collection.query.call_args
    # n_results should appear in either positional or keyword args
    assert call_kwargs is not None
    combined = {**call_kwargs.kwargs}
    if call_kwargs.args:
        combined["query_embeddings"] = call_kwargs.args[0]
    assert combined.get("n_results") == 3 or 3 in call_kwargs.args
