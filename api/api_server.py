"""
API Server

REST API server using FastAPI for the multi-agent system.
"""

import sys
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio
import json
import logging

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from orchestration.workflow_orchestrator import WorkflowOrchestrator
from orchestration.message_bus import MessageType, get_message_bus
from orchestration.state_manager import WorkflowStatus


# Pydantic models for request/response
class CreateProjectRequest(BaseModel):
    prompt: str = Field(..., description="Product idea description")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")


class ProjectResponse(BaseModel):
    project_id: str
    status: str
    current_stage: str
    prompt: str
    created_at: str


class ProjectStatusResponse(BaseModel):
    project_id: str
    status: str
    current_stage: str
    prompt: str
    stages: List[Dict[str, Any]]
    pending_tasks: int
    running_tasks: int
    errors: List[str]
    created_at: str
    updated_at: str


class RetryStageRequest(BaseModel):
    stage_name: str = Field(..., description="Stage to retry")


# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent Web Development System",
    description="API for autonomous web application generation",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
orchestrator: Optional[WorkflowOrchestrator] = None
message_bus = get_message_bus()

# WebSocket connections
active_connections: Dict[str, List[WebSocket]] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize orchestrator on startup with multi-LLM support"""
    global orchestrator

    # Auto-detect and build the best available LLM adapter:
    # - Kimi K2.5 (NVIDIA API) if NVIDIA_API_KEY is set
    # - Ollama (local)          if Ollama is running
    # - MultiLLMRouter          if both are available (recommended)
    from antigravity.llm.setup_llm import build_llm_adapter
    adapter = build_llm_adapter()
    
    # Initialize orchestrator
    orchestrator = WorkflowOrchestrator(llm_adapter=adapter)
    
    # Subscribe to message bus for WebSocket updates
    message_bus.subscribe(MessageType.TASK_STARTED, broadcast_message)
    message_bus.subscribe(MessageType.TASK_COMPLETED, broadcast_message)
    message_bus.subscribe(MessageType.TASK_FAILED, broadcast_message)
    message_bus.subscribe(MessageType.WORKFLOW_COMPLETED, broadcast_message)
    message_bus.subscribe(MessageType.WORKFLOW_FAILED, broadcast_message)
    
    logging.info("API server started")


def broadcast_message(message):
    """Broadcast message to WebSocket clients"""
    project_id = message.project_id
    
    if project_id in active_connections:
        message_data = {
            'type': message.message_type.value,
            'payload': message.payload,
            'timestamp': message.timestamp
        }
        
        # Send to all connected clients for this project
        for connection in active_connections[project_id]:
            try:
                asyncio.create_task(
                    connection.send_json(message_data)
                )
            except Exception as e:
                logging.error(f"Error broadcasting to WebSocket: {e}")


async def process_workflow_background(project_id: str):
    """Process workflow in background"""
    try:
        orchestrator.run(max_iterations=50)
    except Exception as e:
        logging.error(f"Error processing workflow {project_id}: {e}", exc_info=True)


@app.post("/projects", response_model=ProjectResponse)
async def create_project(
    request: CreateProjectRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a new project from a prompt.
    
    The workflow will be processed in the background.
    """
    try:
        project_id = orchestrator.create_project(
            prompt=request.prompt,
            context=request.context
        )
        
        # Process workflow in background
        background_tasks.add_task(process_workflow_background, project_id)
        
        # Get initial status
        workflow = orchestrator.state_manager.get_workflow(project_id)
        
        return ProjectResponse(
            project_id=project_id,
            status=workflow.status.value,
            current_stage=workflow.current_stage,
            prompt=workflow.prompt,
            created_at=workflow.created_at
        )
    
    except Exception as e:
        logging.error(f"Error creating project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects/{project_id}", response_model=ProjectStatusResponse)
