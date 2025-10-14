import asyncio
from typing import Any, Dict, List

import structlog
from pydantic import BaseModel, Field, create_model

from config import get_settings
from lib.datamodels import EntityField, Citation, CompiledEntity
from lib.state import DatasetCompilationState
from lib.tools.extract import extract_structured_data
from lib.tools.scrap import fetch_page_content

logger = structlog.get_logger()


async def extraction_agent_node(state: DatasetCompilationState) -> Dict:
    """Extracts structured data from a batch of web pages."""
    urls_to_process = state.get("pages_to_process", [])
    if not urls_to_process:
        return {"next_action": "search"}  # Nothing to process

    logger.info("extraction_agent_node: starting extraction", url_count=len(urls_to_process))

    # Define the extraction schema based on the orchestrator's analysis
    instructions = f"""
    You are an expert data extraction agent. From the provided web page content, extract all entities that match the user's request.
    The user is looking for: {state['query']}.
    The required fields for each entity are: {state['required_fields']}.
    For each piece of data, create a citation pointing to the source URL.
    Present the extracted data as a list of entities.
    """

    semaphore = asyncio.Semaphore(get_settings().max_concurrent_agents)

    async def process_url(url):
        async with semaphore:
            content = await fetch_page_content(url)
            if not content:
                return []

            # The schema dynamically includes the required fields
            fields = {
                "entity_type": (str, Field(..., description="The type of entity, e.g., 'company', 'person'.")),
            }
            for field in state['required_fields']:
                fields[field] = (Any, Field(..., description=f"The '{field}' of the entity."))

            DynamicEntity = create_model(
                "DynamicEntity",
                **fields
            )

            class DynamicExtractionSchema(BaseModel):
                entities: List[DynamicEntity]

            extracted_data = await extract_structured_data(content, DynamicExtractionSchema, instructions)

            if not extracted_data:
                return []

            # Convert to our standard format and add citations
            formatted_entities = []
            for item in extracted_data:
                fields = []
                for field_name, value in item.items():
                    if field_name != "entity_type":
                        fields.append(EntityField(
                            field_name=field_name,
                            value=value,
                            citations=[Citation(source_url=url)]
                        ).model_dump())

                formatted_entities.append(CompiledEntity(
                    entity_type=item['entity_type'] if 'entity_type' in item else "unknown",
                    fields=fields
                ).model_dump())
            return formatted_entities

    tasks = [process_url(url) for url in urls_to_process]
    results = await asyncio.gather(*tasks)

    new_entities = [entity for batch in results for entity in batch]
    logger.info("extraction_agent_node: completed", new_entities_found=len(new_entities))

    # Deduplicate entities (simple example, could be more sophisticated)
    existing_entities = state.get("discovered_entities", [])
    all_entities = existing_entities + new_entities

    # A simple dedupe based on entity name (assuming a 'name' field exists)
    unique_entities = {}
    for entity in all_entities:
        key_field = next((f for f in entity['fields'] if f['field_name'] in ['name', 'company_name', 'title']), None)
        if key_field:
            unique_entities[key_field['value']] = entity

    return {
        "discovered_entities": list(unique_entities.values()),
        "pages_to_process": [],  # Clear the queue
        "pages_processed": state["pages_processed"] + len(urls_to_process),
        "next_action": "filter"
    }
