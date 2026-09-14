#!/usr/bin/env python3
"""
One-time CLI script to ingest Lenny's Podcast transcripts into ChromaDB.

Usage (from project root):
    python scripts/ingest_transcripts.py
    python scripts/ingest_transcripts.py --reset    # wipe and re-index
    python scripts/ingest_transcripts.py --dir data/transcripts
"""
import asyncio
import argparse
import sys
from pathlib import Path

# Allow imports from backend/app
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.rag.ingest import ingest_directory
import structlog

logger = structlog.get_logger()


async def main():
    parser = argparse.ArgumentParser(description="Ingest Lenny transcripts into ChromaDB")
    parser.add_argument("--dir", default="data/transcripts", help="Path to transcripts folder")
    parser.add_argument("--reset", action="store_true", help="Wipe existing index first")
    args = parser.parse_args()

    transcripts_dir = Path(args.dir)
    if not transcripts_dir.exists():
        print(f"❌ Directory not found: {transcripts_dir}")
        print("   Clone the transcripts repo first:")
        print("   git clone https://github.com/ChatPRD/lennys-podcast-transcripts data/transcripts")
        sys.exit(1)

    print(f"📂 Ingesting from: {transcripts_dir.resolve()}")
    print(f"🔄 Reset: {args.reset}")
    print("⏳ This may take several minutes on first run...")

    result = await ingest_directory(transcripts_dir, reset=args.reset)

    print(f"\n✅ Ingestion complete!")
    print(f"   Files processed : {result['files']}")
    print(f"   Total chunks    : {result['chunks']}")
    print(f"   New chunks added: {result.get('new', 0)}")


if __name__ == "__main__":
    asyncio.run(main())
