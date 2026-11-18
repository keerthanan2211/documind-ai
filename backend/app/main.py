import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.config import get_settings
from app.db import engine, init_db
from app.limiter import limiter
from app.routers import chat, documents
from app.services.ai import AIError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="DocuMind AI",
        description="Upload PDFs and ask questions. Answers cite the pages they came from.",
        version="1.0.0",
        lifespan=lifespan,
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    @app.exception_handler(AIError)
    async def ai_unavailable(_request: Request, exc: AIError):
        # e.g. missing GEMINI_API_KEY: explain instead of returning a bare 500
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origin_list,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type"],
    )

    app.include_router(documents.router, prefix="/api")
    app.include_router(chat.router, prefix="/api")

    @app.get("/api/health", tags=["health"])
    def health():
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok"}

    return app


app = create_app()
