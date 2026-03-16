"""
Eigent MCP Server

Exposes the Eigent Hybrid Workflow (Kimi + Ollama) to Antigravity
and other MCP-compatible clients.
"""

from fastmcp import FastMCP
import sys
import os

# Add project root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from antigravity.llm.llm_router import route_task

# Initialize FastMCP
mcp = FastMCP("Eigent")

@mcp.tool()
def hybrid_reasoning(prompt: str, agent_type: str = "product_interpreter") -> str:
    """
    Useful for high-complexity architecture or deep debugging. 
    Routes tasks between Kimi K2.5 (complex) and local Ollama (fast).
    
    Args:
        prompt: The task or query to process.
        agent_type: Optional context (product_interpreter, architect, debug, testing).
    """
    print(f"🌀 Eigent Routing: {prompt[:50]}...")
    try:
        return route_task(prompt, agent_type=agent_type)
    except Exception as e:
        return f"Error routing task: {str(e)}"

@mcp.tool()
def list_routing_config() -> str:
    """Returns the current LLM routing table."""
    from antigravity.llm.setup_llm import build_llm_adapter
    from antigravity.llm.llm_router import MultiLLMRouter
    
    adapter = build_llm_adapter()
    if isinstance(adapter, MultiLLMRouter):
        table = adapter.get_routing_table()
        lines = [f"{k:20s} -> {v}" for k, v in table.items()]
        return "Eigent Routing Config:\n" + "\n".join(lines)
    return "Router not active (single LLM mode)."

if __name__ == "__main__":
    mcp.run(transport="stdio")
