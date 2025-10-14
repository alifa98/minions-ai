from typing import Dict
import structlog

from lib.state import DatasetCompilationState

logger = structlog.get_logger()


async def filter_agent_node(state: DatasetCompilationState) -> Dict:
    """Applies criteria-based filtering to candidate entities."""
    logger.info("filter_agent_node: entered", entity_count=len(state['discovered_entities']))
    criteria = state.get('filter_criteria')
    if not criteria:
        return {"next_action": "validate"}  # No filtering needed

    # For now, it's a simple example and assumes a specific structure
    # In a real system, this would be a more robust validation function
    def check_criteria(entity: Dict) -> bool:
        # Example: if criteria is {"location": "USA"}
        # check if entity has a field 'location' with value 'USA'
        for key, value in criteria.items():
            found = False
            for field in entity['fields']:
                if field['field_name'] == key and str(value).lower() in str(field['value']).lower():
                    found = True
                    break
            if not found:
                return False
        return True

    filtered_entities = [e for e in state['discovered_entities'] if check_criteria(e)]
    logger.info("filter_agent_node: completed", remaining_entities=len(filtered_entities))

    return {"discovered_entities": filtered_entities, "next_action": "validate"}
