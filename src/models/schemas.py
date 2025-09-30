from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class UserQuery(BaseModel):
    query: str
    top_k: Optional[int] = 5
    conversation_history: Optional[List[Dict[str, str]]] = []
    session_id: Optional[str] = None
    works: Optional[List[str]] = []
    authors: Optional[List[str]] = []


class Citation(BaseModel):
    record_id: str
    link: str
    citation_text: Optional[str] = ""


class AssistantResponse(BaseModel):
    answer: str
    sources: Optional[List[Dict[str, str]]] = None  # List of citation objects with record_id, link, and citation_text
    conversation_history: Optional[List[Dict[str, str]]] = None
    session_id: Optional[str] = None


class GenerateResponseRequest(BaseModel):
    query: str
    context: List[str]


class ManticoreResponse(BaseModel):
    knn_distance: float
    docid: int
    authorid: str
    workid: str
    versionid: str
    sectionid: str
    text: str
    refs: List[str]
    record_id: str


class EmbeddingRequest(BaseModel):
    text: str


class TestQueryRequest(BaseModel):
    query: str
    agentic: bool = False
    top_k: int = 5
    return_fields: List[str] = ["record_id"]  # Default to just record IDs
    
    class Config:
        schema_extra = {
            "example": {
                "query": "What is the nature of God?",
                "agentic": True,
                "top_k": 5,
                "return_fields": ["record_id", "text", "authorid", "workid", "citation_text", "answer"]
            }
        }


class TestResponse(BaseModel):
    query: str
    agentic_mode: bool
    results: List[Dict[str, Any]]
    ai_answer: Optional[str] = None
    processing_info: Dict[str, Any]