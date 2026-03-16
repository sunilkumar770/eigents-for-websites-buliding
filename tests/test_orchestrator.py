"""
Integration Tests for Orchestration Layer

Tests the complete orchestration system including:
- State Manager
- Task Queue
- Message Bus
- Workflow Orchestrator
"""

import pytest
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from state_manager import StateManager, WorkflowStatus, StageStatus, WorkflowState, StageState
from task_queue import TaskQueue, TaskPriority, TaskStatus
from message_bus import MessageBus, MessageType
from workflow_orchestrator import WorkflowOrchestrator
from base_agent import AgentResult


# Mock LLM Adapter for testing
class MockLLMAdapter:
    """Mock LLM adapter that returns predefined responses"""
    
    def __init__(self):
        self.call_count = 0
    
    def chat_completion(self, messages, **kwargs):
        """Mock chat completion"""
        self.call_count += 1
        
        # Return mock response
        return {
            'choices': [{
                'message': {
                    'content': '{"result": "mock response"}'
                }
            }]
        }


# Fixtures
@pytest.fixture
def temp_db(tmp_path):
    """Create temporary database"""
    db_path = tmp_path / "test_workflow.db"
    return str(db_path)


@pytest.fixture
def state_manager(temp_db):
    """Create state manager with temp database"""
    return StateManager(db_path=temp_db)


@pytest.fixture
def task_queue():
    """Create task queue"""
    return TaskQueue()


@pytest.fixture
def message_bus():
    """Create message bus"""
    return MessageBus(persist_messages=True)


@pytest.fixture
def orchestrator(state_manager, task_queue, message_bus):
    """Create orchestrator with mocks"""
    adapter = MockLLMAdapter()
    return WorkflowOrchestrator(
        llm_adapter=adapter,
        state_manager=state_manager,
        task_queue=task_queue,
        message_bus=message_bus
    )


# State Manager Tests
class TestStateManager:
    """Test state manager functionality"""
    
    def test_create_workflow(self, state_manager):
        """Test workflow creation"""
        state = state_manager.create_workflow(
            project_id="test-123",
            prompt="Build a test app",
            context={'test': True}
        )
        
        assert state.project_id == "test-123"
        assert state.status == WorkflowStatus.IDLE
        assert state.prompt == "Build a test app"
        assert state.context == {'test': True}
    
    def test_get_workflow(self, state_manager):
        """Test workflow retrieval"""
        # Create workflow
        state_manager.create_workflow(
            project_id="test-456",
            prompt="Test prompt"
        )
        
        # Retrieve workflow
        retrieved = state_manager.get_workflow("test-456")
        
        assert retrieved is not None
        assert retrieved.project_id == "test-456"
        assert retrieved.prompt == "Test prompt"
    
    def test_update_workflow(self, state_manager):
        """Test workflow update"""
        # Create workflow
        state = state_manager.create_workflow(
            project_id="test-789",
            prompt="Test"
        )
        
        # Update workflow
        state.status = WorkflowStatus.RUNNING
        state.current_stage = "frontend_generation"
        state_manager.update_workflow(state)
        
        # Verify update
        retrieved = state_manager.get_workflow("test-789")
        assert retrieved.status == WorkflowStatus.RUNNING
        assert retrieved.current_stage == "frontend_generation"
    
    def test_save_and_get_stages(self, state_manager):
        """Test stage persistence"""
        # Create workflow
        state_manager.create_workflow(
            project_id="test-stage",
            prompt="Test"
        )
        
        # Save stage
        stage = StageState(
            project_id="test-stage",
            stage_name="product_interpretation",
            status=StageStatus.COMPLETED,
            agent_type="product_interpreter",
            inputs={'prompt': 'Test'},
            outputs={'result': 'Success'},
            confidence=95.0,
            retry_count=0,
            error_message=None,
            started_at=datetime.utcnow().isoformat(),
            completed_at=datetime.utcnow().isoformat()
        )
        state_manager.save_stage(stage)
        
        # Retrieve stages
        stages = state_manager.get_stages("test-stage")
        assert len(stages) == 1
        assert stages[0].stage_name == "product_interpretation"
        assert stages[0].confidence == 95.0
    
    def test_list_workflows(self, state_manager):
        """Test workflow listing"""
        # Create multiple workflows
        for i in range(3):
            state_manager.create_workflow(
                project_id=f"test-{i}",
                prompt=f"Test {i}"
            )
        
        # List all workflows
        workflows = state_manager.list_workflows()
        assert len(workflows) == 3
        
        # List with status filter
        running_workflows = state_manager.list_workflows(
            status=WorkflowStatus.IDLE
        )
        assert len(running_workflows) == 3
    
    def test_delete_workflow(self, state_manager):
        """Test workflow deletion"""
        # Create workflow
        state_manager.create_workflow(
            project_id="test-delete",
            prompt="Test"
        )
        
        # Delete workflow
        state_manager.delete_workflow("test-delete")
        
        # Verify deletion
        retrieved = state_manager.get_workflow("test-delete")
        assert retrieved is None


