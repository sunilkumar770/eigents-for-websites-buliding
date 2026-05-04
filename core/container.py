
from typing import Dict, Any, Optional
from agents.base_agent import AgentType, BaseAgent
from core.contracts.agent_factory import AgentFactory

# Concrete implementations
from agents.product_interpreter_agent import ProductInterpreterAgent
from agents.frontend_engineer_agent import FrontendEngineerAgent
from agents.backend_engineer_agent import BackendEngineerAgent
from agents.integration_agent import IntegrationAgent
from agents.testing_agent import TestingAgent
from agents.debug_agent import DebugAgent
from agents.security_agent import SecurityAgent
from agents.production_readiness_agent import ProductionReadinessAgent

class SimpleAgentFactory(AgentFactory):
    def create_agent(self, agent_type: AgentType, config: Dict[str, Any] = None) -> BaseAgent:
        config = config or {}
        if agent_type == AgentType.PRODUCT_INTERPRETER:
            return ProductInterpreterAgent(config=config)
        elif agent_type == AgentType.FRONTEND_ENGINEER:
            return FrontendEngineerAgent(config=config)
        elif agent_type == AgentType.BACKEND_ENGINEER:
            return BackendEngineerAgent(config=config)
        elif agent_type == AgentType.INTEGRATION:
            return IntegrationAgent(config=config)
        elif agent_type == AgentType.TESTING:
            return TestingAgent(config=config)
        elif agent_type == AgentType.DEBUG:
            return DebugAgent(config=config)
        elif agent_type == AgentType.SECURITY:
            return SecurityAgent(config=config)
        elif agent_type == AgentType.PRODUCTION_READINESS:
            return ProductionReadinessAgent(config=config)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

class Container:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Container, cls).__new__(cls)
            cls._instance.factory = SimpleAgentFactory()
            cls._instance.registry: Dict[AgentType, BaseAgent] = {}
        return cls._instance

    def get_agent(self, agent_type: AgentType, config: Dict[str, Any] = None) -> BaseAgent:
        if agent_type not in self.registry:
            self.registry[agent_type] = self.factory.create_agent(agent_type, config)
        return self.registry[agent_type]

# Global singleton
container = Container()
