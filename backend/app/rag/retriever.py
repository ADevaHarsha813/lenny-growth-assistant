"""
ChromaDB-based semantic retriever for Lenny's transcript chunks.
Embeddings generated via Ollama (nomic-embed-text) or fallback to simple TF-IDF.
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
import httpx
import structlog
from app.config import settings

logger = structlog.get_logger()

COLLECTION_NAME = "lenny_transcripts"
_client = None
_collection = None


def _get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_collection():
    global _collection
    if _collection is None:
        client = _get_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Get embeddings from Ollama nomic-embed-text."""
    embeddings = []
    async with httpx.AsyncClient(timeout=60.0) as client:
        for text in texts:
            resp = await client.post(
                f"{settings.ollama_base_url}/api/embeddings",
                json={"model": settings.ollama_embed_model, "prompt": text},
            )
            resp.raise_for_status()
            embeddings.append(resp.json()["embedding"])
    return embeddings


async def search(query: str, n_results: int = 5) -> list[dict]:
    """
    Semantic search over transcript chunks.
    Returns list of {text, source_file, episode_title, chunk_index, distance}.
    """
    collection = get_collection()
    count = collection.count()
    if count == 0:
        logger.warning("retriever.empty_collection", hint="Run the ingestion script first")
        return []

    try:
        query_embedding = await embed_texts([query])
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=min(n_results, count),
            include=["documents", "metadatas", "distances"],
        )
        hits = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            hits.append({
                "text": doc,
                "source_file": meta.get("source_file", "unknown"),
                "episode_title": meta.get("episode_title", "Unknown Episode"),
                "chunk_index": meta.get("chunk_index", 0),
                "distance": round(dist, 4),
            })
        logger.info("retriever.search", query=query[:60], hits=len(hits))
        return hits
    except Exception as e:
        logger.error("retriever.search_failed", error=str(e))
        return []


def collection_stats() -> dict:
    try:
        col = get_collection()
        return {"count": col.count(), "name": COLLECTION_NAME}
    except Exception as e:
        return {"count": 0, "error": str(e)}
