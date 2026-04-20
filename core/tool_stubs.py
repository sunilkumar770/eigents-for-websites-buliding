"""
core/tool_stubs.py
Stub implementations for MCP tools, E2B sandbox, and tiered memory.
Replace each stub with a real SDK call when ready.
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict, List

from .agent_state import SandboxRun


# ── MCP Tool stub ─────────────────────────────────────────────────────────────

async def call_tool_async(tool_name: str, args: Dict[str, Any]) -> dict:
    """
    Placeholder for MCP client call.
    In production: route to an MCP server (filesystem, git, postgres, browser, etc.).

    Example real swap:
        from mcp import ClientSession
        async with ClientSession(...) as session:
            result = await session.call_tool(tool_name, args)
            return result
    """
    return {"tool": tool_name, "args": args, "result": "ok"}


# ── E2B sandbox stub ──────────────────────────────────────────────────────────

async def run_in_sandbox(module: str, source: str, tests: str) -> SandboxRun:
    """
    Stub for E2B code-interpreter sandbox execution.
    In production swap with:
        from e2b_code_interpreter import CodeInterpreter
        async with CodeInterpreter() as sandbox:
            exec_result = sandbox.notebook.exec_cell(f"{source}\n\n{tests}")
            return SandboxRun(
                module=module,
                stdout=exec_result.text or "",
                stderr=str(exec_result.error) if exec_result.error else "",
                exit_code=1 if exec_result.error else 0,
                duration_ms=...,
            )
    """
    # Simulate instant success – replace with real E2B call
    return SandboxRun(
        module=module,
        stdout="All tests passed (stub)",
        stderr="",
        exit_code=0,
        duration_ms=120,
    )


# ── Tiered memory stubs ───────────────────────────────────────────────────────

# Tier 1 – Working memory (in-process dict; replace with Redis for multi-process)
_working_memory: Dict[str, str] = {}


async def memory_store_async(key: str, value: str) -> None:
    """
    Stub: upsert a key-value pair into the memory store.
    In production: write to FAISS/Qdrant (episodic) + Graphiti/Zep (temporal KG).
    """
    _working_memory[key] = value


async def memory_retrieve_async(query: str, top_k: int = 5) -> List[str]:
    """
    Stub: retrieve top-k relevant memories for a query.
    In production: vector similarity search via FAISS/Qdrant + BM25 hybrid retrieval.
    """
    # Naive keyword match over working memory for now
    results = [
        v for k, v in _working_memory.items()
        if any(word.lower() in k.lower() for word in query.split()[:5])
    ]
    return results[:top_k]


async def memory_snapshot() -> Dict[str, Any]:
    """Return a snapshot of the current working memory (for debugging/dashboard)."""
    return {
        "entries": len(_working_memory),
        "keys": list(_working_memory.keys())[-20:],  # last 20
        "timestamp": time.time(),
    }
