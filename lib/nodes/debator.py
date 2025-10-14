import json
from typing import Dict

import structlog

from config import get_openai_client
from lib.state import DatasetCompilationState

logger = structlog.get_logger()


async def debate_agent_node(state: DatasetCompilationState) -> Dict:
    """Identifies gaps and triggers strategy adjustments."""
    logger.info("debate_agent_node: analyzing for coverage gaps")

    current_entities = state.get('discovered_entities', [])
    if not current_entities:
        logger.info("debate_agent_node: no entities found, cannot debate strategy.")
        return {"next_action": "complete"}

    prompt = f"""
    You are a debate agent. Your role is to critique the current dataset compilation strategy to improve its comprehensiveness.

    Original Query: "{state['query']}"
    Current Search Queries: {state['search_queries']}
    Number of Entities Found: {len(current_entities)}
    Target Number of Entities: {state['target_comprehensiveness']}

    Analyze the current state. Are there any obvious gaps? Are the search queries too narrow or too broad?
    Suggest 3 new, creative, and diverse search queries that might uncover missing information.
    For example, think about synonyms, related concepts, or different types of sources (forums, news, official reports).

    Return your answer in JSON format:
    {{
      "analysis": "Brief analysis of the current strategy's weakness.",
      "proposed_new_queries": ["...", "...", "..."]
    }}
    """

    try:
        response = await get_openai_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        debate_result = json.loads(response.choices[0].message.content)

        logger.info("debate_agent_node: generated new strategic input", analysis=debate_result['analysis'])

        # Combine old and new queries, then keep unique ones
        new_queries = state['search_queries'] + debate_result['proposed_new_queries']
        unique_queries = list(dict.fromkeys(new_queries))

        if len(unique_queries) > 1:
            return {"search_queries": unique_queries, "next_action": "search"}
        return {"next_action": "complete"}

    except Exception as e:
        logger.error("debate_agent_node: failed to generate new queries", error=str(e))
        return {"next_action": "complete"}
