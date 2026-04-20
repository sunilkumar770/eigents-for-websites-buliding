"""
fastapi_server.py
FastAPI REST wrapper for the Multi-Agent Framework v3.
Run: uvicorn fastapi_server.py:app --reload
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent_framework import run_task
from core.agent_state import AgentState

app = FastAPI(
    title="Eigent Multi-Agent Framework v3 API",
    description="Async LangGraph-style agentic workflow engine",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory history for the session
_task_history: List[Dict[str, Any]] = []


class TaskRequest(BaseModel):
    task: str


class TaskHistoryItem(BaseModel):
    task: str
    status: str
    timestamp: float


@app.post("/run", response_model=Dict[str, Any])
async def run_task_endpoint(req: TaskRequest):
    """
    Execute a new task synchronously (waits for graph completion).
    Returns the full AgentState JSON.
    """
    if not req.task.strip():
        raise HTTPException(status_code=400, detail="Task cannot be empty")
        
    try:
        start_time = time.time()
        state = await run_task(req.task)
        
        _task_history.append({
            "task": req.task,
            "status": state.status,
            "timestamp": start_time,
            "duration": time.time() - start_time
        })
        
        # Pydantic v2 .model_dump()
        return state.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph execution failed: {str(e)}")


@app.get("/history", response_model=List[Dict[str, Any]])
async def get_history():
    """Retrieve the last 20 tasks executed this session."""
    return _task_history[-20:]


@app.get("/health")
async def health():
    """Liveness check."""
    return {"status": "ok", "engine": "eigent-v3", "uptime": time.process_time()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
