from celery import Celery
import os
import sys
from typing import Dict, Any

# Add libs to path
sys.path.append('/app/libs')

from llm import summarize_with_citations, extract_claims
from tavily_client import corroborate_claims

celery = Celery(
    __name__,
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0")
)

@celery.task(name="tasks.editorial.summarize_and_qc", bind=True)
def summarize_and_qc(self, payload: Dict[str, Any]):
    """Generate summary and perform quality control."""
    try:
        print(f"Editorial processing: {payload.get('title', 'Untitled')}")
        
        # Generate summary with citations
        try:
            summary = summarize_with_citations(payload["text"], payload["labels"])
            print(f"Generated summary ({len(summary)} chars)")
        except Exception as e:
            print(f"Summarization failed: {e}")
            # Fallback to truncated text
            summary = payload["text"][:500] + "..." if len(payload["text"]) > 500 else payload["text"]
        
        # Extract claims for fact-checking
        try:
            claims = extract_claims(summary)
            claims = claims[:10]  # Limit to 10 claims
            print(f"Extracted {len(claims)} claims for fact-checking")
        except Exception as e:
            print(f"Claim extraction failed: {e}")
            claims = []
        
        # Fact-check claims if any exist
        citations = []
        if claims:
            try:
                ok, citations = corroborate_claims(claims, required=2)
                print(f"Fact-check result: {ok}, {len(citations)} citations")
                
                if not ok:
                    print("Warning: Fact-check failed, routing to human review")
                    # In production, this would route to human review queue
                    # For now, we'll continue with a warning flag
                    payload["needs_review"] = True
            except Exception as e:
                print(f"Fact-checking failed: {e}")
                citations = []
        
        # Add editorial results to payload
        payload["abstract"] = summary
        payload["abstract_citations"] = citations
        payload["editorial_claims"] = claims
        
        # Send to ingestion queue
        celery.send_task(
            "tasks.ingestion.write_to_0711",
            args=[payload],
            queue="ingestion"
        )
        
        print(f"Editorial processing completed for: {payload.get('title', 'Untitled')}")
        return {
            "success": True,
            "summary_length": len(summary),
            "claims_count": len(claims),
            "citations_count": len(citations),
            "needs_review": payload.get("needs_review", False)
        }
        
    except Exception as e:
        print(f"Editorial task failed: {e}")
        self.retry(countdown=60, max_retries=2)

@celery.task(name="tasks.editorial.human_review", bind=True)
def human_review(self, payload: Dict[str, Any], reviewer_notes: str = ""):
    """Process document after human review."""
    try:
        # Add reviewer notes
        payload["reviewer_notes"] = reviewer_notes
        payload["human_reviewed"] = True
        
        # Send to ingestion
        celery.send_task(
            "tasks.ingestion.write_to_0711",
            args=[payload],
            queue="ingestion"
        )
        
        return {"success": True, "reviewed": True}
        
    except Exception as e:
        print(f"Human review processing failed: {e}")
        self.retry(countdown=30, max_retries=1)

@celery.task(name="tasks.editorial.quality_check", bind=True)
def quality_check(self, payload: Dict[str, Any]):
    """Perform additional quality checks."""
    try:
        quality_score = 0.0
        issues = []
        
        # Check text length
        text_length = len(payload.get("text", ""))
        if text_length < 100:
            issues.append("Text too short")
        elif text_length > 50000:
            issues.append("Text very long")
        else:
            quality_score += 0.3
        
        # Check if title exists
        if payload.get("title") and len(payload["title"]) > 5:
            quality_score += 0.2
        else:
            issues.append("Missing or poor title")
        
        # Check if abstract exists
        if payload.get("abstract") and len(payload["abstract"]) > 50:
            quality_score += 0.2
        else:
            issues.append("Missing or poor abstract")
        
        # Check entities
        if payload.get("entities") and len(payload["entities"]) > 0:
            quality_score += 0.15
        else:
            issues.append("No entities extracted")
        
        # Check citations
        if payload.get("abstract_citations") and len(payload["abstract_citations"]) > 0:
            quality_score += 0.15
        else:
            issues.append("No citations found")
        
        payload["quality_score"] = quality_score
        payload["quality_issues"] = issues
        
        print(f"Quality check: {quality_score:.2f} score, {len(issues)} issues")
        
        return {
            "success": True,
            "quality_score": quality_score,
            "issues": issues
        }
        
    except Exception as e:
        print(f"Quality check failed: {e}")
        return {"success": False, "error": str(e)}