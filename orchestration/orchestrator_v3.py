"""
orchestration/orchestrator_v3.py

Modernized orchestrator using the v3 StateGraph architecture.
Bridges the legacy project management API with the new async graph.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.execution.graph_compiler import compile_v3_graph
from core.agent_state import AgentState
from orchestration.state_manager import StateManager, WorkflowStatus, WorkflowState
from orchestration.message_bus import MessageBus, MessageType, get_message_bus

logger = logging.getLogger(__name__)

class OrchestratorV3:
    """
    v3 Orchestrator coordinating the StateGraph execution.
    """
    
    def __init__(
        self,
        state_manager: Optional[StateManager] = None,
        message_bus: Optional[MessageBus] = None
    ):
        self.state_manager = state_manager or StateManager()
        self.message_bus = message_bus or get_message_bus()
        self.graph = compile_v3_graph()
        logger.info("OrchestratorV3 initialized with v3 StateGraph")

    def create_project(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Create a new project and initialize v3 state."""
        project_id = str(uuid.uuid4())
        
        # Create legacy workflow entry for compatibility
        self.state_manager.create_workflow(
            project_id=project_id,
            prompt=prompt,
            context=context or {}
        )
        
        # Initial status event
        self.message_bus.publish(
            MessageType.WORKFLOW_STARTED,
            project_id=project_id,
            payload={'prompt': prompt},
            sender="orchestrator_v3"
        )
        
        logger.info(f"v3 Project {project_id} created.")
        return project_id

    async def arun(self, project_id: str):
        """Asynchronously run the graph for a project."""
        workflow = self.state_manager.get_workflow(project_id)
        if not workflow:
            logger.error(f"Project {project_id} not found for execution")
            return

        # Initialize v3 AgentState
        state = AgentState(
            task=workflow.prompt,
            full_requirements=workflow.context
        )

        try:
            # Update status to running
            workflow.status = WorkflowStatus.RUNNING
            self.state_manager.update_workflow(workflow)

            # Invoke the graph
            logger.info(f"Starting graph execution for project {project_id}")
            
            # We can iterate through the graph steps if we wanted more granular updates,
            # but for now we'll do an ainvoke. 
            # TODO: Add incremental checkpointing inside graph nodes.
            final_state = await self.graph.ainvoke(state)
            
            # Finalize workflow
            workflow.status = WorkflowStatus.COMPLETED
            workflow.stage_results = {
                "final_state": final_state.to_dict()
            }
            self.state_manager.update_workflow(workflow)
            
            self.message_bus.publish(
                MessageType.WORKFLOW_COMPLETED,
                project_id=project_id,
                payload={'status': 'completed'},
                sender="orchestrator_v3"
            )
            logger.info(f"v3 Project {project_id} completed successfully")

        except Exception as e:
            logger.error(f"Graph execution failed for {project_id}: {e}", exc_info=True)
            workflow.status = WorkflowStatus.FAILED
            workflow.errors.append(str(e))
            self.state_manager.update_workflow(workflow)
            
            self.message_bus.publish(
                MessageType.WORKFLOW_FAILED,
                project_id=project_id,
                payload={'error': str(e)},
                sender="orchestrator_v3"
            )

    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get status compatible with existing API."""
        workflow = self.state_manager.get_workflow(project_id)
        if not workflow:
            return {'error': 'Project not found'}
        
        return {
            'project_id': project_id,
            'status': workflow.status.value,
            'current_stage': workflow.current_stage,
            'prompt': workflow.prompt,
            'errors': workflow.errors,
            'created_at': workflow.created_at,
            'updated_at': workflow.updated_at
        }
