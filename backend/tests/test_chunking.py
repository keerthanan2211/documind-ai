import pytest

from app.services.chunking import chunk_pages


def test_keeps_page_numbers():
    chunks = chunk_pages(["First page text.", "Second page text."], size=100, overlap=20)
    assert [c.page for c in chunks] == [1, 2]
    assert [c.index for c in chunks] == [0, 1]


def test_respects_max_size():
    text = " ".join(f"Sentence number {i} is here." for i in range(200))
    chunks = chunk_pages([text], size=300, overlap=50)
    assert len(chunks) > 1
    assert all(len(c.content) <= 300 for c in chunks)


def test_overlap_carries_context_forward():
    text = " ".join(f"Fact {i} about the system." for i in range(60))
    first, second = chunk_pages([text], size=200, overlap=60)[:2]
    assert first.content[-30:].split()[-1] in second.content


def test_rejoins_hyphenated_words_and_skips_empty_pages():
    chunks = chunk_pages(["The purifi-\ncation step", "   ", "End."], size=200, overlap=20)
    assert "purification" in chunks[0].content
    assert [c.page for c in chunks] == [1, 3]


def test_splits_very_long_words_safely():
    chunks = chunk_pages(["x" * 1000], size=300, overlap=50)
    assert all(len(c.content) <= 300 for c in chunks)
    assert all(set(c.content) <= {"x", " "} for c in chunks)
    assert sum(len(c.content) for c in chunks) >= 1000  # nothing lost (overlap may repeat some)


def test_rejects_overlap_not_smaller_than_size():
    with pytest.raises(ValueError):
        chunk_pages(["text"], size=100, overlap=100)
