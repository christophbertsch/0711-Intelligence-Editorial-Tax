from typing import List, Dict, Any, Optional
from pydantic import BaseModel, HttpUrl
from datetime import datetime

class Document(BaseModel):
    """Core document schema."""
    url: HttpUrl
    title: str
    text: str
    language: Optional[str] = None
    published_at: Optional[datetime] = None
    content_hash: str
    metadata: Dict[str, Any] = {}

class Entity(BaseModel):
    """Named entity schema."""
    name: str
    type: str
    confidence: float
    mentions: List[Dict[str, Any]] = []

class Edge(BaseModel):
    """Graph edge schema."""
    source: str
    target: str
    relation: str
    confidence: float

class ProcessedDocument(Document):
    """Document with processing results."""
    labels: Dict[str, Any] = {}
    entities: List[Entity] = []
    edges: List[Edge] = []
    chunks: List[str] = []
    vectors: List[List[float]] = []
    abstract: Optional[str] = None
    abstract_citations: List[Dict[str, Any]] = []

class TaskResult(BaseModel):
    """Generic task result schema."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}