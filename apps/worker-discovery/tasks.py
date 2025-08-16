from celery import Celery
import os
import sys
from typing import Dict, Any, List

# Add libs to path
sys.path.append('/app/libs')

from tavily_client import tavily_search
from common.config import load_vertical

celery = Celery(
    __name__,
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0")
)

def expand_queries(query_templates: List[str], topics: List[str] = None) -> List[str]:
    """Expand query templates with topics."""
    if not topics:
        topics = ["technology", "science", "policy", "regulation", "guidelines"]
    
    queries = []
    for template in query_templates:
        if "{topic}" in template:
            for topic in topics:
                queries.append(template.replace("{topic}", topic))
        else:
            queries.append(template)
    
    return queries

@celery.task(name="tasks.discovery.plan_and_search", bind=True)
def plan_and_search(self, cfg: Dict[str, Any]):
    """Plan and execute discovery searches."""
    try:
        discovery_config = cfg.get("discovery", {})
        
        # Expand query templates
        query_templates = discovery_config.get("queries", [])
        topics = cfg.get("topics", [])
        
        if isinstance(topics, list) and topics and isinstance(topics[0], dict):
            # Extract topic titles if topics are objects
            topic_names = [t.get("title", t.get("id", "")) for t in topics]
        else:
            topic_names = topics if topics else None
        
        queries = expand_queries(query_templates, topic_names)
        
        print(f"Executing {len(queries)} discovery queries")
        
        total_results = 0
        for query in queries:
            try:
                results = tavily_search(
                    query,
                    max_results=discovery_config.get("max_results", 25),
                    freshness=discovery_config.get("freshness", "30d"),
                    allow=discovery_config.get("allowlist", []),
                    deny=discovery_config.get("denylist", [])
                )
                
                print(f"Query '{query}' returned {len(results)} results")
                total_results += len(results)
                
                # Send each result to intake queue
                for result in results:
                    if result.get("url"):
                        celery.send_task(
                            "tasks.intake.fetch_extract",
                            args=[result["url"]],
                            queue="intake"
                        )
                
            except Exception as e:
                print(f"Error processing query '{query}': {e}")
                continue
        
        print(f"Discovery completed: {total_results} total results queued for intake")
        return {"success": True, "queries_processed": len(queries), "results_found": total_results}
        
    except Exception as e:
        print(f"Discovery task failed: {e}")
        self.retry(countdown=60, max_retries=3)

@celery.task(name="tasks.discovery.single_search", bind=True)
def single_search(self, query: str, config: Dict[str, Any] = None):
    """Execute a single search query."""
    try:
        if not config:
            config = load_vertical().get("discovery", {})
        
        results = tavily_search(
            query,
            max_results=config.get("max_results", 25),
            freshness=config.get("freshness", "30d"),
            allow=config.get("allowlist", []),
            deny=config.get("denylist", [])
        )
        
        # Queue results for intake
        for result in results:
            if result.get("url"):
                celery.send_task(
                    "tasks.intake.fetch_extract",
                    args=[result["url"]],
                    queue="intake"
                )
        
        return {"success": True, "results_found": len(results)}
        
    except Exception as e:
        print(f"Single search failed for query '{query}': {e}")
        self.retry(countdown=30, max_retries=2)