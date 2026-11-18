from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration comes from environment variables (or a .env file)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://documind:documind@localhost:5432/documind"

    gemini_api_key: str = ""
    gemini_chat_model: str = "gemini-2.5-flash"
    gemini_embed_model: str = "gemini-embedding-001"
    embed_dim: int = 768

    storage_backend: str = "local"  # "local" or "s3"
    local_storage_dir: str = "./uploads"
    s3_bucket: str = ""
    aws_region: str = "ap-south-1"

    max_upload_mb: int = 20
    max_pages: int = 300
    chunk_size: int = 1200
    chunk_overlap: int = 200
    top_k: int = 6
    # Passages farther than this cosine distance are treated as unrelated (0 = identical, 2 = opposite)
    max_distance: float = 0.75

    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
