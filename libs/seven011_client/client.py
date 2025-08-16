import os
import requests
from typing import Dict, Any, List

class Seven011Client:
    """Client for 0711 Agent System API."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_collections(self) -> List[Dict[str, Any]]:
        """List all collections."""
        response = requests.get(f"{self.base_url}/v1/collections", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def create_collection(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create a new collection."""
        payload = {"name": name, "description": description}
        response = requests.post(f"{self.base_url}/v1/collections", json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def create_document(self, collection: str, document: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document."""
        payload = {"collection": collection, **document}
        response = requests.post(f"{self.base_url}/v1/documents/", json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def reindex_document(self, doc_id: str) -> Dict[str, Any]:
        """Reindex a document."""
        response = requests.post(f"{self.base_url}/v1/documents/{doc_id}/reindex", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def search(self, collection: str, query: str, k: int = 20, hybrid: bool = True, 
               return_fields: List[str] = None) -> Dict[str, Any]:
        """Search documents."""
        payload = {
            "collection": collection,
            "query": query,
            "k": k,
            "hybrid": hybrid
        }
        if return_fields:
            payload["return"] = return_fields
        
        response = requests.post(f"{self.base_url}/v1/search", json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def graph_query(self, collection: str, cypher: str) -> Dict[str, Any]:
        """Execute Cypher query on graph."""
        payload = {"collection": collection, "cypher": cypher}
        response = requests.post(f"{self.base_url}/v1/graph/query", json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

# Global client instance
_client = None

def _get_client():
    global _client
    if _client is None:
        base_url = os.getenv("SEVEN011_BASE_URL")
        api_key = os.getenv("SEVEN011_API_KEY")
        if not base_url or not api_key:
            raise ValueError("SEVEN011_BASE_URL and SEVEN011_API_KEY environment variables required")
        _client = Seven011Client(base_url, api_key)
    return _client

def create_collection_if_missing(name: str) -> None:
    """Create collection if it doesn't exist."""
    client = _get_client()
    collections = client.get_collections()
    
    if name not in [c["name"] for c in collections]:
        client.create_collection(name, f"Auto-created collection for {name}")

def upsert_document(collection: str, payload: Dict[str, Any]) -> str:
    """Create or update document in 0711."""
    client = _get_client()
    
    doc = {
        "collection": collection,
        "title": payload["title"],
        "source_url": payload["url"],
        "language": payload.get("language", "auto"),
        "published_at": payload.get("published_at"),
        "doc_type": payload["labels"].get("doc_type"),
        "abstract": payload.get("abstract", ""),
        "chunks": [
            {"id": f"c{i}", "text": c, "order": i} 
            for i, c in enumerate(payload.get("chunks", []), 1)
        ],
        "entities": payload.get("entities", []),
        "citations": payload.get("abstract_citations", []),
        "metadata": payload.get("metadata", {})
    }
    
    result = client.create_document(collection, doc)
    return result["id"]

def reindex_document(doc_id: str) -> None:
    """Reindex document for search."""
    client = _get_client()
    client.reindex_document(doc_id)

def graph_upsert(collection: str, entities: List[Dict], edges: List[Dict]) -> None:
    """Upsert entities and relationships to graph."""
    if not entities and not edges:
        return
    
    client = _get_client()
    
    # Build Cypher query to create entities and relationships
    cypher_parts = []
    
    # Create entities
    for i, entity in enumerate(entities):
        node_var = f"n{i}"
        cypher_parts.append(
            f"MERGE ({node_var}:{entity['type']} {{name: '{entity['name']}'}})"
        )
    
    # Create relationships
    for edge in edges:
        # Find source and target entity indices
        source_idx = next((i for i, e in enumerate(entities) if e['name'] == edge['source']), None)
        target_idx = next((i for i, e in enumerate(entities) if e['name'] == edge['target']), None)
        
        if source_idx is not None and target_idx is not None:
            cypher_parts.append(
                f"MERGE (n{source_idx})-[:{edge['relation']}]->(n{target_idx})"
            )
    
    if cypher_parts:
        cypher = " ".join(cypher_parts)
        client.graph_query(collection, cypher)

def search_documents(collection: str, query: str, k: int = 20) -> Dict[str, Any]:
    """Search documents in collection."""
    client = _get_client()
    return client.search(
        collection=collection,
        query=query,
        k=k,
        hybrid=True,
        return_fields=["title", "snippet", "score", "citations", "source_url"]
    )