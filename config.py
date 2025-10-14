# ==============================================================================
#       Configuration
# ==============================================================================
from functools import lru_cache

from openai import AsyncOpenAI
from pydantic_settings import BaseSettings
from redis import asyncio as aioredis


class Settings(BaseSettings):
    openai_api_key: str
    serper_api_key: str
    redis_url: str = "redis://localhost:6379"
    postgres_url: str
    openai_model: str = "gpt-4o"
    openai_embedding_model_large: str = "text-embedding-3-large"
    openai_embedding_model_small: str = "text-embedding-3-small"
    max_iterations: int = 5
    max_concurrent_agents: int = 5
    relevance_threshold: float = 0.5
    checkpointer: str

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_openai_client() -> AsyncOpenAI:
    settings = get_settings()
    return AsyncOpenAI(api_key=settings.open_api_key)


def get_redis() -> aioredis.Redis:
    settings = get_settings()
    return aioredis.from_url(settings.redis_url)
