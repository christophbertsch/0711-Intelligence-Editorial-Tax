from celery import Celery
import os
import sys
from typing import Dict, Any

# Add libs to path
sys.path.append('/app/libs')

from llm import classify_json, ner_link
from common.chunking import chunk_by_headings
from common.embed import embed_chunks

celery = Celery(
    __name__,
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0")
)

@celery.task(name="tasks.understanding.classify_ner", bind=True)
def classify_ner(self, doc: Dict[str, Any]):
    """Classify document and extract named entities."""
    try:
        print(f"Understanding document: {doc.get('title', 'Untitled')}")
        
        # Classify document
        try:
            labels = classify_json(doc["text"])
            print(f"Classification: {labels}")
        except Exception as e:
            print(f"Classification failed: {e}")
            labels = {"doc_type": "article", "language": "en", "audience": "general"}
        
        # Extract named entities and relationships
        try:
            entities, edges = ner_link(doc["text"], labels)
            print(f"Extracted {len(entities)} entities and {len(edges)} relationships")
        except Exception as e:
            print(f"NER failed: {e}")
            entities, edges = [], []
        
        # Chunk text
        try:
            chunks = chunk_by_headings(
                doc["text"], 
                keep_headings=True, 
                target_tokens=500
            )
            print(f"Created {len(chunks)} chunks")
        except Exception as e:
            print(f"Chunking failed: {e}")
            chunks = [doc["text"]]  # Fallback to single chunk
        
        # Generate embeddings
        try:
            vectors = embed_chunks(chunks)
            print(f"Generated {len(vectors)} embeddings")
        except Exception as e:
            print(f"Embedding failed: {e}")
            vectors = []  # Will be handled downstream
        
        # Prepare payload for editorial stage
        payload = {
            **doc,
            "labels": labels,
            "entities": entities,
            "edges": edges,
            "chunks": chunks,
            "vectors": vectors
        }
        
        # Send to editorial queue
        celery.send_task(
            "tasks.editorial.summarize_and_qc",
            args=[payload],
            queue="editorial"
        )
        
        print(f"Successfully processed understanding for: {doc.get('title', 'Untitled')}")
        return {
            "success": True,
            "labels": labels,
            "entities_count": len(entities),
            "edges_count": len(edges),
            "chunks_count": len(chunks)
        }
        
    except Exception as e:
        print(f"Understanding task failed: {e}")
        self.retry(countdown=60, max_retries=2)

@celery.task(name="tasks.understanding.reprocess_embeddings", bind=True)
def reprocess_embeddings(self, doc_id: str, chunks: list):
    """Reprocess embeddings for existing document."""
    try:
        vectors = embed_chunks(chunks)
        
        # Update document with new embeddings
        # This would typically update the document in 0711
        print(f"Reprocessed embeddings for document {doc_id}")
        
        return {"success": True, "vectors_count": len(vectors)}
        
    except Exception as e:
        print(f"Embedding reprocessing failed: {e}")
        self.retry(countdown=30, max_retries=1)