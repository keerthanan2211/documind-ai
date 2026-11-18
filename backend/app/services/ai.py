"""
AI provider abstraction. The app depends on the small `AIProvider` interface, not on Gemini directly,
so tests use a fake provider and switching to another model vendor only touches this file.
"""

from functools import lru_cache
from typing import Literal, Protocol

from app.config import get_settings

TaskType = Literal["document", "query"]


class AIError(RuntimeError):
    pass


class AIProvider(Protocol):
    def embed(self, texts: list[str], task: TaskType) -> list[list[float]]: ...

    def generate(self, system: str, prompt: str) -> str: ...


class GeminiProvider:
    BATCH = 50  # stay well under the API's per-request input limit

    def __init__(self, api_key: str, chat_model: str, embed_model: str, dim: int):
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._chat_model = chat_model
        self._embed_model = embed_model
        self._dim = dim

    def embed(self, texts: list[str], task: TaskType) -> list[list[float]]:
        from google.genai import types

        config = types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT" if task == "document" else "RETRIEVAL_QUERY",
            output_dimensionality=self._dim,
        )
        vectors: list[list[float]] = []
        try:
            for start in range(0, len(texts), self.BATCH):
                batch = texts[start : start + self.BATCH]
                result = self._client.models.embed_content(model=self._embed_model, contents=batch, config=config)
                vectors.extend(list(e.values) for e in result.embeddings)
        except Exception as exc:  # network, quota, auth
            raise AIError(f"Embedding request failed: {exc}") from exc
        return vectors

    def generate(self, system: str, prompt: str) -> str:
        from google.genai import types

        try:
            response = self._client.models.generate_content(
                model=self._chat_model,
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=system, temperature=0.2, max_output_tokens=1024),
            )
        except Exception as exc:
            raise AIError(f"Answer generation failed: {exc}") from exc
        return (response.text or "").strip()


@lru_cache
def get_ai() -> AIProvider:
    s = get_settings()
    if not s.gemini_api_key:
        raise AIError("GEMINI_API_KEY is not set. Add it to backend/.env.")
    return GeminiProvider(s.gemini_api_key, s.gemini_chat_model, s.gemini_embed_model, s.embed_dim)
