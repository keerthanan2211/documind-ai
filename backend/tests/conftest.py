"""
Integration tests run against a real PostgreSQL + pgvector database, with a fake AI provider
so they are fast, free and deterministic. Set TEST_DATABASE_URL to point at your test database.
"""

import hashlib
import io
import math
import os
import re
import tempfile

import pytest

os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://postgres@/documind_test?host=/tmp"
)
os.environ["LOCAL_STORAGE_DIR"] = tempfile.mkdtemp(prefix="documind-test-")
os.environ["STORAGE_BACKEND"] = "local"
# Word-overlap fake embeddings are less similar than real ones, so loosen the relevance cutoff
os.environ["MAX_DISTANCE"] = "0.9"

from fastapi.testclient import TestClient  # noqa: E402

from app.config import get_settings  # noqa: E402
from app.db import Base, engine, init_db  # noqa: E402
from app.main import create_app  # noqa: E402
from app.services.ai import get_ai  # noqa: E402

DIM = get_settings().embed_dim


class FakeAI:
    """Bag-of-words hashing 'embeddings': texts that share words get similar vectors, like real ones."""

    def __init__(self):
        self.prompts: list[str] = []

    def embed(self, texts, task):
        vectors = []
        for text in texts:
            v = [0.0] * DIM
            for word in re.findall(r"[a-z]{3,}", text.lower()):
                v[int(hashlib.md5(word.encode()).hexdigest(), 16) % DIM] += 1.0
            norm = math.sqrt(sum(x * x for x in v)) or 1.0
            vectors.append([x / norm for x in v])
        return vectors

    def generate(self, system, prompt):
        self.prompts.append(prompt)
        return "The warranty lasts 24 months from purchase [1]."


@pytest.fixture()
def fake_ai():
    return FakeAI()


@pytest.fixture()
def client(fake_ai):
    Base.metadata.drop_all(engine)
    init_db()
    app = create_app()
    app.dependency_overrides[get_ai] = lambda: fake_ai
    app.state.limiter.enabled = False
    with TestClient(app) as c:
        yield c


def make_pdf(pages: list[str]) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    for text in pages:
        y = 800
        for line in text.split("\n"):
            pdf.drawString(50, y, line)
            y -= 16
        pdf.showPage()
    pdf.save()
    return buf.getvalue()


@pytest.fixture()
def sample_pdf() -> bytes:
    return make_pdf(
        [
            "Product Manual\nThis guide explains setup and daily use of the water purifier.",
            "Warranty\nThe warranty lasts 24 months from the date of purchase.\nIt covers manufacturing defects only.",
            "Cleaning\nReplace the carbon filter every six months for best taste.",
        ]
    )
