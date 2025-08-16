from celery import Celery
import os
import sys
from typing import Dict, Any

# Add libs to path
sys.path.append('/app/libs')

from common.fetch import fetch_url, compute_content_hash
from common.extract import extract_text, extract_pdf_text, canonicalize_url
from common.dedupe import canonicalize, is_duplicate

celery = Celery(
    __name__,
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0")
)

@celery.task(name="tasks.intake.fetch_extract", bind=True)
def fetch_extract(self, url: str):
    """Fetch and extract content from URL."""
    try:
        print(f"Processing URL: {url}")
        
        # Canonicalize URL
        canonical_url = canonicalize_url(url)
        
        # Fetch content
        try:
            html, headers = fetch_url(canonical_url)
        except Exception as e:
            print(f"Failed to fetch {canonical_url}: {e}")
            return {"success": False, "error": f"Fetch failed: {e}"}
        
        # Extract content based on content type
        content_type = headers.get('content-type', '').lower()
        
        if 'pdf' in content_type:
            try:
                text = extract_pdf_text(canonical_url)
                doc = {
                    'url': canonical_url,
                    'title': f"PDF Document from {canonical_url}",
                    'text': text,
                    'metadata': {'content_type': 'application/pdf'}
                }
            except Exception as e:
                print(f"PDF extraction failed for {canonical_url}: {e}")
                return {"success": False, "error": f"PDF extraction failed: {e}"}
        else:
            # Extract from HTML
            doc = extract_text(html, canonical_url)
        
        # Skip if content is too short
        if len(doc['text']) < 100:
            print(f"Skipping {canonical_url}: content too short ({len(doc['text'])} chars)")
            return {"success": False, "error": "Content too short"}
        
        # Canonicalize and check for duplicates
        doc = canonicalize(doc)
        
        if is_duplicate(doc):
            print(f"Skipping {canonical_url}: duplicate content")
            return {"success": False, "error": "Duplicate content"}
        
        # Send to understanding queue
        celery.send_task(
            "tasks.understanding.classify_ner",
            args=[doc],
            queue="understanding"
        )
        
        print(f"Successfully processed {canonical_url} ({len(doc['text'])} chars)")
        return {"success": True, "url": canonical_url, "text_length": len(doc['text'])}
        
    except Exception as e:
        print(f"Intake task failed for {url}: {e}")
        self.retry(countdown=60, max_retries=2)

@celery.task(name="tasks.intake.batch_fetch", bind=True)
def batch_fetch(self, urls: list):
    """Process multiple URLs in batch."""
    try:
        results = []
        for url in urls:
            try:
                result = fetch_extract.apply_async(args=[url])
                results.append({"url": url, "task_id": result.id})
            except Exception as e:
                results.append({"url": url, "error": str(e)})
        
        return {"success": True, "processed": len(results), "results": results}
        
    except Exception as e:
        print(f"Batch fetch failed: {e}")
        self.retry(countdown=30, max_retries=1)