async def get_project_status(project_id: str):
    """Get project status"""
    try:
        status = orchestrator.get_project_status(project_id)
        
        if 'error' in status:
            raise HTTPException(status_code=404, detail=status['error'])
        
        return ProjectStatusResponse(**status)
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting project status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects")
async def list_projects(
    status: Optional[str] = None,
    limit: int = 100
):
    """List all projects with optional status filter"""
    try:
        workflow_status = WorkflowStatus(status) if status else None
        workflows = orchestrator.state_manager.list_workflows(
            status=workflow_status,
            limit=limit
        )
        
        return [
            {
                'project_id': w.project_id,
                'status': w.status.value,
                'current_stage': w.current_stage,
                'prompt': w.prompt,
                'created_at': w.created_at,
                'updated_at': w.updated_at
            }
            for w in workflows
        ]
    
    except Exception as e:
        logging.error(f"Error listing projects: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/projects/{project_id}/progress")
async def stream_progress(project_id: str):
    """
    Stream project progress using Server-Sent Events.
    
    Returns real-time updates as the workflow progresses.
    """
    async def event_generator():
        # Check if project exists
        workflow = orchestrator.state_manager.get_workflow(project_id)
        if not workflow:
            yield f"data: {json.dumps({'error': 'Project not found'})}\n\n"
            return
        
        # Send initial status
        status = orchestrator.get_project_status(project_id)
        yield f"data: {json.dumps(status)}\n\n"
        
        # Stream updates while workflow is running
        while True:
            await asyncio.sleep(2)  # Poll every 2 seconds
            
            status = orchestrator.get_project_status(project_id)
            yield f"data: {json.dumps(status)}\n\n"
            
            # Stop streaming when workflow is complete or failed
            if status['status'] in ['completed', 'failed', 'cancelled']:
                break
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@app.get("/projects/{project_id}/artifacts")
async def download_artifacts(project_id: str):
    """
    Download generated code artifacts.
    
    Returns a JSON object with all generated files.
    """
    try:
        workflow = orchestrator.state_manager.get_workflow(project_id)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Allow downloading partial artifacts even if not completed
        # if workflow.status != WorkflowStatus.COMPLETED:
        #     raise HTTPException(
        #         status_code=400,
        #         detail=f"Project not completed (status: {workflow.status.value})"
        #     )
        
        # Collect all generated files
        results = workflow.stage_results
        artifacts = {}
        
        if 'frontend_generation' in results:
            artifacts['frontend'] = results['frontend_generation'].get('code_files', {})
        
        if 'backend_generation' in results:
            artifacts['backend'] = results['backend_generation'].get('code_files', {})
        
        if 'integration' in results:
            artifacts['integration'] = results['integration'].get('api_client_code', {})
        
        return JSONResponse(content=artifacts)
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error downloading artifacts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/projects/{project_id}/retry")
async def retry_stage(
    project_id: str,
    request: RetryStageRequest,
    background_tasks: BackgroundTasks
):
    """
    Retry a failed stage.
    
    This will re-enqueue the specified stage and resume processing.
    """
    try:
        workflow = orchestrator.state_manager.get_workflow(project_id)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # TODO: Implement retry logic
        # For now, just return success
        
        return {"message": f"Retry initiated for stage {request.stage_name}"}
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error retrying stage: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    try:
        workflow = orchestrator.state_manager.get_workflow(project_id)
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Cancel any pending tasks
        tasks = orchestrator.task_queue.get_project_tasks(project_id)
        for task in tasks:
            if task.status.value == 'pending':
                orchestrator.task_queue.cancel_task(task.task_id)
        
        # Delete workflow
        orchestrator.state_manager.delete_workflow(project_id)
        
        # Clear message history
        message_bus.clear_history(project_id)
        
        return {"message": f"Project {project_id} deleted"}
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/projects/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """
    WebSocket endpoint for real-time project updates.
    
    Clients can connect to receive live updates as the workflow progresses.
    """
    await websocket.accept()
    
    # Add to active connections
    if project_id not in active_connections:
        active_connections[project_id] = []
    active_connections[project_id].append(websocket)
    
    try:
        # Send initial status
        status = orchestrator.get_project_status(project_id)
        await websocket.send_json(status)
        
        # Keep connection alive
        while True:
            # Wait for messages from client (ping/pong)
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_text("pong")
    
    except WebSocketDisconnect:
        # Remove from active connections
        active_connections[project_id].remove(websocket)
        if not active_connections[project_id]:
            del active_connections[project_id]
    
    except Exception as e:
        logging.error(f"WebSocket error: {e}", exc_info=True)


