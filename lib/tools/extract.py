import json
from typing import Dict, List, Optional

import structlog
from pydantic import BaseModel

from config import get_settings, get_openai_client

logger = structlog.get_logger()


async def extract_structured_data(html_content: str, pydantic_model: BaseModel, instructions: str) -> Optional[
    List[Dict]]:
    """Extract structured data using OpenAI's functions/tools feature."""
    try:
        openai_client = get_openai_client()
        response = await openai_client.chat.completions.create(
            model=get_settings().openai_model,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user",
                 "content": f"Here is the webpage content to extract from:\n\n{html_content[:10000]}..."}
            ],
            tools=[{"type": "function",
                    "function": {"name": "extract_entities", "description": "Extract entities from the text.",
                                 "parameters": pydantic_model.model_json_schema()}}],
            tool_choice={"type": "function", "function": {"name": "extract_entities"}},
        )
        tool_call = response.choices[0].message.tool_calls[0]
        arguments = json.loads(tool_call.function.arguments)
        return arguments.get("entities", [])
    except Exception as e:
        logger.error("extract_structured_data_failed", error=str(e))
        return None