# Task Queue Tests
class TestTaskQueue:
    """Test task queue functionality"""
    
    def test_enqueue_dequeue(self, task_queue):
        """Test basic enqueue/dequeue"""
        # Enqueue task
        task_id = task_queue.enqueue(
            project_id="proj-1",
            stage_name="test_stage",
            agent_type="test_agent",
            inputs={'test': True},
            priority=TaskPriority.NORMAL
        )
        
        # Dequeue task
        task = task_queue.dequeue()
        
        assert task is not None
        assert task.task_id == task_id
        assert task.stage_name == "test_stage"
    
    def test_priority_ordering(self, task_queue):
        """Test priority-based ordering"""
        # Enqueue tasks with different priorities
        low_id = task_queue.enqueue(
            project_id="proj-1",
            stage_name="low",
            agent_type="test",
            inputs={},
            priority=TaskPriority.LOW
        )
        
        high_id = task_queue.enqueue(
            project_id="proj-1",
            stage_name="high",
            agent_type="test",
            inputs={},
            priority=TaskPriority.HIGH
        )
        
        critical_id = task_queue.enqueue(
            project_id="proj-1",
            stage_name="critical",
            agent_type="test",
            inputs={},
            priority=TaskPriority.CRITICAL
        )
        
        # Dequeue should return highest priority first
        task1 = task_queue.dequeue()
        assert task1.task_id == critical_id
        
        task2 = task_queue.dequeue()
        assert task2.task_id == high_id
        
        task3 = task_queue.dequeue()
        assert task3.task_id == low_id
    
    def test_dependencies(self, task_queue):
        """Test task dependencies"""
        # Enqueue task 1
        task1_id = task_queue.enqueue(
            project_id="proj-1",
            stage_name="task1",
            agent_type="test",
            inputs={}
        )
        
        # Enqueue task 2 that depends on task 1
        task2_id = task_queue.enqueue(
            project_id="proj-1",
            stage_name="task2",
            agent_type="test",
            inputs={},
            dependencies=[task1_id]
        )
        
        # Dequeue should return task 1 first
        task1 = task_queue.dequeue()
        assert task1.task_id == task1_id
        
        # Task 2 should not be available yet
        task2 = task_queue.dequeue()
        assert task2 is None
        
        # Complete task 1
        task_queue.mark_completed(task1_id, {'result': 'success'})
        
        # Now task 2 should be available
        task2 = task_queue.dequeue()
        assert task2 is not None
        assert task2.task_id == task2_id
    
    def test_retry_logic(self, task_queue):
        """Test task retry"""
        # Enqueue task
        task_id = task_queue.enqueue(
            project_id="proj-1",
            stage_name="test",
            agent_type="test",
            inputs={},
            max_retries=3
        )
        
        # Dequeue and fail
        task = task_queue.dequeue()
        task_queue.mark_failed(task_id, "Test error", retry=True)
        
        # Task should be re-enqueued
        stats = task_queue.get_statistics()
        assert stats['pending'] == 1
        
        # Dequeue again
        task = task_queue.dequeue()
        assert task.retry_count == 1
    
    def test_mark_completed(self, task_queue):
        """Test task completion"""
        task_id = task_queue.enqueue(
            project_id="proj-1",
            stage_name="test",
            agent_type="test",
            inputs={}
        )
        
        task = task_queue.dequeue()
        task_queue.mark_completed(task_id, {'result': 'success'})
        
        stats = task_queue.get_statistics()
        assert stats['completed'] == 1
        assert stats['running'] == 0


