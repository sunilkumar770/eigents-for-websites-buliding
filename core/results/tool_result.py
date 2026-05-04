
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

@dataclass
class ToolResult:
    tool_name: str
    success: bool
    output: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
