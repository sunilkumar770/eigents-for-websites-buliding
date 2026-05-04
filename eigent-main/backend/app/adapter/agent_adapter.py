# ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========= Copyright 2025-2026 @ Eigent.ai All Rights Reserved. =========

from typing import Any, Dict, Optional
from pydantic import BaseModel

from core.contracts.agent_protocols import AgentProtocol
from core.results.agent_lifecycle_result import ExecutionResult
from app.infrastructure.camel.listen_chat_agent import ListenChatAgent
from camel.messages import BaseMessage

class AgentAdapter(AgentProtocol):
    """Adapter to make ListenChatAgent compliant with AgentProtocol."""
    
    def __init__(self, agent: ListenChatAgent):
        self._agent = agent

    @property
    def agent_id(self) -> str:
        return self._agent.agent_id or ""

    @property
    def name(self) -> str:
        return self._agent.agent_name

    async def step(
        self, 
        input_data: Any, 
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        # Map input_data to BaseMessage if needed
        if isinstance(input_data, str):
            message = input_data
        else:
            message = str(input_data)
            
        response = await self._agent.astep(message)
        
        # Map ChatAgentResponse to ExecutionResult
        return ExecutionResult(
            success=True,
            output=response.msg.content if response.msg else "",
            metadata={
                "tokens": response.info.get("usage", {}).get("total_tokens", 0),
                "model": response.info.get("model_name", "")
            }
        )

    async def run(
        self, 
        task: Any, 
        initial_state: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        # For now, run is just a single step or a loop
        return await self.step(task)

    def get_state(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "memory_size": len(self._agent.memory.retrieve()) if self._agent.memory else 0
        }

    def set_state(self, state: Dict[str, Any]) -> None:
        # Implementation depends on what we want to restore
        pass
