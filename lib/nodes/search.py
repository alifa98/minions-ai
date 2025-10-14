import asyncio
from typing import Dict

import structlog

from config import get_settings
from lib.state import DatasetCompilationState
from lib.tools.embedding import get_embedding, cosine_similarity
from lib.tools.search import serper_search

logger = structlog.get_logger()

async def search_agent_node(state: DatasetCompilationState) -> Dict:
    """Executes search queries and identifies relevant pages."""
    logger.info("search_agent_node: entered", queries=state['search_queries'])

    # Hierarchical Filtering - Stage 1
    query_embedding = await get_embedding(state['query'])
    if not query_embedding:
        logger.error("search_agent_node: failed to get query embedding. Aborting search.")
        return {"pages_to_process": []}

    all_urls = set()
    tasks = [serper_search(q) for q in state['search_queries']]
    search_results = await asyncio.gather(*tasks)

    relevant_pages = []
    processed_urls = state.get('processed_urls', list([]))

    for results in search_results:
        for result in results:
            url = result['url']
            if url and url not in processed_urls and url not in all_urls:
                snippet = result.get('snippet', '')
                snippet_embedding = await get_embedding(snippet)
                if snippet_embedding:
                    similarity = cosine_similarity(query_embedding, snippet_embedding)
                    if similarity > get_settings().relevance_threshold:
                        logger.info("search_agent_node: found relevant page", url=url, similarity=f"{similarity:.2f}")
                        relevant_pages.append(url)
                        all_urls.add(url)

    logger.info("search_agent_node: completed", relevant_pages_found=len(relevant_pages))

    return {
        "pages_to_process": relevant_pages,
        "processed_urls": list(set(processed_urls) | all_urls),
        "next_action": "extract"  # if relevant_pages else "search"
    }
