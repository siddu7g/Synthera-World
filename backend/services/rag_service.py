"""Lightweight local RAG service for chat context retrieval."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RagChunk:
    source: str
    text: str
    tokens: set[str]


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-zA-Z0-9_]+", text.lower()) if len(t) > 2}


class RagService:
    """Loads local docs and retrieves top-k chunks by token overlap."""

    def __init__(self, docs_dir: str | None = None) -> None:
        base = docs_dir or os.getenv("RAG_DOCS_DIR", "../rag")
        self.docs_dir = Path(base).expanduser().resolve()
        self.chunks: list[RagChunk] = []

    def load(self) -> None:
        """Load .md/.txt docs into in-memory chunks."""
        self.chunks = []
        if not self.docs_dir.exists():
            return

        for path in sorted(self.docs_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".md", ".txt"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            parts = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
            for part in parts:
                tokens = _tokenize(part)
                if not tokens:
                    continue
                self.chunks.append(
                    RagChunk(
                        source=str(path.relative_to(self.docs_dir)),
                        text=part,
                        tokens=tokens,
                    )
                )

    def retrieve(self, query: str, top_k: int = 4) -> list[RagChunk]:
        """Return best-matching chunks for a query."""
        query_tokens = _tokenize(query)
        if not query_tokens or not self.chunks:
            return []

        scored: list[tuple[int, RagChunk]] = []
        for chunk in self.chunks:
            score = len(query_tokens & chunk.tokens)
            if score > 0:
                scored.append((score, chunk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]


def format_rag_chunks_for_prompt(chunks: list[RagChunk]) -> str:
    """Join retrieved chunks for injection into a model user message."""
    if not chunks:
        return ""
    return "\n\n".join(f"[{c.source}]\n{c.text}" for c in chunks)


def merge_rag_chunks_unique(chunks: list[RagChunk], max_total: int) -> list[RagChunk]:
    """Deduplicate by (source, text), preserve order, cap length."""
    seen: set[tuple[str, str]] = set()
    out: list[RagChunk] = []
    for chunk in chunks:
        key = (chunk.source, chunk.text)
        if key in seen:
            continue
        seen.add(key)
        out.append(chunk)
        if len(out) >= max_total:
            break
    return out
