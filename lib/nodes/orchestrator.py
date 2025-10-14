import json
from typing import Dict

import structlog

from config import get_openai_client, get_settings
from lib.state import DatasetCompilationState

logger = structlog.get_logger()


async def orchestrator_node(state: DatasetCompilationState) -> Dict:
    """
    Analyzes the query, plans the strategy, coordinates agents, and evaluates completion.
    """
    logger.info("orchestrator_node: entered", iteration=state['current_iteration'])

    if state["current_iteration"] == 0:
        # Phase 1: Query Analysis (first run)
        logger.info("orchestrator_node: performing initial query analysis")
        analysis_prompt = f"""
        Analyze the following user query and decompose it into a structured search plan.
        Query: "{state['query']}"

        1.  **Complexity Tier**: Classify as "simple", "moderate", or "complex".
        2.  **Required Fields**: Identify the key data fields the user wants for each entity.
        3.  **Filter Criteria**: Extract any explicit filters (e.g., date ranges, locations).
        4.  **Target Comprehensiveness**: Estimate the number of entities a good answer would contain.
        5.  **Search Queries**: Generate 3-5 diverse Google search queries to find the data.

        Respond in JSON format:
        {{
            "complexity_tier": "...",
            "required_fields": ["...", "..."],
            "filter_criteria": {{...}},
            "target_comprehensiveness": <integer>,
            "search_queries": ["...", "..."]
        }}
        """
        response = await get_openai_client().chat.completions.create(
            model=get_settings().openai_model,
            messages=[{"role": "user", "content": analysis_prompt}],
            response_format={"type": "json_object"},
        )
        analysis = json.loads(response.choices[0].message.content)

        return {
            "complexity_tier": analysis["complexity_tier"],
            "required_fields": analysis["required_fields"],
            "filter_criteria": analysis["filter_criteria"],
            "target_comprehensiveness": analysis["target_comprehensiveness"],
            "search_queries": analysis["search_queries"],
            "current_iteration": 1,
            "next_action": "search"
        }

    # Meta-Learning Checkpoint (after each iteration)
    if state["current_iteration"] > 1:
        # Evaluate progress
        current_entities = len(state.get('discovered_entities', []))
        target = state['target_comprehensiveness']
        comprehensiveness = current_entities / target if target > 0 else 0

        logger.info(
            "orchestrator_node: meta_checkpoint",
            iteration=state['current_iteration'],
            entities_found=current_entities,
            target=target,
            comprehensiveness=f"{comprehensiveness:.2%}"
        )

        if comprehensiveness >= 0.9 or state["current_iteration"] > state["max_iterations"]:
            logger.info("orchestrator_node: goal met or max iterations reached. Moving to validation.")
            return {"next_action": "complete", "comprehensiveness_score": comprehensiveness}

    # Decide next action based on state
    if not state.get("pages_to_process"):
        logger.info("orchestrator_node: no pages to process, initiating new search cycle.")
        return {"next_action": "search", "current_iteration": state["current_iteration"] + 1}
    else:
        logger.info("orchestrator_node: pages found, dispatching to extraction agent.")
        return {"next_action": "extract", "current_iteration": state["current_iteration"] + 1}


def orchestrator_router(state: DatasetCompilationState) -> str:
    """A simple Router that routes from the orchestrator to the appropriate worker agent or ends."""
    action = state.get("next_action")
    logger.info("orchestrator_router: routing", next_action=action)
    if action in {"search", "extract", "filter", "validate", "complete", "debate"}:
        return action
    else:
        raise ValueError("Invalid next_action in state")