@app.get("/api/agents/status")
async def get_agents_status():
    """
    Get current status of all agents
    
    Returns:
        Dict with agent status (idle, busy, offline)
    """
    try:
        # Get rate limiter metrics to see active calls
        from orchestration.rate_limiter import get_rate_limiter
        rate_limiter = get_rate_limiter()
        metrics = rate_limiter.get_metrics()
        
        # Get all agent types
        from agents.base_agent import AgentType
        
        # Build agent status
        agent_status = {}
        for agent_type in AgentType:
            agent_name = agent_type.value
            
            # Check if this agent has an active API call
            is_busy = any(
                call['agent_type'] == agent_name 
                for call in metrics['active_calls']
            )
            
            # Get agent stats if available
            agent_stats = {'status': 'busy' if is_busy else 'idle'}
            
            if hasattr(orchestrator, 'agents') and agent_type in orchestrator.agents:
                agent = orchestrator.agents[agent_type]
                agent_stats.update(agent.get_stats())
            
            agent_status[agent_name] = agent_stats
        
        return {
            'agents': agent_status,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logging.error(f"Error getting agent status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metrics/realtime")
async def get_realtime_metrics():
    """
    Get real-time system metrics
    
    Returns:
        Dict with API rates, queue depth, throughput, etc.
    """
    try:
        from orchestration.rate_limiter import get_rate_limiter
        rate_limiter = get_rate_limiter()
        
        # Get rate limiter metrics
        rate_metrics = rate_limiter.get_metrics()
        
        # Get workflow and task stats
        workflow_stats = orchestrator.state_manager.get_statistics() if hasattr(orchestrator.state_manager, 'get_statistics') else {}
        task_stats = orchestrator.task_queue.get_statistics() if hasattr(orchestrator.task_queue, 'get_statistics') else {}
        
        return {
            'rate_limiter': rate_metrics,
            'workflows': workflow_stats,
            'tasks': task_stats,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logging.error(f"Error getting realtime metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}/history")
async def get_project_history(project_id: str, limit: int = 50):
    """
    Get agent interaction history for a project
    
    Args:
        project_id: Project ID
        limit: Maximum number of events to return
    
    Returns:
        List of agent interaction events
    """
    try:
        workflow = orchestrator.state_manager.get_workflow(project_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get message history for this project
        history = message_bus.get_history(project_id, limit=limit) if hasattr(message_bus, 'get_history') else []
        
        # Get stage history
        stages = orchestrator.state_manager.get_stages(project_id)
        stage_events = [
            {
                'type': 'stage',
                'stage_name': s.stage_name,
                'status': s.status.value,
                'agent_type': s.agent_type,
                'confidence': s.confidence,
                'started_at': s.started_at,
                'completed_at': s.completed_at
            }
            for s in stages
        ]
        
        return {
            'project_id': project_id,
            'events': history,
            'stages': stage_events,
            'timestamp': datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting project history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/stats")
async def get_statistics():
    """Get system statistics"""
    try:
        return {
            'workflows': orchestrator.state_manager.get_statistics(),
            'tasks': orchestrator.task_queue.get_statistics(),
            'messages': message_bus.get_statistics()
        }
    except Exception as e:
        logging.error(f"Error getting statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
