
from typing import Protocol, runtime_checkable, Any, Dict
from agents.base_agent import AgentType, BaseAgent

@runtime_checkable
class AgentFactory(Protocol):
    def create_agent(self, agent_type: AgentType, config: Dict[str, Any] = None) -> BaseAgent:
        ...
