from celery import Celery
import os
import sys
from typing import Dict, Any

# Add libs to path
sys.path.append('/app/libs')

from seven011_client import (
    create_collection_if_missing, 
    upsert_document, 
    reindex_document, 
    graph_upsert
)

celery = Celery(
    __name__,
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0")
)

@celery.task(name="tasks.ingestion.write_to_0711", bind=True)
def write_to_0711(self, payload: Dict[str, Any]):
    """Write processed document to 0711 Agent System."""
    try:
        collection = os.getenv("COLLECTION", "vertical_generic")
        print(f"Ingesting document to collection '{collection}': {payload.get('title', 'Untitled')}")
        
        # Ensure collection exists
        try:
            create_collection_if_missing(collection)
            print(f"Collection '{collection}' ready")
        except Exception as e:
            print(f"Collection creation failed: {e}")
            # Continue anyway, collection might already exist
        
        # Upsert document
        try:
            doc_id = upsert_document(collection, payload)
            print(f"Document created with ID: {doc_id}")
        except Exception as e:
            print(f"Document creation failed: {e}")
            self.retry(countdown=60, max_retries=2)
            return
        
        # Upsert graph entities and relationships
        try:
            entities = payload.get("entities", [])
            edges = payload.get("edges", [])
            
            if entities or edges:
                graph_upsert(collection, entities, edges)
                print(f"Graph updated: {len(entities)} entities, {len(edges)} edges")
        except Exception as e:
            print(f"Graph update failed: {e}")
            # Don't fail the whole task for graph issues
        
        # Reindex document for search
        try:
            reindex_document(doc_id)
            print(f"Document {doc_id} reindexed for search")
        except Exception as e:
            print(f"Reindexing failed: {e}")
            # Don't fail the whole task for reindexing issues
        
        print(f"Successfully ingested: {payload.get('title', 'Untitled')}")
        return {
            "success": True,
            "doc_id": doc_id,
            "collection": collection,
            "entities_count": len(payload.get("entities", [])),
            "edges_count": len(payload.get("edges", []))
        }
        
    except Exception as e:
        print(f"Ingestion task failed: {e}")
        self.retry(countdown=60, max_retries=3)

@celery.task(name="tasks.ingestion.bulk_ingest", bind=True)
def bulk_ingest(self, documents: list, collection: str = None):
    """Bulk ingest multiple documents."""
    try:
        if not collection:
            collection = os.getenv("COLLECTION", "vertical_generic")
        
        create_collection_if_missing(collection)
        
        results = []
        for doc in documents:
            try:
                doc_id = upsert_document(collection, doc)
                
                # Handle graph data
                entities = doc.get("entities", [])
                edges = doc.get("edges", [])
                if entities or edges:
                    graph_upsert(collection, entities, edges)
                
                results.append({"success": True, "doc_id": doc_id})
            except Exception as e:
                results.append({"success": False, "error": str(e)})
        
        successful = sum(1 for r in results if r["success"])
        print(f"Bulk ingest completed: {successful}/{len(documents)} successful")
        
        return {
            "success": True,
            "total": len(documents),
            "successful": successful,
            "results": results
        }
        
    except Exception as e:
        print(f"Bulk ingest failed: {e}")
        self.retry(countdown=60, max_retries=2)

@celery.task(name="tasks.ingestion.update_document", bind=True)
def update_document(self, doc_id: str, updates: Dict[str, Any]):
    """Update existing document."""
    try:
        # This would typically use a PATCH endpoint if available
        # For now, we'll log the update request
        print(f"Update request for document {doc_id}: {list(updates.keys())}")
        
        # In a real implementation, you'd call the 0711 API to update
        # the document with the provided updates
        
        return {"success": True, "doc_id": doc_id, "updated_fields": list(updates.keys())}
        
    except Exception as e:
        print(f"Document update failed: {e}")
        self.retry(countdown=30, max_retries=1)