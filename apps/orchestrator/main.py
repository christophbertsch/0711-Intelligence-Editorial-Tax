from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from celery import Celery
from typing import Dict, Any
import os
import sys

# Add libs to path
sys.path.append('/app/libs')

from common.config import load_vertical
from common.schemas import TaskResult

app = FastAPI(
    title="Editorial Orchestrator",
    description="Control plane for editorial agent platform",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Celery setup
celery = Celery(
    __name__, 
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0")
)

# Load vertical configuration
try:
    cfg = load_vertical()
except Exception as e:
    print(f"Warning: Could not load vertical config: {e}")
    cfg = {"name": "generic"}

@app.on_event("startup")
async def schedule_jobs():
    """Schedule periodic discovery jobs."""
    try:
        # Schedule initial discovery
        celery.send_task(
            "tasks.discovery.plan_and_search", 
            args=[cfg],
            queue="discovery"
        )
        print("Scheduled initial discovery job")
    except Exception as e:
        print(f"Error scheduling jobs: {e}")

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy", "vertical": cfg.get("name", "unknown")}

@app.get("/")
def root():
    """Root endpoint."""
    return {
        "service": "Editorial Orchestrator",
        "version": "1.0.0",
        "vertical": cfg.get("name", "generic"),
        "endpoints": {
            "health": "/health",
            "trigger_discovery": "/trigger/discovery",
            "status": "/status"
        }
    }

@app.post("/trigger/discovery")
def trigger_discovery():
    """Manually trigger discovery process."""
    try:
        task = celery.send_task(
            "tasks.discovery.plan_and_search",
            args=[cfg],
            queue="discovery"
        )
        return {"task_id": task.id, "status": "queued"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
def get_status():
    """Get system status."""
    try:
        # Check Celery workers
        inspect = celery.control.inspect()
        active_workers = inspect.active()
        
        return {
            "vertical": cfg.get("name", "generic"),
            "workers": {
                "active": len(active_workers) if active_workers else 0,
                "queues": ["discovery", "intake", "understanding", "editorial", "ingestion"]
            },
            "config": {
                "discovery_queries": len(cfg.get("discovery", {}).get("queries", [])),
                "max_results": cfg.get("discovery", {}).get("max_results", 25),
                "collection": cfg.get("ingestion", {}).get("collection", "vertical_generic")
            }
        }
    except Exception as e:
        return {"error": str(e), "vertical": cfg.get("name", "generic")}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)