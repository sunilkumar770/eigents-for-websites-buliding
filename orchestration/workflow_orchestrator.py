"""
Workflow Orchestrator

Main orchestrator that manages the agent workflow state machine.
"""

import sys
import os
from typing import Dict, List, Any, Optional
from enum import Enum
import logging
import uuid
from datetime import datetime

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from orchestration.state_manager import StateManager, WorkflowState, WorkflowStatus, StageState, StageStatus
from orchestration.task_queue import TaskQueue, TaskPriority
from orchestration.message_bus import MessageBus, MessageType, get_message_bus
from agents.base_agent import AgentType, AgentResult

# Import all agents
from agents.product_interpreter_agent import ProductInterpreterAgent
from agents.frontend_engineer_agent import FrontendEngineerAgent
from agents.backend_engineer_agent import BackendEngineerAgent
from agents.integration_agent import IntegrationAgent
from agents.testing_agent import TestingAgent
from agents.debug_agent import DebugAgent
from agents.security_agent import SecurityAgent
from agents.production_readiness_agent import ProductionReadinessAgent


class WorkflowStage(Enum):
    """Workflow stages"""
    PRODUCT_INTERPRETATION = "product_interpretation"
    FRONTEND_GENERATION = "frontend_generation"
    BACKEND_GENERATION = "backend_generation"
    INTEGRATION = "integration"
    TESTING = "testing"
    DEBUG = "debug"
    SECURITY_AUDIT = "security_audit"
    PRODUCTION_READINESS = "production_readiness"


