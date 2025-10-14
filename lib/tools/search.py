from typing import Dict, List

import httpx
import structlog

from config import get_settings

logger = structlog.get_logger()


async def serper_search(query: str, num_results: int = 20) -> List[Dict]:
    """Execute Google search via Serper.dev API."""
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": get_settings().serper_api_key, "Content-Type": "application/json"}
    payload = {"q": query, "num": num_results}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            results = response.json().get("organic", [])
            return [{"url": r.get("link"), "title": r.get("title"), "snippet": r.get("snippet")} for r in results]
    except httpx.HTTPError as e:
        logger.error("serper_search_failed", query=query, error=str(e))
        return []
