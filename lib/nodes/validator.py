from datetime import datetime
from typing import Dict

import structlog
from pydantic import ValidationError

from lib.state import DatasetCompilationState

logger = structlog.get_logger()


async def validation_agent_node(state: DatasetCompilationState) -> Dict:
    """Verifies citations and data quality."""
    logger.info("validation_agent_node: entered", entity_count=len(state['discovered_entities']))

    validated_entities = []

    verification_prompt_template = """
    Please act as a fact-checker. I will provide you with a statement and the source content it was extracted from.
    Determine if the source content explicitly supports the statement.
    Respond with only "verified", "weak", or "contradicted".

    - "verified": The source directly and clearly supports the statement.
    - "weak": The source hints at the statement but does not state it directly.
    - "contradicted": The source contradicts the statement.

    Source Content:
    ---
    {content}
    ---

    Statement to Verify:
    "{field_name}" is "{field_value}"
    """

    for entity_dict in state['discovered_entities']:
        try:
            entity = CompiledEntity.model_validate(entity_dict)
            for field in entity.fields:
                for citation in field.citations:
                    content = await fetch_page_content(str(citation.source_url))
                    if content:
                        prompt = verification_prompt_template.format(
                            content=content[:5000],
                            field_name=field.field_name,
                            field_value=field.value
                        )
                        response = await openai_client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": prompt}],
                            max_tokens=10,
                            temperature=0
                        )
                        status = response.choices[0].message.content.lower().strip()
                        if status in ["verified", "weak", "contradicted"]:
                            citation.verification_status = status
                            citation.support_strength = {"verified": 1.0, "weak": 0.5, "contradicted": 0.0}.get(status,
                                                                                                                0.5)

            entity.last_validated = datetime.now()
            validated_entities.append(entity.model_dump())
        except ValidationError as e:
            logger.warning("validation_agent_node: skipping invalid entity", error=str(e))
            continue

    logger.info("validation_agent_node: completed")
    return {"discovered_entities": validated_entities, "next_action": "debate"}