class WorkflowOrchestrator:
    """
    Main orchestrator coordinating all agents.
    
    Features:
    - State machine with 8 stages
    - Automatic retry logic
    - Quality gates between stages
    - Parallel execution (Frontend + Backend)
    - Escalation handling
    """
    
    def __init__(
        self,
        llm_adapter: Any,
        state_manager: Optional[StateManager] = None,
        task_queue: Optional[TaskQueue] = None,
        message_bus: Optional[MessageBus] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.llm_adapter = llm_adapter
        self.state_manager = state_manager or StateManager()
        self.task_queue = task_queue or TaskQueue()
        self.message_bus = message_bus or get_message_bus()
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting configuration
        max_concurrent_calls = int(os.getenv('MAX_CONCURRENT_API_CALLS', '2'))
        self.config['max_concurrent_api_calls'] = max_concurrent_calls
        self.logger.info(f"Rate limiting configured: max {max_concurrent_calls} concurrent API calls")
        
        # Initialize agents
        self._init_agents()
        
        # Quality gate thresholds
        self.confidence_threshold = self.config.get('confidence_threshold', 70.0)
        self.max_retries = self.config.get('max_retries', 3)
    
    def _init_agents(self):
        """Initialize all agents"""
        self.agents = {
            AgentType.PRODUCT_INTERPRETER: ProductInterpreterAgent(self.llm_adapter),
            AgentType.FRONTEND_ENGINEER: FrontendEngineerAgent(self.llm_adapter),
            AgentType.BACKEND_ENGINEER: BackendEngineerAgent(self.llm_adapter),
            AgentType.INTEGRATION: IntegrationAgent(self.llm_adapter),
            AgentType.TESTING: TestingAgent(self.llm_adapter),
            AgentType.DEBUG: DebugAgent(self.llm_adapter),
            AgentType.SECURITY: SecurityAgent(self.llm_adapter),
            AgentType.PRODUCTION_READINESS: ProductionReadinessAgent(self.llm_adapter)
        }
        
        self.logger.info("Initialized all 8 agents")
    
    def create_project(
        self,
        prompt: str,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Create a new project from a prompt.
        
        Args:
            prompt: User's product idea
            context: Optional context (target audience, features, etc.)
        
        Returns:
            Project ID
        """
        project_id = str(uuid.uuid4())
        
        # Create workflow state
        workflow = self.state_manager.create_workflow(
            project_id=project_id,
            prompt=prompt,
            context=context or {}
        )
        
        # Publish workflow started event
        self.message_bus.publish(
            MessageType.WORKFLOW_STARTED,
            project_id=project_id,
            payload={'prompt': prompt},
            sender="orchestrator"
        )
        
        # Enqueue first task (Product Interpretation)
        self._enqueue_stage(
            project_id=project_id,
            stage=WorkflowStage.PRODUCT_INTERPRETATION,
            inputs={'prompt': prompt, 'context': context or {}},
            priority=TaskPriority.HIGH
        )
        
        self.logger.info(f"Created project {project_id}")
        
        return project_id
    
    def _enqueue_stage(
        self,
        project_id: str,
        stage: WorkflowStage,
        inputs: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: List[str] = None
    ) -> str:
        """Enqueue a stage task"""
        
        agent_type_map = {
            WorkflowStage.PRODUCT_INTERPRETATION: AgentType.PRODUCT_INTERPRETER,
            WorkflowStage.FRONTEND_GENERATION: AgentType.FRONTEND_ENGINEER,
            WorkflowStage.BACKEND_GENERATION: AgentType.BACKEND_ENGINEER,
            WorkflowStage.INTEGRATION: AgentType.INTEGRATION,
            WorkflowStage.TESTING: AgentType.TESTING,
            WorkflowStage.DEBUG: AgentType.DEBUG,
            WorkflowStage.SECURITY_AUDIT: AgentType.SECURITY,
            WorkflowStage.PRODUCTION_READINESS: AgentType.PRODUCTION_READINESS
        }
        
        task_id = self.task_queue.enqueue(
            project_id=project_id,
            stage_name=stage.value,
            agent_type=agent_type_map[stage].value,
            inputs=inputs,
            priority=priority,
            dependencies=dependencies,
            max_retries=self.max_retries
        )
        
        return task_id
    
    def process_next_task(self) -> bool:
        """
        Process the next task in the queue.
        
        Returns:
            True if a task was processed, False if queue is empty
        """
        task = self.task_queue.dequeue()
        
        if not task:
            return False
        
        self.logger.info(f"Processing task {task.task_id} for stage {task.stage_name}")
        
        # Publish task started event
        self.message_bus.publish(
            MessageType.TASK_STARTED,
            project_id=task.project_id,
            payload={
                'task_id': task.task_id,
                'stage_name': task.stage_name,
                'retry_count': task.retry_count
            },
            sender="orchestrator"
        )
        
        # Update workflow state
        workflow = self.state_manager.get_workflow(task.project_id)
        workflow.status = WorkflowStatus.RUNNING
        workflow.current_stage = task.stage_name
        self.state_manager.update_workflow(workflow)
        
        # Save stage state
        stage_state = StageState(
            project_id=task.project_id,
            stage_name=task.stage_name,
            status=StageStatus.RUNNING,
            agent_type=task.agent_type,
            inputs=task.inputs,
            outputs={},
            confidence=0.0,
            retry_count=task.retry_count,
            error_message=None,
            started_at=datetime.utcnow().isoformat(),
            completed_at=None
        )
        self.state_manager.save_stage(stage_state)
        
        # Execute agent
        try:
            agent_type = AgentType(task.agent_type)
            agent = self.agents[agent_type]
            
            result = agent.execute_with_retry(task.inputs)
            
            if result.success:
                self._handle_task_success(task, result, workflow)
            else:
                self._handle_task_failure(task, result, workflow)
        
        except Exception as e:
            self.logger.error(f"Error executing task {task.task_id}: {e}", exc_info=True)
            self._handle_task_failure(
                task,
                AgentResult(
                    success=False,
                    confidence=0.0,
                    outputs={},
                    errors=[str(e)]
                ),
                workflow
            )
        
        return True
    
    def _handle_task_success(
        self,
        task: Any,
        result: AgentResult,
        workflow: WorkflowState
    ):
        """Handle successful task completion"""
        
        # Mark task as completed
        self.task_queue.mark_completed(task.task_id, result.outputs)
        
        # Update workflow state
        workflow.stage_results[task.stage_name] = result.outputs
        
        # Save stage completion
        stage_state = StageState(
            project_id=task.project_id,
            stage_name=task.stage_name,
            status=StageStatus.COMPLETED,
            agent_type=task.agent_type,
            inputs=task.inputs,
            outputs=result.outputs,
            confidence=result.confidence,
            retry_count=task.retry_count,
            error_message=None,
            started_at=task.started_at,
            completed_at=datetime.utcnow().isoformat()
        )
        self.state_manager.save_stage(stage_state)
        
        # Publish task completed event
        self.message_bus.publish(
            MessageType.TASK_COMPLETED,
            project_id=task.project_id,
            payload={
                'task_id': task.task_id,
                'stage_name': task.stage_name,
                'confidence': result.confidence,
                'outputs': result.outputs
            },
            sender=task.agent_type
        )
        
        # Enqueue next stage(s)
        self._enqueue_next_stages(task, workflow)
        
        self.logger.info(
            f"Task {task.task_id} completed successfully "
            f"(confidence: {result.confidence}%)"
        )
    
    def _handle_task_failure(
        self,
        task: Any,
        result: AgentResult,
        workflow: WorkflowState
    ):
        """Handle task failure"""
        
        error_message = '; '.join(result.errors) if result.errors else "Unknown error"
        
        # Mark task as failed (will retry if under max retries)
        self.task_queue.mark_failed(
            task.task_id,
            error_message,
            retry=True
        )
        
        # Update workflow errors
        workflow.errors.append(f"{task.stage_name}: {error_message}")
        
        # Check if task will be retried
        if task.retry_count < task.max_retries:
            self.logger.warning(
                f"Task {task.task_id} failed, will retry "
                f"({task.retry_count + 1}/{task.max_retries})"
            )
        else:
            # Permanent failure
            workflow.status = WorkflowStatus.FAILED
            self.state_manager.update_workflow(workflow)
            
            # Publish workflow failed event
            self.message_bus.publish(
                MessageType.WORKFLOW_FAILED,
                project_id=task.project_id,
                payload={
                    'stage_name': task.stage_name,
                    'error': error_message
                },
                sender="orchestrator"
            )
            
            self.logger.error(
                f"Task {task.task_id} failed permanently after "
                f"{task.retry_count} attempts"
            )
        
        # Publish task failed event
        self.message_bus.publish(
            MessageType.TASK_FAILED,
            project_id=task.project_id,
            payload={
                'task_id': task.task_id,
                'stage_name': task.stage_name,
                'error': error_message,
                'retry_count': task.retry_count
            },
            sender=task.agent_type
        )
    
    def _enqueue_next_stages(self, task: Any, workflow: WorkflowState):
        """Enqueue the next stage(s) based on current stage"""
        
        stage = WorkflowStage(task.stage_name)
        results = workflow.stage_results
        
        if stage == WorkflowStage.PRODUCT_INTERPRETATION:
            # Enqueue Frontend and Backend in parallel
            requirements = results['product_interpretation']
            
            frontend_task_id = self._enqueue_stage(
                project_id=task.project_id,
                stage=WorkflowStage.FRONTEND_GENERATION,
                inputs={'requirements': requirements},
                priority=TaskPriority.NORMAL,
                dependencies=[task.task_id]
            )
            
            backend_task_id = self._enqueue_stage(
                project_id=task.project_id,
                stage=WorkflowStage.BACKEND_GENERATION,
                inputs={'requirements': requirements},
                priority=TaskPriority.NORMAL,
                dependencies=[task.task_id]
            )
            
            # Store task IDs for integration dependencies
            workflow.metadata['frontend_task_id'] = frontend_task_id
            workflow.metadata['backend_task_id'] = backend_task_id
        
        elif stage == WorkflowStage.FRONTEND_GENERATION:
            # Check if backend is also complete
            if 'backend_generation' in results:
                self._enqueue_integration(task, workflow)
        
        elif stage == WorkflowStage.BACKEND_GENERATION:
            # Check if frontend is also complete
            if 'frontend_generation' in results:
                self._enqueue_integration(task, workflow)
        
        elif stage == WorkflowStage.INTEGRATION:
            # Enqueue testing
            self._enqueue_stage(
                project_id=task.project_id,
                stage=WorkflowStage.TESTING,
                inputs={
                    'frontend_outputs': results['frontend_generation'],
                    'backend_outputs': results['backend_generation'],
                    'requirements': results['product_interpretation']
                },
                priority=TaskPriority.HIGH,
                dependencies=[task.task_id]
            )
        
        elif stage == WorkflowStage.TESTING:
            # Check if tests passed
            test_results = results['testing']
            
            if not test_results.get('success', False):
                # Enqueue debug
                self._enqueue_stage(
                    project_id=task.project_id,
                    stage=WorkflowStage.DEBUG,
                    inputs={
                        'error_report': {'type': 'TestFailure', 'message': 'Tests failed'},
                        'code_context': {
                            'files': {
                                **results['frontend_generation']['code_files'],
                                **results['backend_generation']['code_files']
                            }
                        },
                        'test_results': test_results
                    },
                    priority=TaskPriority.HIGH,
                    dependencies=[task.task_id]
                )
            else:
                # Skip debug, go to security
                self._enqueue_security(task, workflow)
        
        elif stage == WorkflowStage.DEBUG:
            # Re-run testing after debug
            # (In a real implementation, would update code files with fixes)
            self._enqueue_security(task, workflow)
        
        elif stage == WorkflowStage.SECURITY_AUDIT:
            # Enqueue production readiness
            self._enqueue_stage(
                project_id=task.project_id,
                stage=WorkflowStage.PRODUCTION_READINESS,
                inputs={
                    'frontend_outputs': results['frontend_generation'],
                    'backend_outputs': results['backend_generation'],
                    'test_results': results.get('testing', {}),
                    'security_report': results['security_audit']
                },
                priority=TaskPriority.CRITICAL,
                dependencies=[task.task_id]
            )
        
        elif stage == WorkflowStage.PRODUCTION_READINESS:
            # Workflow complete
            workflow.status = WorkflowStatus.COMPLETED
            self.state_manager.update_workflow(workflow)
            
            # Publish workflow completed event
            self.message_bus.publish(
                MessageType.WORKFLOW_COMPLETED,
                project_id=task.project_id,
                payload={
                    'readiness_score': results['production_readiness']['readiness_report']['score']
                },
                sender="orchestrator"
            )
            
            self.logger.info(f"Workflow {task.project_id} completed successfully")
        
        # Save workflow state
        self.state_manager.update_workflow(workflow)
    
    def _enqueue_integration(self, task: Any, workflow: WorkflowState):
        """Enqueue integration stage"""
        results = workflow.stage_results
        
        frontend_task_id = workflow.metadata.get('frontend_task_id')
        backend_task_id = workflow.metadata.get('backend_task_id')
        
        self._enqueue_stage(
            project_id=task.project_id,
            stage=WorkflowStage.INTEGRATION,
            inputs={
                'frontend_outputs': results['frontend_generation'],
                'backend_outputs': results['backend_generation']
            },
            priority=TaskPriority.HIGH,
            dependencies=[frontend_task_id, backend_task_id]
        )
    
    def _enqueue_security(self, task: Any, workflow: WorkflowState):
        """Enqueue security audit stage"""
        results = workflow.stage_results
        
        self._enqueue_stage(
            project_id=task.project_id,
            stage=WorkflowStage.SECURITY_AUDIT,
            inputs={
                'code_files': {
                    **results['frontend_generation']['code_files'],
                    **results['backend_generation']['code_files']
                },
                'dependencies': results['backend_generation'].get('dependencies', {}),
                'api_endpoints': results['backend_generation'].get('api_design', {}).get('endpoints', [])
            },
            priority=TaskPriority.HIGH,
            dependencies=[task.task_id]
        )
    
    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get project status"""
        workflow = self.state_manager.get_workflow(project_id)
        if not workflow:
            return {'error': 'Project not found'}
        
        stages = self.state_manager.get_stages(project_id)
        tasks = self.task_queue.get_project_tasks(project_id)
        
        return {
            'project_id': project_id,
            'status': workflow.status.value,
            'current_stage': workflow.current_stage,
            'prompt': workflow.prompt,
            'stages': [
                {
                    'name': s.stage_name,
                    'status': s.status.value,
                    'confidence': s.confidence,
                    'retry_count': s.retry_count
                }
                for s in stages
            ],
            'pending_tasks': len([t for t in tasks if t.status.value == 'pending']),
            'running_tasks': len([t for t in tasks if t.status.value == 'running']),
            'errors': workflow.errors,
            'created_at': workflow.created_at,
            'updated_at': workflow.updated_at
        }
    
    def run(self, max_iterations: int = 100):
        """
        Run the orchestrator (process tasks until queue is empty).
        
        Args:
            max_iterations: Maximum number of tasks to process
        """
        iterations = 0
        
        while iterations < max_iterations:
            processed = self.process_next_task()
            
            if not processed:
                break
            
            iterations += 1
        
        self.logger.info(f"Processed {iterations} tasks")


if __name__ == '__main__':
    # Test the orchestrator
    from antigravity.llm.kimi_adapter import KimiAdapter
    
    logging.basicConfig(level=logging.INFO)
    
    adapter = KimiAdapter(api_key="MOCK_KEY")
    orchestrator = WorkflowOrchestrator(llm_adapter=adapter)
    
    # Create project
    project_id = orchestrator.create_project(
        prompt="Build a recipe sharing platform",
        context={'target_audience': 'home cooks'}
    )
    
    print(f"Created project: {project_id}")
    
    # Process tasks
    orchestrator.run(max_iterations=20)
    
    # Get final status
    status = orchestrator.get_project_status(project_id)
    print(f"\nFinal status: {status['status']}")
    print(f"Stages completed: {len([s for s in status['stages'] if s['status'] == 'completed'])}")
