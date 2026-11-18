"""
Splits page text into overlapping passages for embedding.

Passages break on paragraph or sentence boundaries where possible, so an answer's
source excerpt reads naturally, and each passage remembers which page it came from
so answers can cite page numbers.
"""

import re
from dataclasses import dataclass

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class TextChunk:
    page: int  # 1-based page number
    index: int  # position in the document
    content: str


def _normalise(text: str) -> str:
    text = re.sub(r"-\n(?=\w)", "", text)  # re-join words hyphenated across lines
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_units(text: str, size: int) -> list[str]:
    """Paragraphs, then sentences, then hard cuts, so no unit is longer than `size`."""
    units: list[str] = []
    for para in re.split(r"\n\s*\n", text):
        para = " ".join(para.split())
        if not para:
            continue
        if len(para) <= size:
            units.append(para)
            continue
        for sentence in _SENTENCE_END.split(para):
            while len(sentence) > size:
                cut = sentence.rfind(" ", 0, size)
                cut = cut if cut > size // 2 else size
                units.append(sentence[:cut].strip())
                sentence = sentence[cut:].strip()
            if sentence:
                units.append(sentence)
    return units


def chunk_pages(pages: list[str], size: int = 1200, overlap: int = 200) -> list[TextChunk]:
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")

    chunks: list[TextChunk] = []
    for page_number, raw in enumerate(pages, start=1):
        current = ""
        for unit in _split_units(_normalise(raw), size):
            candidate = f"{current} {unit}".strip()
            if len(candidate) <= size:
                current = candidate
                continue
            chunks.append(TextChunk(page_number, len(chunks), current))
            # Carry the tail of the previous passage forward so context isn't lost at boundaries
            tail = current[-overlap:]
            tail = tail[tail.find(" ") + 1 :] if " " in tail else tail
            current = f"{tail} {unit}".strip() if len(tail) + len(unit) + 1 <= size else unit
        if current:
            chunks.append(TextChunk(page_number, len(chunks), current))
    return chunks