# Message Bus Tests
class TestMessageBus:
    """Test message bus functionality"""
    
    def test_publish_subscribe(self, message_bus):
        """Test basic pub/sub"""
        received_messages = []
        
        def callback(message):
            received_messages.append(message)
        
        # Subscribe
        message_bus.subscribe(MessageType.TASK_COMPLETED, callback)
        
        # Publish
        message_bus.publish(
            MessageType.TASK_COMPLETED,
            project_id="proj-1",
            payload={'stage': 'test'},
            sender="test"
        )
        
        # Verify callback was called
        assert len(received_messages) == 1
        assert received_messages[0].message_type == MessageType.TASK_COMPLETED
    
    def test_multiple_subscribers(self, message_bus):
        """Test multiple subscribers"""
        count1 = [0]
        count2 = [0]
        
        def callback1(message):
            count1[0] += 1
        
        def callback2(message):
            count2[0] += 1
        
        # Subscribe both
        message_bus.subscribe(MessageType.TASK_STARTED, callback1)
        message_bus.subscribe(MessageType.TASK_STARTED, callback2)
        
        # Publish
        message_bus.publish(
            MessageType.TASK_STARTED,
            project_id="proj-1",
            payload={},
            sender="test"
        )
        
        # Both should receive
        assert count1[0] == 1
        assert count2[0] == 1
    
    def test_message_history(self, message_bus):
        """Test message persistence"""
        # Publish messages
        for i in range(5):
            message_bus.publish(
                MessageType.PROGRESS_UPDATE,
                project_id="proj-1",
                payload={'step': i},
                sender="test"
            )
        
        # Get history
        messages = message_bus.get_messages(project_id="proj-1")
        assert len(messages) == 5
    
    def test_message_filtering(self, message_bus):
        """Test message filtering"""
        # Publish different message types
        message_bus.publish(
            MessageType.TASK_STARTED,
            project_id="proj-1",
            payload={},
            sender="test"
        )
        
        message_bus.publish(
            MessageType.TASK_COMPLETED,
            project_id="proj-1",
            payload={},
            sender="test"
        )
        
        # Filter by type
        started_messages = message_bus.get_messages(
            project_id="proj-1",
            message_type=MessageType.TASK_STARTED
        )
        
        assert len(started_messages) == 1
        assert started_messages[0].message_type == MessageType.TASK_STARTED


# Workflow Orchestrator Tests
class TestWorkflowOrchestrator:
    """Test workflow orchestrator"""
    
    def test_create_project(self, orchestrator):
        """Test project creation"""
        project_id = orchestrator.create_project(
            prompt="Build a test app",
            context={'test': True}
        )
        
        assert project_id is not None
        
        # Verify workflow was created
        workflow = orchestrator.state_manager.get_workflow(project_id)
        assert workflow is not None
        assert workflow.prompt == "Build a test app"
        
        # Verify first task was enqueued
        stats = orchestrator.task_queue.get_statistics()
        assert stats['pending'] >= 1
    
    def test_get_project_status(self, orchestrator):
        """Test project status retrieval"""
        project_id = orchestrator.create_project(
            prompt="Test",
            context={}
        )
        
        status = orchestrator.get_project_status(project_id)
        
        assert status['project_id'] == project_id
        assert status['status'] == 'idle'
        assert 'stages' in status
    
    def test_process_task(self, orchestrator):
        """Test task processing"""
        project_id = orchestrator.create_project(
            prompt="Test",
            context={}
        )
        
        # Process one task
        processed = orchestrator.process_next_task()
        
        assert processed is True
        
        # Check workflow was updated
        workflow = orchestrator.state_manager.get_workflow(project_id)
        assert workflow.status == WorkflowStatus.RUNNING


# End-to-End Tests
class TestEndToEnd:
    """End-to-end integration tests"""
    
    def test_complete_workflow_simulation(self, orchestrator):
        """Test complete workflow (with mocked agents)"""
        # Create project
        project_id = orchestrator.create_project(
            prompt="Build a recipe app",
            context={'target_audience': 'home cooks'}
        )
        
        # Process multiple tasks
        iterations = 0
        max_iterations = 20
        
        while iterations < max_iterations:
            processed = orchestrator.process_next_task()
            if not processed:
                break
            iterations += 1
        
        # Check final status
        status = orchestrator.get_project_status(project_id)
        
        # Should have processed at least the first stage
        assert len(status['stages']) >= 1
        
        # Verify messages were published
        messages = orchestrator.message_bus.get_messages(project_id)
        assert len(messages) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
