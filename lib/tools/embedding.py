import json
from typing import List, Optional

import numpy as np
import structlog

from config import get_redis, get_openai_client, get_settings

logger = structlog.get_logger()


async def get_embedding(text: str) -> Optional[List[float]]:
    """Generate embedding vector for text, with caching."""

    redis_client = get_redis()

    text = text.strip()
    if not text:
        return None

    # Check cache first
    cache_key = f"embed:{hash(text)}"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    try:
        response = await get_openai_client().embeddings.create(model=get_settings().openai_embedding_model_small,
                                                               input=[text])
        embedding = response.data[0].embedding
        # Cache the result
        await redis_client.setex(cache_key, 3600 * 24 * 7, json.dumps(embedding))
        return embedding
    except Exception as e:
        logger.error("get_embedding_failed", error=str(e))
        return None


def cosine_similarity(v1, v2):
    """Calculate cosine similarity between two vectors."""
    vec1 = np.array(v1)
    vec2 = np.array(v2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
