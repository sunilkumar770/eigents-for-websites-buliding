
from dataclasses import dataclass, field
from typing import Dict, List, Any, Generic, TypeVar

T = TypeVar("T")

@dataclass
class ExecutionResult(Generic[T]):
    success: bool
    confidence: float
    payload: T
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'confidence': self.confidence,
            'payload': self.payload,
            'metadata': self.metadata,
            'errors': self.errors,
            'warnings': self.warnings,
            'duration': self.duration
        }
