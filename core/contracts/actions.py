
from enum import Enum
from typing import Dict, Any, List, Optional, Union, Literal
from pydantic import BaseModel

class Action(str, Enum):
    # System Actions
    START = "start"
    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"
    END = "end"
    TIMEOUT = "timeout"
    
    # Task Lifecycle
    UPDATE_TASK = "update_task"
    TASK_STATE = "task_state"
    NEW_TASK_STATE = "new_task_state"
    DECOMPOSE_PROGRESS = "decompose_progress"
    DECOMPOSE_TEXT = "decompose_text"
    ASSIGN_TASK = "assign_task"
    SKIP_TASK = "skip_task"
    REMOVE_TASK = "remove_task"
    ADD_TASK = "add_task"
    
    # Agent Interaction
    CREATE_AGENT = "create_agent"
    ACTIVATE_AGENT = "activate_agent"
    DEACTIVATE_AGENT = "deactivate_agent"
    NEW_AGENT = "new_agent"
    ASK = "ask"
    NOTICE = "notice"
    SUPPLEMENT = "supplement"
    HUMAN_REPLY = "human_reply"
    
    # Tool/Infrastructure
    ACTIVATE_TOOLKIT = "activate_toolkit"
    DEACTIVATE_TOOLKIT = "deactivate_toolkit"
    WRITE_FILE = "write_file"
    SEARCH_MCP = "search_mcp"
    INSTALL_MCP = "install_mcp"
    TERMINAL = "terminal"
    
    # Misc
    IMPROVE = "improve"
    BUDGET_NOT_ENOUGH = "budget_not_enough"

class SSEPayload(BaseModel):
    action: Action
    task_id: Optional[str] = None
    data: Any = None
    timestamp: str = ""
    success: bool = True
    metadata: Dict[str, Any] = {}
