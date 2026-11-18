import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.limiter import limiter
from app.models import Document, Message
from app.schemas import AskIn, AskOut
from app.services.ai import AIError, AIProvider, get_ai
from app.services.rag import NOT_FOUND, SYSTEM_PROMPT, build_prompt, make_sources, retrieve

router = APIRouter(prefix="/documents", tags=["chat"])


@router.post("/{doc_id}/ask", response_model=AskOut)
@limiter.limit("20/minute")
def ask(
    request: Request,
    doc_id: uuid.UUID,
    body: AskIn,
    db: Session = Depends(get_db),
    ai: AIProvider = Depends(get_ai),
):
    doc = db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    if doc.status != "ready":
        raise HTTPException(status.HTTP_409_CONFLICT, "This document is still being processed")

    question = body.question.strip()
    history = list(doc.messages)

    try:
        [query_vector] = ai.embed([question], task="query")
        settings = get_settings()
        chunks = retrieve(db, doc.id, query_vector, settings.top_k, settings.max_distance)
        # Nothing relevant: answer honestly without calling the model at all
        answer = ai.generate(SYSTEM_PROMPT, build_prompt(question, chunks, history)) if chunks else NOT_FOUND
    except AIError as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY, "The AI service is unavailable right now. Try again shortly."
        ) from exc

    user_msg = Message(document_id=doc.id, role="user", content=question)
    bot_msg = Message(
        document_id=doc.id, role="assistant", content=answer or NOT_FOUND, sources=make_sources(answer, chunks)
    )
    db.add_all([user_msg, bot_msg])
    db.commit()
    return AskOut(question=user_msg, answer=bot_msg)
