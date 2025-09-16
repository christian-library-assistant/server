from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class UserQuery(BaseModel):
    query: str
    top_k: Optional[int] = 5
    conversation_history: Optional[List[Dict[str, str]]] = []


class Citation(BaseModel):
    record_id: str
    link: str
    citation_text: Optional[str] = ""


class AssistantResponse(BaseModel):
    answer: str
    sources: Optional[List[Dict[str, str]]] = None  # List of citation objects with record_id, link, and citation_text
    conversation_history: Optional[List[Dict[str, str]]] = None


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