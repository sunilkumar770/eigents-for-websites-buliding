
from abc import ABC, abstractmethod
from typing import Dict, Any

class RunnableTrait(ABC):
    @abstractmethod
    async def execute(self, inputs: Dict[str, Any]) -> Any:
        """Main async execution method"""
        pass
    
    @abstractmethod
    async def validate_inputs(self, inputs: Dict[str, Any]) -> tuple[bool, list[str]]:
        """Async input validation"""
        pass
