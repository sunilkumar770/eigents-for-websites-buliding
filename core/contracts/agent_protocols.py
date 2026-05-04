from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

@runtime_checkable
class AgentProtocol(Protocol):
    """Base protocol for all agents in the system."""
    
    @property
    def agent_id(self) -> str:
        """Unique identifier for the agent."""
        ...

    @property
    def name(self) -> str:
        """Human-readable name of the agent."""
        ...

    async def step(
        self, 
        input_data: Any, 
        context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Perform a single step of reasoning/action."""
        ...

    async def run(
        self, 
        task: Any, 
        initial_state: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a full task until completion or failure."""
        ...

    def get_state(self) -> Dict[str, Any]:
        """Serialize current agent state."""
        ...

    def set_state(self, state: Dict[str, Any]) -> None:
        """Restore agent state from a dictionary."""
        ...


@runtime_checkable
class WorkforceProtocol(Protocol):
    """Protocol for managing a group of agents (Workforce)."""
    
    async def process_task(self, task: Any) -> Any:
        """Assign and execute a task using the workforce."""
        ...

    def add_agent(self, agent: AgentProtocol) -> None:
        """Add an agent to the workforce."""
        ...

    def remove_agent(self, agent_id: str) -> None:
        """Remove an agent by ID."""
        ...

    async def stop(self) -> None:
        """Stop all agents and cleanup."""
        ...


@runtime_checkable
class ResultProtocol(Protocol):
    """Protocol for standardized agent results."""
    
    @property
    def success(self) -> bool: ...
    
    @property
    def confidence(self) -> float: ...
    
    @property
    def outputs(self) -> Dict[str, Any]: ...
    
    @property
    def metadata(self) -> Dict[str, Any]: ...
    
    @property
    def errors(self) -> List[str]: ...
    
    @property
    def warnings(self) -> List[str]: ...
    
    @property
    def duration(self) -> float: ...
