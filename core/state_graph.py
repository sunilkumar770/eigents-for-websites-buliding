"""
core/state_graph.py
Lightweight async StateGraph – a stand-in for LangGraph's StateGraph/CompiledGraph.
Sufficient for demo; swap the ainvoke() for a real LangGraph compiled graph when ready.
"""
from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional, Tuple

from .agent_state import AgentState


# ── Node wrapper ─────────────────────────────────────────────────────────────

class NodeFunc:
    """Thin wrapper that makes any async function callable as a graph node."""

    def __init__(self, name: str, fn: Callable):
        self.name = name
        self.fn = fn

    async def __call__(self, state: AgentState) -> AgentState:
        return await self.fn(state)

    def __repr__(self) -> str:
        return f"<Node:{self.name}>"


# ── StateGraph ────────────────────────────────────────────────────────────────

ConditionalEdge = Tuple[
    str,                    # from_node name
    Callable[[AgentState], str],  # condition fn  → key
    Dict[str, str],         # mapping: key → to_node name
]


class SimpleStateGraph:
    """
    Minimal async state-machine graph.

    Usage::
        sg = SimpleStateGraph()
        sg.add_node("supervisor", supervisor_node)
        sg.add_edge("supervisor", "planner")
        sg.add_conditional_edges("planner", lambda s: "OK", {"OK": "thinker"})
        sg.set_entry_point("supervisor")
        final_state = await sg.ainvoke(AgentState(task="..."))
    """

    TERMINAL_STATUSES = {"DONE", "FAILED"}

    def __init__(self):
        self.nodes: Dict[str, NodeFunc] = {}
        self.edges: List[Tuple[str, str]] = []          # (from, to)
        self.conditionals: List[ConditionalEdge] = []
        self.entry_point: Optional[str] = None
        # Build an adjacency map lazily after compile()
        self._adjacency: Optional[Dict[str, List[str]]] = None

    # ── Graph construction ─────────────────────────────────────────────────

    def add_node(self, name: str, fn: Callable) -> "SimpleStateGraph":
        self.nodes[name] = NodeFunc(name, fn)
        self._adjacency = None  # invalidate cache
        return self

    def set_entry_point(self, name: str) -> "SimpleStateGraph":
        self.entry_point = name
        return self

    def add_edge(self, from_name: str, to_name: str) -> "SimpleStateGraph":
        self.edges.append((from_name, to_name))
        return self

    def add_conditional_edges(
        self,
        from_name: str,
        condition_fn: Callable[[AgentState], str],
        mapping: Dict[str, str],
    ) -> "SimpleStateGraph":
        self.conditionals.append((from_name, condition_fn, mapping))
        return self

    # ── Sequential execution (BFS-like, follows declared edge order) ──────

    def _next_nodes(self, current: str, state: AgentState) -> List[str]:
        """Return the list of node names to run after `current`."""
        nexts: List[str] = []

        # Static edges
        for frm, to in self.edges:
            if frm == current:
                nexts.append(to)

        # Conditional edges (override static if both present – conditional wins)
        for frm, cond_fn, mapping in self.conditionals:
            if frm == current:
                key = cond_fn(state)
                dest = mapping.get(key)
                if dest and dest not in nexts:
                    nexts.append(dest)

        return nexts

    async def ainvoke(self, initial_state: AgentState) -> AgentState:
        """
        Run the graph to completion (DONE or FAILED) or until no more edges exist.
        Nodes are executed sequentially in the order: entry → edges → conditionals.
        """
        if not self.entry_point:
            raise RuntimeError("Graph has no entry point. Call set_entry_point() first.")

        state = initial_state
        current = self.entry_point

        # Safety valve: cap iterations to prevent infinite loops
        max_iterations = 50
        iterations = 0

        while current and state.status not in self.TERMINAL_STATUSES:
            if iterations >= max_iterations:
                import logging
                logging.getLogger("eigent.state_graph").error(
                    f"Graph exceeded {max_iterations} iterations – terminating."
                )
                state.status = "FAILED"
                break

            node = self.nodes.get(current)
            if node is None:
                raise RuntimeError(f"Node '{current}' not found in graph.")

            state = await node(state)
            iterations += 1

            # Determine next node
            nexts = self._next_nodes(current, state)
            current = nexts[0] if nexts else None  # take first for linear graphs

        return state
