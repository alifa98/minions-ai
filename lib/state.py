# ==============================================================================
#       LangGraph State Schema
# ==============================================================================

from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langgraph.graph.message import add_messages


class DatasetCompilationState(TypedDict):
    # User Input
    query: str
    task_id: str
    thread_id: str

    # Query Analysis
    complexity_tier: str
    required_fields: List[str]
    filter_criteria: Dict[str, Any]
    target_comprehensiveness: int

    # Search Strategy
    search_queries: List[str]
    data_sources: List[str]
    current_iteration: int
    max_iterations: int

    # Knowledge Accumulation
    discovered_entities: List[Dict]  # Raw dicts before Pydantic validation
    knowledge_cache: Dict[str, Any]
    source_insights: Dict[str, float]

    # Processing Status
    pages_processed: int
    pages_to_process: List[str]
    processed_urls: List[str]
    relevance_threshold: float

    # Quality Metrics
    comprehensiveness_score: float
    citation_coverage: float
    verification_status: Dict[str, str]

    # Agent Communication
    messages: Annotated[List, add_messages]
    next_action: Optional[str]
