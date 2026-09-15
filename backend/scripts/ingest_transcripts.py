"""
Ingest Lenny's Podcast transcripts into ChromaDB vector store.
Run with: docker compose exec backend python scripts/ingest_transcripts.py
"""
import asyncio
import os
import sys
from pathlib import Path

# Add /app to path so we can import app modules
sys.path.insert(0, "/app")

import yaml
import structlog

log = structlog.get_logger()

TRANSCRIPTS_DIR = Path("/app/data/transcripts/episodes")
CHUNK_SIZE = 1000      # characters per chunk
CHUNK_OVERLAP = 150    # overlap between chunks


def parse_transcript(filepath: Path) -> dict | None:
    """Parse a transcript markdown file with YAML frontmatter."""
    try:
        text = filepath.read_text(encoding="utf-8")
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                meta = yaml.safe_load(parts[1]) or {}
                content = parts[2].strip()
            else:
                meta = {}
                content = text
        else:
            meta = {}
            content = text

        if not content:
            return None

        return {
            "guest": meta.get("guest", filepath.parent.name),
            "title": meta.get("title", filepath.parent.name),
            "publish_date": str(meta.get("publish_date", "")),
            "content": content,
        }
    except Exception as e:
        log.warning("parse_error", file=str(filepath), error=str(e))
        return None


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


async def main():
    from app.rag.retriever import get_retriever

    if not TRANSCRIPTS_DIR.exists():
        log.error("transcripts_dir_not_found", path=str(TRANSCRIPTS_DIR))
        print(f"ERROR: {TRANSCRIPTS_DIR} not found. Make sure data/transcripts is mounted.")
        sys.exit(1)

    episode_dirs = sorted(TRANSCRIPTS_DIR.iterdir())
    log.info("ingestion_start", total_episodes=len(episode_dirs))
    print(f"\n🎙️  Ingesting {len(episode_dirs)} episodes into ChromaDB...\n")

    retriever = get_retriever()

    # Check existing count
    existing = retriever.collection.count()
    if existing > 0:
        print(f"⚠️  Collection already has {existing} chunks. Clearing and re-ingesting...\n")
        retriever.collection.delete(where={"guest": {"$ne": ""}})

    total_chunks = 0
    failed = 0

    for i, ep_dir in enumerate(episode_dirs):
        transcript_file = ep_dir / "transcript.md"
        if not transcript_file.exists():
            continue

        doc = parse_transcript(transcript_file)
        if not doc:
            failed += 1
            continue

        chunks = chunk_text(doc["content"])
        if not chunks:
            continue

        # Embed and store
        try:
            embeddings = await retriever.embed_texts(chunks)
            ids = [f"{ep_dir.name}_chunk_{j}" for j in range(len(chunks))]
            metadatas = [
                {
                    "guest": doc["guest"],
                    "title": doc["title"],
                    "publish_date": doc["publish_date"],
                    "episode": ep_dir.name,
                    "chunk_index": j,
                }
                for j in range(len(chunks))
            ]
            retriever.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=chunks,
                metadatas=metadatas,
            )
            total_chunks += len(chunks)
            print(f"  [{i+1}/{len(episode_dirs)}] ✓ {doc['guest']} — {len(chunks)} chunks")
        except Exception as e:
            log.warning("embed_error", episode=ep_dir.name, error=str(e))
            failed += 1

    print(f"\n✅ Ingestion complete!")
    print(f"   Episodes processed : {len(episode_dirs) - failed}")
    print(f"   Total chunks stored: {total_chunks}")
    print(f"   Failed             : {failed}")
    log.info("ingestion_complete", total_chunks=total_chunks, failed=failed)


if __name__ == "__main__":
    asyncio.run(main())
