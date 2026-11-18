import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    filename: str
    size_bytes: int
    page_count: int
    chunk_count: int
    status: str
    error: str | None
    created_at: datetime


class Source(BaseModel):
    number: int
    page: int
    excerpt: str


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    sources: list[Source] | None = None
    created_at: datetime


class AskIn(BaseModel):
    question: str = Field(min_length=2, max_length=1000)


class AskOut(BaseModel):
    question: MessageOut
    answer: MessageOut
