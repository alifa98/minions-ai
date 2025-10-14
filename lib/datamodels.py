# ==============================================================================
#       Data Models (Pydantic Schemas)
# ==============================================================================
import uuid
from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class Citation(BaseModel):
    source_url: HttpUrl
    retrieval_date: datetime = Field(default_factory=datetime.now)
    support_strength: float = Field(ge=0.0, le=1.0, default=0.5)
    verification_status: str = "unverified"  # "verified" | "weak" | "unverified"


class EntityField(BaseModel):
    field_name: str
    value: Any
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    citations: List[Citation] = Field(default_factory=list)


class CompiledEntity(BaseModel):
    entity_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: str
    fields: List[EntityField]
    extraction_timestamp: datetime = Field(default_factory=datetime.now)
    last_validated: Optional[datetime] = None


class Dataset(BaseModel):
    task_id: str
    query: str
    entities: List[CompiledEntity]
    metadata: dict = Field(default_factory=dict)
    race_scores: dict = Field(default_factory=dict)
    fact_scores: dict = Field(default_factory=dict)


class KnowledgeCacheEntry(BaseModel):
    key: str
    value: Any
    relevance_score: float
    discovery_iteration: int
    usage_count: int = 0
    last_accessed: datetime = Field(default_factory=datetime.now)
