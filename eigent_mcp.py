"""
Eigent MCP Server

Exposes the Eigent Hybrid Workflow (Kimi + Ollama) to Antigravity
and other MCP-compatible clients.
"""

from fastmcp import FastMCP
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from orchestration.orchestrator_v3 import OrchestratorV3
from core.model_caller import call_model_async
import asyncio

# Initialize FastMCP
mcp = FastMCP("Eigent")

# Shared orchestrator instance
orch = OrchestratorV3()

@mcp.tool()
async def hybrid_reasoning(prompt: str, agent_role: str = "glm-nim") -> str:
    """
    Direct access to specialized NVIDIA NIM models (glm-nim, minimax-nim, kimi-nim, nemotron).
    Useful for architectural queries or deep code reasoning.
    """
    try:
        resp = await call_model_async(agent_role, [{"role": "user", "content": prompt}])
        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error in reasoning: {str(e)}"

@mcp.tool()
async def generate_project(prompt: str, context: str = "{}") -> str:
    """
    Triggers the full Eigent v3 Multi-Agent graph to build a project from a description.
    Runs in the background and returns a Project ID.
    """
    import json
    try:
        ctx_dict = json.loads(context)
        project_id = orch.create_project(prompt, ctx_dict)
        # Trigger background execution
        asyncio.create_task(orch.arun(project_id))
        return f"🚀 Project generation started! ID: {project_id}\nYou can check status using get_project_status."
    except Exception as e:
        return f"Error starting project: {str(e)}"

@mcp.tool()
def get_project_status(project_id: str) -> str:
    """
    Checks the status and current stage of an Eigent project.
    """
    status = orch.get_project_status(project_id)
    if 'error' in status:
        return f"❌ {status['error']}"
    
    return (
        f"📊 Project Status: {status['status'].upper()}\n"
        f"📍 Stage: {status['current_stage']}\n"
        f"📝 Prompt: {status['prompt'][:100]}...\n"
        f"⚠️ Errors: {', '.join(status['errors']) if status['errors'] else 'None'}"
    )

@mcp.tool()
def list_nim_models() -> str:
    """Returns the available NVIDIA NIM models in the framework."""
    return "Eigent NIM Stack: minimax-nim (Planner), glm-nim (Coder), kimi-nim (Security), nemotron (Debug)"

if __name__ == "__main__":
    mcp.run(transport="stdio")
