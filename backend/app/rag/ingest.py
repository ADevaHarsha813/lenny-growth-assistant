"""
Ingestion pipeline: loads transcripts → chunks → embeds → stores in ChromaDB.
Called by scripts/ingest_transcripts.py
"""
import asyncio
from pathlib import Path
import httpx
import structlog
from app.rag.chunker import load_and_chunk, Chunk
from app.rag.retriever import get_collection, embed_texts
from app.config import settings

logger = structlog.get_logger()

TRANSCRIPT_EXTENSIONS = {".txt", ".md"}
BATCH_SIZE = 10  # embed N chunks at a time


async def ingest_directory(transcripts_dir: Path, reset: bool = False) -> dict:
    """
    Main ingestion entry point.
    - transcripts_dir: path to folder with transcript files
    - reset: if True, drops existing collection first
    """
    collection = get_collection()

    if reset:
        from app.rag.retriever import _get_client, COLLECTION_NAME
        client = _get_client()
        try:
            client.delete_collection(COLLECTION_NAME)
            logger.info("ingest.collection_reset")
        except Exception:
            pass
        # Re-create
        from app.rag import retriever as ret
        ret._collection = None
        collection = get_collection()

    files = [
        f for f in transcripts_dir.rglob("*")
        if f.suffix.lower() in TRANSCRIPT_EXTENSIONS and f.is_file()
    ]

    if not files:
        logger.warning("ingest.no_files_found", dir=str(transcripts_dir))
        return {"files": 0, "chunks": 0}

    logger.info("ingest.start", file_count=len(files))

    all_chunks: list[Chunk] = []
    for f in files:
        chunks = load_and_chunk(f)
        all_chunks.extend(chunks)
        logger.info("ingest.file_chunked", file=f.name, chunks=len(chunks))

    logger.info("ingest.total_chunks", count=len(all_chunks))

    # Check which chunks already exist (skip re-embedding)
    existing_ids = set()
    try:
        existing = collection.get(include=[])
        existing_ids = set(existing["ids"])
    except Exception:
        pass

    new_chunks = []
    for chunk in all_chunks:
        cid = f"{chunk.source_file}::{chunk.chunk_index}"
        if cid not in existing_ids:
            new_chunks.append((cid, chunk))

    if not new_chunks:
        logger.info("ingest.already_up_to_date")
        return {"files": len(files), "chunks": len(all_chunks), "new": 0}

    logger.info("ingest.embedding_new_chunks", count=len(new_chunks))

    # Batch embed
    added = 0
    for i in range(0, len(new_chunks), BATCH_SIZE):
        batch = new_chunks[i : i + BATCH_SIZE]
        ids = [b[0] for b in batch]
        texts = [b[1].text for b in batch]
        metadatas = [b[1].to_metadata() for b in batch]

        try:
            embeddings = await embed_texts(texts)
            collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
            added += len(batch)
            logger.info("ingest.batch_done", progress=f"{i+len(batch)}/{len(new_chunks)}")
        except Exception as e:
            logger.error("ingest.batch_failed", error=str(e), batch_start=i)

    return {"files": len(files), "chunks": len(all_chunks), "new": added}
