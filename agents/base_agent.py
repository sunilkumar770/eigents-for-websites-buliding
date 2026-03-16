"""
Base Agent

Foundation class for all agents in the multi-agent system.
"""

import logging
import time
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


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
    Abstract base class for all agents in the multi-agent system.
    
    All specialized agents must inherit from this class and implement
    the required abstract methods.
    """
    
    def __init__(
        self,
        agent_type: AgentType,
        llm_adapter: Any,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize base agent
        
        Args:
            agent_type: Type of agent
            llm_adapter: LLM adapter (e.g., KimiAdapter)
            config: Agent-specific configuration
        """
        self.agent_type = agent_type
        self.llm_adapter = llm_adapter
        self.config = config or {}
        self.logger = logging.getLogger(f"Agent.{agent_type.value}")
        
        # State management
        self.state = {
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_confidence': 0.0,
            'last_execution': None
        }
        
        # Confidence threshold (can be overridden by subclasses)
        self.confidence_threshold = self.config.get('confidence_threshold', 90.0)
        
        # Retry configuration
        self.max_retries = self.config.get('max_retries', 3)
        
        self.logger.info(f"Initialized {agent_type.value} agent")
    
    @abstractmethod
    def execute(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Main execution method - must be implemented by subclasses
        
        Args:
            inputs: Input data for the agent
        
        Returns:
            AgentResult with outputs and metadata
        """
        pass
    
    @abstractmethod
    def validate_inputs(self, inputs: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate input data
        
        Args:
            inputs: Input data to validate
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        pass
    
    def execute_with_retry(self, inputs: Dict[str, Any]) -> AgentResult:
        """
        Execute task with automatic retry logic
        
        Args:
            inputs: Input data for the agent
        
        Returns:
            AgentResult
        """
        start_time = time.time()
        attempt = 0
        last_error = None
        
        while attempt < self.max_retries:
            try:
                self.logger.info(f"Executing task (attempt {attempt + 1}/{self.max_retries})")
                
                # Validate inputs
                is_valid, errors = self.validate_inputs(inputs)
                if not is_valid:
                    return AgentResult(
                        success=False,
                        confidence=0.0,
                        outputs={},
                        errors=errors,
                        duration=time.time() - start_time
                    )
                
                # Execute main task
                result = self.execute(inputs)
                result.duration = time.time() - start_time
                
                # Check confidence threshold
                if result.success and result.confidence >= self.confidence_threshold:
                    self._update_state(success=True, confidence=result.confidence)
                    self.logger.info(f"Task completed successfully (confidence: {result.confidence}%)")
                    return result
                elif result.success:
                    # Success but low confidence
                    warning = f"Low confidence: {result.confidence}% < {self.confidence_threshold}%"
                    result.warnings.append(warning)
                    self.logger.warning(warning)
                    
                    if attempt < self.max_retries - 1:
                        attempt += 1
                        continue
                    else:
                        return result
                else:
                    # Failed execution
                    last_error = result.errors
                    attempt += 1
                    
            except Exception as e:
                self.logger.error(f"Exception during execution: {str(e)}", exc_info=True)
                last_error = [str(e)]
                attempt += 1
        
        # All retries exhausted
        self._update_state(success=False, confidence=0.0)
        return AgentResult(
            success=False,
            confidence=0.0,
            outputs={},
            errors=last_error or ["Max retries exceeded"],
            duration=time.time() - start_time
        )
    
    def _update_state(self, success: bool, confidence: float):
        """Update internal state tracking"""
        if success:
            self.state['tasks_completed'] += 1
            self.state['total_confidence'] += confidence
        else:
            self.state['tasks_failed'] += 1
        
        self.state['last_execution'] = datetime.now().isoformat()
    
    def get_average_confidence(self) -> float:
        """Get average confidence across all completed tasks"""
        if self.state['tasks_completed'] == 0:
            return 0.0
        return self.state['total_confidence'] / self.state['tasks_completed']
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            'agent_type': self.agent_type.value,
            'tasks_completed': self.state['tasks_completed'],
            'tasks_failed': self.state['tasks_failed'],
            'average_confidence': self.get_average_confidence(),
            'last_execution': self.state['last_execution']
        }
    
    def _call_llm(
        self,
        prompt: str,
        system_context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> str:
        """
        Helper method to call LLM
        
        Args:
            prompt: User prompt
            system_context: System context (prepended to user message)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        
        Returns:
            LLM response text
        """
        # Build message
        if system_context:
            message = f"[SYSTEM CONTEXT: {system_context}]\n\n{prompt}"
        else:
            message = prompt
        
        messages = [{"role": "user", "content": message}]
        
        # Call LLM with agent type for rate limiting
        response = self.llm_adapter.chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
            agent_type=self.agent_type.value  # Pass agent type for tracking
        )
        
        # Extract content
        # Handle different response types (string content or API response dict)
        if isinstance(response, str):
            content = response
        elif isinstance(response, dict) and "choices" in response:
            content = response["choices"][0]["message"]["content"]
        else:
            # Fallback or unknown format
            content = str(response)
        return content
    
    def _parse_json_from_llm(self, llm_response: str) -> Optional[Dict[str, Any]]:
        """
        Extract and parse JSON from LLM response
        
        Args:
            llm_response: Raw LLM response
        
        Returns:
            Parsed JSON dict or None if parsing fails
        """
        try:
            # Try to find JSON in code blocks
            if "```json" in llm_response:
                start = llm_response.find("```json") + 7
                end = llm_response.find("```", start)
                json_str = llm_response[start:end].strip()
            elif "```" in llm_response:
                start = llm_response.find("```") + 3
                end = llm_response.find("```", start)
                json_str = llm_response[start:end].strip()
            else:
                # Try to parse entire response
                json_str = llm_response.strip()
            
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON from LLM response: {e}")
            return None

    def _extract_code_from_llm(self, llm_response: str) -> str:
        """
        Extract code from LLM response (markdown blocks or raw text)
        
        Args:
            llm_response: Raw LLM response
            
        Returns:
            Extracted code string
        """
        if "```" in llm_response:
            # Find all code blocks
            import re
            code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", llm_response, re.DOTALL)
            if code_blocks:
                return "\n\n".join(code_blocks).strip()
            
            # Fallback to simple extraction if regex fails or format is weird
            start = llm_response.find("```")
            # Skip language identifier if present
            newline = llm_response.find("\n", start)
            if newline != -1 and newline < start + 20:
                start = newline + 1
            else:
                start += 3
                
            end = llm_response.rfind("```")
            if end > start:
                return llm_response[start:end].strip()
        
        # valid fallback: return clean response
        return llm_response.strip()
    
    def _calculate_confidence(
        self,
        criteria: Dict[str, bool],
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calculate confidence score based on criteria
        
        Args:
            criteria: Dict of criterion_name -> passed (bool)
            weights: Optional weights for each criterion (default: equal weights)
        
        Returns:
            Confidence score (0-100)
        """
        if not criteria:
            return 0.0
        
        if weights is None:
            # Equal weights
            weights = {k: 1.0 for k in criteria.keys()}
        
        total_weight = sum(weights.values())
        weighted_score = sum(
            weights.get(k, 1.0) for k, v in criteria.items() if v
        )
        
        return (weighted_score / total_weight) * 100.0
    
    def log_decision(self, decision: str, reasoning: str):
        """
        Log an agent decision with reasoning
        
        Args:
            decision: The decision made
            reasoning: Reasoning behind the decision
        """
        self.logger.info(f"DECISION: {decision}")
        self.logger.info(f"REASONING: {reasoning}")
    
    def should_escalate(self, result: AgentResult) -> bool:
        """
        Determine if task should be escalated to human
        
        Args:
            result: Agent result
        
        Returns:
            True if should escalate
        """
        # Escalate if failed after all retries
        if not result.success:
            return True
        
        # Escalate if confidence is critically low
        if result.confidence < 50.0:
            return True
        
        # Escalate if there are critical errors
        critical_keywords = ['critical', 'security', 'data loss', 'corruption']
        for error in result.errors:
            if any(keyword in error.lower() for keyword in critical_keywords):
                return True
        
        return False


class AgentRegistry:
    """Registry to manage all agents in the system"""
    
    def __init__(self):
        self.agents: Dict[AgentType, BaseAgent] = {}
        self.logger = logging.getLogger("AgentRegistry")
    
    def register(self, agent: BaseAgent):
        """Register an agent"""
        self.agents[agent.agent_type] = agent
        self.logger.info(f"Registered agent: {agent.agent_type.value}")
    
    def get(self, agent_type: AgentType) -> Optional[BaseAgent]:
        """Get an agent by type"""
        return self.agents.get(agent_type)
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all agents"""
        return {
            agent_type.value: agent.get_stats()
            for agent_type, agent in self.agents.items()
        }


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
