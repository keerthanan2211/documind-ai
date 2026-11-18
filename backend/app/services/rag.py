"""
Retrieval-augmented generation: find the passages most similar to the question,
then ask the model to answer ONLY from those passages and cite them by number.
"""

import re
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Chunk, Message

SYSTEM_PROMPT = """You answer questions about a single document using only the numbered sources provided.

Rules:
- Use only facts from the sources. Do not use outside knowledge.
- Cite every claim with the source number in square brackets, like [1] or [2][3].
- If the sources don't contain the answer, say exactly: "I couldn't find that in this document."
- Be concise and plain. Use short paragraphs or a brief list when it helps."""

NOT_FOUND = "I couldn't find that in this document."


def retrieve(
    db: Session, document_id: uuid.UUID, query_vector: list[float], k: int, max_distance: float
) -> list[Chunk]:
    distance = Chunk.embedding.cosine_distance(query_vector)
    rows = db.execute(
        select(Chunk, distance.label("distance")).where(Chunk.document_id == document_id).order_by(distance).limit(k)
    ).all()
    return [chunk for chunk, dist in rows if dist <= max_distance]


def build_prompt(question: str, chunks: list[Chunk], history: list[Message]) -> str:
    sources = "\n\n".join(f"[{i}] (page {c.page})\n{c.content}" for i, c in enumerate(chunks, start=1))
    # A few recent turns let follow-ups like "what about the second one?" make sense
    recent = "\n".join(f"{m.role.upper()}: {m.content}" for m in history[-4:])
    parts = [f"SOURCES:\n{sources}"]
    if recent:
        parts.append(f"EARLIER IN THIS CONVERSATION:\n{recent}")
    parts.append(f"QUESTION: {question}")
    return "\n\n".join(parts)


def cited_numbers(answer: str) -> set[int]:
    return {int(n) for n in re.findall(r"\[(\d+)\]", answer)}


def make_sources(answer: str, chunks: list[Chunk], excerpt_len: int = 280) -> list[dict]:
    """Returns only the sources the answer actually cited, with a short excerpt for display."""
    used = cited_numbers(answer)
    sources = []
    for number, chunk in enumerate(chunks, start=1):
        if number in used:
            text = chunk.content
            excerpt = text if len(text) <= excerpt_len else text[:excerpt_len].rsplit(" ", 1)[0] + "…"
            sources.append({"number": number, "page": chunk.page, "excerpt": excerpt})
    return sources
