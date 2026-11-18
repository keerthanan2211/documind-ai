import logging
import uuid

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Chunk, Document
from app.services.ai import AIProvider
from app.services.chunking import chunk_pages
from app.services.pdf import PdfError, extract_pages
from app.services.storage import Storage

log = logging.getLogger(__name__)


def ingest_document(db: Session, doc_id: uuid.UUID, ai: AIProvider, storage: Storage) -> None:
    """
    Runs after upload (as a background task): PDF -> page text -> passages -> embeddings -> pgvector.
    Any failure is stored on the document so the UI can explain what went wrong.
    """
    settings = get_settings()
    doc = db.get(Document, doc_id)
    if doc is None:
        return

    try:
        pages = extract_pages(storage.load(doc.storage_key), settings.max_pages)
        passages = chunk_pages(pages, settings.chunk_size, settings.chunk_overlap)
        vectors = ai.embed([p.content for p in passages], task="document")
        if len(vectors) != len(passages):
            raise RuntimeError("Embedding count did not match passage count")

        db.add_all(
            Chunk(document_id=doc.id, page=p.page, chunk_index=p.index, content=p.content, embedding=v)
            for p, v in zip(passages, vectors, strict=True)
        )
        doc.page_count = len(pages)
        doc.chunk_count = len(passages)
        doc.status = "ready"
        db.commit()
    except PdfError as exc:
        db.rollback()
        _fail(db, doc, str(exc))
    except Exception:
        log.exception("Ingestion failed for document %s", doc_id)
        db.rollback()
        _fail(db, doc, "Processing failed. Try uploading the file again.")


def _fail(db: Session, doc: Document, message: str) -> None:
    doc.status = "failed"
    doc.error = message
    db.commit()
