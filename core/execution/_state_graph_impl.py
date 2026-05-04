
from __future__ import annotations
import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Generic
from core.contracts.graph_protocols import ExecutionGraph, NodeWrapper

TState = TypeVar("TState")

class NodeFunc(Generic[TState], NodeWrapper[TState]):
    def __init__(self, name: str, fn: Callable[[TState], Any]):
        self.name = name
        self.fn = fn

    async def __call__(self, state: TState) -> TState:
        res = self.fn(state)
        if asyncio.iscoroutine(res):
            return await res
        return res

class _SimpleStateGraphImpl(Generic[TState], ExecutionGraph[TState]):
    def __init__(self, terminal_statuses: set[str] = None):
        self.nodes: Dict[str, NodeFunc[TState]] = {}
        self.edges: List[Tuple[str, str]] = []
        self.conditionals: List[Tuple[str, Callable[[TState], str], Dict[str, str]]] = []
        self.entry_point: Optional[str] = None
        self.terminal_statuses = terminal_statuses or {"DONE", "FAILED"}
        self.logger = logging.getLogger("eigent.execution")

    def add_node(self, name: str, fn: Callable[[TState], Any]) -> None:
        self.nodes[name] = NodeFunc(name, fn)

    def set_entry_point(self, name: str) -> None:
        self.entry_point = name

    def add_edge(self, from_name: str, to_name: str) -> None:
        self.edges.append((from_name, to_name))

    def add_conditional_edges(
        self,
        from_name: str,
        condition_fn: Callable[[TState], str],
        mapping: Dict[str, str],
    ) -> None:
        self.conditionals.append((from_name, condition_fn, mapping))

    def _next_nodes(self, current: str, state: TState) -> List[str]:
        nexts: List[str] = []
        for frm, to in self.edges:
            if frm == current:
                nexts.append(to)
        for frm, cond_fn, mapping in self.conditionals:
            if frm == current:
                key = cond_fn(state)
                dest = mapping.get(key)
                if dest and dest not in nexts:
                    nexts.append(dest)
        return nexts

    async def ainvoke(self, initial_state: TState, config: Dict[str, Any] = None) -> TState:
        if not self.entry_point:
            raise RuntimeError("Graph has no entry point.")

        state = initial_state
        current = self.entry_point
        max_iterations = 100
        iterations = 0

        while current:
            # Check terminal status if state has one
            status = getattr(state, "status", None)
            if status in self.terminal_statuses:
                break
                
            if iterations >= max_iterations:
                self.logger.error(f"Graph exceeded {max_iterations} iterations.")
                if hasattr(state, "status"):
                    state.status = "FAILED"
                break

            node = self.nodes.get(current)
            if node is None:
                raise RuntimeError(f"Node '{current}' not found.")

            state = await node(state)
            iterations += 1
            nexts = self._next_nodes(current, state)
            current = nexts[0] if nexts else None

        return state
