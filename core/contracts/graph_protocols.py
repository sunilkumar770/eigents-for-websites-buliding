
from typing import Any, Dict, List, Protocol, runtime_checkable, TypeVar, Generic

TState = TypeVar("TState")

@runtime_checkable
class NodeWrapper(Protocol, Generic[TState]):
    async def __call__(self, state: TState) -> TState:
        ...

@runtime_checkable
class ExecutionGraph(Protocol, Generic[TState]):
    async def ainvoke(self, state: TState, config: Dict[str, Any] = None) -> TState:
        ...
    def add_node(self, name: str, node: NodeWrapper[TState]) -> None:
        ...
    def add_edge(self, source: str, target: str) -> None:
        ...
