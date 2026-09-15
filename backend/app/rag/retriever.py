"""ChromaDB retriever with Ollama embeddings."""
import httpx
import chromadb
from chromadb.config import Settings
from app.config import settings
import structlog

log = structlog.get_logger()

_retriever_instance = None


class Retriever:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name="lenny_transcripts",
            metadata={"hnsw:space": "cosine"},
        )

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Get embeddings from Ollama."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            embeddings = []
            for text in texts:
                resp = await client.post(
                    f"{settings.ollama_base_url}/api/embeddings",
                    json={"model": settings.ollama_embed_model, "prompt": text},
                )
                resp.raise_for_status()
                data = resp.json()
                embeddings.append(data["embedding"])
            return embeddings

    async def search(self, query: str, n_results: int = 5) -> list[dict]:
        """Search for relevant transcript chunks."""
        try:
            count = self.collection.count()
            if count == 0:
                return []
            
            embeddings = await self.embed_texts([query])
            results = self.collection.query(
                query_embeddings=embeddings,
                n_results=min(n_results, count),
                include=["documents", "metadatas", "distances"],
            )
            
            chunks = []
            if results["documents"] and results["documents"][0]:
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                ):
                    chunks.append({
                        "text": doc,
                        "source_file": meta.get("source_file", ""),
                        "episode_title": meta.get("episode_title", "Unknown Episode"),
                        "chunk_index": meta.get("chunk_index", 0),
                        "distance": dist,
                    })
            return chunks
        except Exception as e:
            log.error("retriever_search_error", error=str(e))
            return []

    def collection_stats(self) -> dict:
        try:
            return {"count": self.collection.count()}
        except Exception:
            return {"count": 0}


def get_retriever() -> Retriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = Retriever()
    return _retriever_instance
