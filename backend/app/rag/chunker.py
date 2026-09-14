import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Chunk:
    text: str
    source_file: str
    episode_title: str
    chunk_index: int

    def to_metadata(self) -> dict:
        return {
            "source_file": self.source_file,
            "episode_title": self.episode_title,
            "chunk_index": self.chunk_index,
        }


def infer_title(filename: str) -> str:
    stem = Path(filename).stem
    stem = re.sub(r"^\d+[-_]", "", stem)
    stem = re.sub(r"[-_]", " ", stem)
    return stem.strip().title()


def chunk_text(text: str, source_file: str, chunk_size: int = 1800, overlap: int = 300) -> list[Chunk]:
    title = infer_title(source_file)
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, current, idx = [], "", 0
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(current) + len(s) + 1 > chunk_size and current:
            chunks.append(Chunk(text=current.strip(), source_file=source_file, episode_title=title, chunk_index=idx))
            idx += 1
            current = current[-overlap:] + " " + s
        else:
            current = (current + " " + s).strip()
    if current.strip():
        chunks.append(Chunk(text=current.strip(), source_file=source_file, episode_title=title, chunk_index=idx))
    return chunks


def load_and_chunk(filepath: Path) -> list[Chunk]:
    text = filepath.read_text(encoding="utf-8", errors="replace").strip()
    if len(text) < 200:
        return []
    return chunk_text(text, source_file=filepath.name)
