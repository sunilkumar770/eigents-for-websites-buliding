"""
Base Agent (Async v3)

Foundation class for all agents in the multi-agent system.
Updated for the v3 Async/Graph architecture.
"""

import logging
import time
import json
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# Import v3 core components
from core.model_caller import call_model_async


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class AgentType(Enum):
    """Types of agents in the system"""
    PRODUCT_INTERPRETER = "product_interpreter"
    FRONTEND_ENGINEER = "frontend_engineer"
    BACKEND_ENGINEER = "backend_engineer"
    INTEGRATION = "integration"
    TESTING = "testing"
    DEBUG = "debug"
    SECURITY = "security"
    PRODUCTION_READINESS = "production_readiness"


class TaskStatus(Enum):
    """Status of agent tasks"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class AgentMessage:
    """Message format for inter-agent communication"""
    id: str
    timestamp: str
    from_agent: AgentType
    to_agent: Optional[AgentType]
    message_type: str  # 'TASK', 'RESULT', 'ERROR', 'QUERY'
    payload: Dict[str, Any]
    priority: str = "MEDIUM"  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    retry_count: int = 0


@dataclass
class AgentResult:
    """Standardized result format from agent execution"""
    success: bool
    confidence: float  # 0-100
    outputs: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration: float = 0.0  # seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'success': self.success,
            'confidence': self.confidence,
            'outputs': self.outputs,
            'metadata': self.metadata,
            'errors': self.errors,
            'warnings': self.warnings,
            'duration': self.duration
        }


class BaseAgent(ABC):
    """
    Abstract async base class for all agents in the multi-agent system.
    """
    
    def __init__(
        self,
        agent_type: AgentType,
        config: Optional[Dict[str, Any]] = None,
        llm_adapter: Any = None # Keep for compat, but we prefer call_model_async
    ):
        """
        Initialize base agent
        """
        self.agent_type = agent_type
        self.config = config or {}
        self.llm_adapter = llm_adapter # Legacy, can be None
        self.logger = logging.getLogger(f"Agent.{agent_type.value}")
        
        # State management
        self.state = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_confidence': 0.0,
            'last_execution': None
        }
        
        self.confidence_threshold = self.config.get('confidence_threshold', 90.0)
        self.max_retries = self.config.get('max_retries', 3)
        
        self.logger.info(f"Initialized {agent_type.value} agent (Async v3)")
    
    @abstractmethod
    async def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """Main async execution method"""
        pass
    
    @abstractmethod
    async def validate_inputs(self, inputs: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Async input validation"""
        pass
    
    async def execute_with_retry(self, inputs: Dict[str, Any]) -> AgentResult:
        """Execute task with async retry logic"""
        start_time = time.time()
        attempt = 0
        last_error = None
        
        while attempt < self.max_retries:
            try:
                self.logger.info(f"Executing task (attempt {attempt + 1}/{self.max_retries})")
                
                # Validate inputs
                is_valid, errors = await self.validate_inputs(inputs)
                if not is_valid:
                    return AgentResult(
                        success=False,
                        confidence=0.0,
                        outputs={},
                        errors=errors,
                        duration=time.time() - start_time
                    )
                
                # Execute main task
                result = await self.execute(inputs)
                result.duration = time.time() - start_time
                
                # Check confidence threshold
                if result.success and result.confidence >= self.confidence_threshold:
                    self._update_state(success=True, confidence=result.confidence)
                    return result
                elif result.success:
                    self.logger.warning(f"Low confidence: {result.confidence}% < {self.confidence_threshold}%")
                    if attempt < self.max_retries - 1:
                        attempt += 1
                        continue
                    return result
                else:
                    last_error = result.errors
                    attempt += 1
                    
            except Exception as e:
                self.logger.error(f"Exception: {str(e)}", exc_info=True)
                last_error = [str(e)]
                attempt += 1
        
        self._update_state(success=False, confidence=0.0)
        return AgentResult(
            success=False,
            confidence=0.0,
            outputs={},
            errors=last_error or ["Max retries exceeded"],
            duration=time.time() - start_time
        )
    
    def _update_state(self, success: bool, confidence: float):
        self.state['tasks_completed'] += 1 if success else 0
        if success: self.state['total_confidence'] += confidence
        else: self.state['tasks_failed'] += 1
        self.state['last_execution'] = datetime.now().isoformat()
    
    async def _call_llm(
        self,
        prompt: str,
        system_context: Optional[str] = None,
        role: str = "general", # Maps to v3 model mapping
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """Integrated with v3 call_model_async"""
        messages = []
        if system_context:
            messages.append({"role": "system", "content": system_context})
        messages.append({"role": "user", "content": prompt})
        
        # In v3, we map agent types to model roles:
        role_map = {
            AgentType.PRODUCT_INTERPRETER: "minimax-nim",
            AgentType.FRONTEND_ENGINEER: "glm-nim",
            AgentType.BACKEND_ENGINEER: "glm-nim",
            AgentType.DEBUG: "nemotron",
            AgentType.SECURITY: "kimi-nim"
        }
        
        model_name = role_map.get(self.agent_type, "gemma")
        
        resp = await call_model_async(
            model_name,
            messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return resp["choices"][0]["message"]["content"]
    
    def _parse_json_from_llm(self, llm_response: str) -> Optional[Dict[str, Any]]:
        try:
            import re
            match = re.search(r"\{.*\}", llm_response, re.DOTALL)
            return json.loads(match.group(0)) if match else json.loads(llm_response)
        except Exception as e:
            self.logger.error(f"JSON Parse fail: {e}")
            return None

    def _extract_code_from_llm(self, llm_response: str) -> str:
        if "```" in llm_response:
            import re
            code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", llm_response, re.DOTALL)
            return "\n\n".join(code_blocks).strip() if code_blocks else llm_response.strip()
        return llm_response.strip()
    
    def _calculate_confidence(self, criteria: Dict[str, bool], weights: Optional[Dict[str, float]] = None) -> float:
        if not criteria: return 0.0
        w = weights or {k: 1.0 for k in criteria.keys()}
        total = sum(w.values())
        score = sum(w.get(k, 1.0) for k, v in criteria.items() if v)
        return (score / total) * 100.0

    def log_decision(self, decision: str, reasoning: str):
        self.logger.info(f"DECISION: {decision} | REASONING: {reasoning}")


class AgentRegistry:
    def __init__(self):
        self.agents: Dict[AgentType, BaseAgent] = {}
    def register(self, agent: BaseAgent):
        self.agents[agent.agent_type] = agent
    def get(self, agent_type: AgentType) -> Optional[BaseAgent]:
        return self.agents.get(agent_type)


if __name__ == '__main__':
    # Example usage
    from antigravity.llm.kimi_adapter import KimiAdapter
    
    # This would be implemented by a concrete agent
    class ExampleAgent(BaseAgent):
        def execute(self, inputs: Dict[str, Any]) -> AgentResult:
            # Dummy implementation
            return AgentResult(
                success=True,
                confidence=95.0,
                outputs={'result': 'example'}
            )
        
        def validate_inputs(self, inputs: Dict[str, Any]) -> Tuple[bool, List[str]]:
            return True, []
    
    adapter = KimiAdapter(api_key="MOCK_KEY")
    agent = ExampleAgent(AgentType.PRODUCT_INTERPRETER, adapter)
    
    result = agent.execute_with_retry({'test': 'input'})
    print(f"Success: {result.success}, Confidence: {result.confidence}%")
