from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="Natural language query to be processed by the multi-agent graph.",
        json_schema_extra={"example": "How do we handle GCP secret rotation?"}
    )

class DocumentPayload(BaseModel):
    id: str
    content: str
    category: str
    score: float

class QueryResponse(BaseModel):
    query: str
    current_step: str
    retrieved_docs: List[DocumentPayload]
    analysis_output: Optional[str]
    error: Optional[str]

class IngestRequest(BaseModel):
    documents: List[Dict[str, Any]] = Field(
        ...,
        description="List of raw document dictionaries to embed and upsert into Qdrant.",
        json_schema_extra={"example": [{"id": "doc_99", "category": "infra", "content": "Sample enterprise document text."}]}
    )

class IngestResponse(BaseModel):
    status: str
    message: str