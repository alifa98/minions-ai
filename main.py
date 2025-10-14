# ==============================================================================
#  Main Execution Logic
# ==============================================================================

import asyncio
import json
import os
import uuid

import pandas as pd
import structlog

from config import get_settings
from lib.checkpointer import get_checkpointer
from lib.datamodels import CompiledEntity, Dataset
from lib.graph import get_state_graph

logger = structlog.get_logger()


async def main():
    """Main function to run the multi-agent system."""

    setting = get_settings()

    # --- Example Query ---
    query = "List top 20 latest patents in renewable energy filed in the last 2 years in the USA with inventor names and assignees."

    # --- Initial State ---
    task_id = str(uuid.uuid4())
    thread_id = f"thread_{task_id}"
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "query": query,
        "task_id": task_id,
        "thread_id": thread_id,
        "current_iteration": 0,
        "max_iterations": setting.max_iterations,
        "pages_processed": 0,
        "processed_urls": [],
        "discovered_entities": [],
        "messages": [],
    }

    logger.info("Starting new dataset compilation task...", **initial_state)

    checkpointer = get_checkpointer()

    graph = get_state_graph(checkpointer)

    final_state = None
    async for event in graph.astream(initial_state, config=config, stream_mode="values"):
        final_state = event
        # You can add real-time logging of the state here if needed
        # logger.info("State updated", current_node=list(event.keys())[0])

    logger.info("✅ Workflow finished. Finalizing dataset.")

    # --- Finalization (Section 3.3.2, Phase 5) ---
    final_entities = [CompiledEntity.model_validate(e) for e in final_state["discovered_entities"]]

    dataset = Dataset(
        task_id=task_id,
        query=query,
        entities=final_entities,
        metadata={
            "required_fields": final_state.get("required_fields", []),
            "filter_criteria": final_state.get("filter_criteria", {}),
        }
    )

    # --- Save results to files ---
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # Save as JSON
    json_path = os.path.join(output_dir, f"{task_id}.json")
    with open(json_path, 'w') as f:
        f.write(dataset.model_dump_json(indent=2))
    logger.info(f"💾 Dataset saved to {json_path}")

    # Save as CSV
    try:
        flat_data = []
        for entity in dataset.entities:
            row = {"entity_id": entity.entity_id, "entity_type": entity.entity_type}
            for field in entity.fields:
                row[field.field_name] = json.dumps(field.value)
                row[f"{field.field_name}_confidence"] = field.confidence
                # Include first citation source for simplicity in CSV
                if field.citations:
                    row[f"{field.field_name}_source"] = str(field.citations[0].source_url)
            flat_data.append(row)

        if flat_data:
            df = pd.DataFrame(flat_data)
            csv_path = os.path.join(output_dir, f"{task_id}.csv")
            df.to_csv(csv_path, index=False)
            logger.info(f"💾 Dataset saved to {csv_path}")
    except Exception as e:
        logger.error("Failed to export to CSV", error=str(e))


if __name__ == "__main__":
    asyncio.run(main())
