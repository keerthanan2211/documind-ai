import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import SessionLocal, get_db
from app.limiter import limiter
from app.models import Document
from app.schemas import DocumentOut, MessageOut
from app.services.ai import AIProvider, get_ai
from app.services.ingest import ingest_document
from app.services.storage import Storage, get_storage

router = APIRouter(prefix="/documents", tags=["documents"])


def _run_ingest(doc_id: uuid.UUID, ai: AIProvider, storage: Storage) -> None:
    # Background tasks outlive the request, so they open their own database session
    with SessionLocal() as db:
        ingest_document(db, doc_id, ai, storage)


@router.post("", response_model=DocumentOut, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("10/minute")
async def upload(
    request: Request,
    file: UploadFile,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
    ai: AIProvider = Depends(get_ai),
    storage: Storage = Depends(get_storage),
):
    """Accepts a PDF, stores it, and starts processing in the background. Poll GET /documents/{id} for status."""
    settings = get_settings()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    data = await file.read(max_bytes + 1)

    if len(data) > max_bytes:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"Files must be {settings.max_upload_mb} MB or smaller"
        )
    if not data.startswith(b"%PDF"):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Only PDF files are supported")

    doc_id = uuid.uuid4()
    filename = (file.filename or "document.pdf").replace("/", "_")[:255]
    key = f"documents/{doc_id}.pdf"
    storage.save(key, data)

    doc = Document(id=doc_id, filename=filename, size_bytes=len(data), storage_key=key)
    db.add(doc)
    db.commit()

    background.add_task(_run_ingest, doc_id, ai, storage)
    return doc


@router.get("", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    return db.scalars(select(Document).order_by(Document.created_at.desc())).all()


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: uuid.UUID, db: Session = Depends(get_db)):
    return _get_or_404(db, doc_id)


@router.get("/{doc_id}/messages", response_model=list[MessageOut])
def get_messages(doc_id: uuid.UUID, db: Session = Depends(get_db)):
    return _get_or_404(db, doc_id).messages


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(doc_id: uuid.UUID, db: Session = Depends(get_db), storage: Storage = Depends(get_storage)):
    doc = _get_or_404(db, doc_id)
    storage.delete(doc.storage_key)
    db.delete(doc)  # chunks and messages are removed by ON DELETE CASCADE
    db.commit()


def _get_or_404(db: Session, doc_id: uuid.UUID) -> Document:
    doc = db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return doc
