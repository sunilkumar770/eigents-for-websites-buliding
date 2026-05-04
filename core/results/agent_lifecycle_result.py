
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class LifecycleResult:
    event: str  # 'START', 'STOP', 'PAUSE', 'RESUME'
    success: bool
    details: str = ""
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
