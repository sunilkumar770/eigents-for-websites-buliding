"""
Task Queue

Priority-based task queue for managing agent tasks.
"""

import heapq
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from enum import Enum
from dataclasses import dataclass, field
import logging
import uuid


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class TaskStatus(Enum):
    """Task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(order=True)
class Task:
    """Task representation"""
    priority: int = field(compare=True)
    task_id: str = field(compare=False)
    project_id: str = field(compare=False)
    stage_name: str = field(compare=False)
    agent_type: str = field(compare=False)
    inputs: Dict[str, Any] = field(compare=False)
    dependencies: List[str] = field(default_factory=list, compare=False)
    status: TaskStatus = field(default=TaskStatus.PENDING, compare=False)
    retry_count: int = field(default=0, compare=False)
    max_retries: int = field(default=3, compare=False)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat(), compare=False)
    started_at: Optional[str] = field(default=None, compare=False)
    completed_at: Optional[str] = field(default=None, compare=False)
    error_message: Optional[str] = field(default=None, compare=False)
    result: Optional[Dict[str, Any]] = field(default=None, compare=False)


class TaskQueue:
    """
    Priority-based task queue with dependency management.
    
    Features:
    - Priority levels (CRITICAL, HIGH, NORMAL, LOW)
    - Task dependencies
    - Retry queue for failed tasks
    - Thread-safe operations
    """
    
    def __init__(self):
        self.queue: List[Task] = []
        self.tasks: Dict[str, Task] = {}
        self.running_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}
        self.failed_tasks: Dict[str, Task] = {}
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
    
    def enqueue(
        self,
        project_id: str,
        stage_name: str,
        agent_type: str,
        inputs: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: List[str] = None,
        max_retries: int = 3
    ) -> str:
        """
        Add a task to the queue.
        
        Args:
            project_id: Project identifier
            stage_name: Stage name (e.g., 'frontend_generation')
            agent_type: Agent type (e.g., 'frontend_engineer')
            inputs: Task inputs
            priority: Task priority
            dependencies: List of task IDs this task depends on
            max_retries: Maximum retry attempts
        
        Returns:
            Task ID
        """
        with self.lock:
            task_id = str(uuid.uuid4())
            
            task = Task(
                priority=priority.value,
                task_id=task_id,
                project_id=project_id,
                stage_name=stage_name,
                agent_type=agent_type,
                inputs=inputs,
                dependencies=dependencies or [],
                max_retries=max_retries
            )
            
            heapq.heappush(self.queue, task)
            self.tasks[task_id] = task
            
            self.logger.info(
                f"Enqueued task {task_id} for {stage_name} "
                f"(priority: {priority.name})"
            )
            
            return task_id
    
    def dequeue(self) -> Optional[Task]:
        """
        Get the highest priority task that's ready to run.
        
        A task is ready if:
        - All dependencies are completed
        - Not currently running
        
        Returns:
            Task or None if no tasks are ready
        """
        with self.lock:
            # Find first task with satisfied dependencies
            ready_tasks = []
            
            for task in self.queue:
                if self._are_dependencies_satisfied(task):
                    ready_tasks.append(task)
            
            if not ready_tasks:
                return None
            
            # Get highest priority ready task
            task = min(ready_tasks, key=lambda t: t.priority)
            
            # Remove from queue
            self.queue.remove(task)
            heapq.heapify(self.queue)
            
            # Mark as running
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow().isoformat()
            self.running_tasks[task.task_id] = task
            
            self.logger.info(f"Dequeued task {task.task_id} for {task.stage_name}")
            
            return task
    
    def _are_dependencies_satisfied(self, task: Task) -> bool:
        """Check if all task dependencies are completed"""
        if not task.dependencies:
            return True
        
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                return False
        
        return True
    
    def mark_completed(
        self,
        task_id: str,
        result: Dict[str, Any]
    ):
        """Mark a task as completed"""
        with self.lock:
            if task_id not in self.running_tasks:
                self.logger.warning(f"Task {task_id} not in running tasks")
                return
            
            task = self.running_tasks.pop(task_id)
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow().isoformat()
            task.result = result
            
            self.completed_tasks[task_id] = task
            
            self.logger.info(f"Task {task_id} completed")
    
    def mark_failed(
        self,
        task_id: str,
        error_message: str,
        retry: bool = True
    ):
        """
        Mark a task as failed.
        
        Args:
            task_id: Task identifier
            error_message: Error description
            retry: Whether to retry the task
        """
        with self.lock:
            if task_id not in self.running_tasks:
                self.logger.warning(f"Task {task_id} not in running tasks")
                return
            
            task = self.running_tasks.pop(task_id)
            task.error_message = error_message
            task.retry_count += 1
            
            # Retry if under max retries
            if retry and task.retry_count < task.max_retries:
                task.status = TaskStatus.PENDING
                task.started_at = None
                
                # Re-enqueue with same priority
                heapq.heappush(self.queue, task)
                
                self.logger.warning(
                    f"Task {task_id} failed, retrying "
                    f"({task.retry_count}/{task.max_retries})"
                )
            else:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow().isoformat()
                self.failed_tasks[task_id] = task
                
                self.logger.error(
                    f"Task {task_id} failed permanently after "
                    f"{task.retry_count} attempts"
                )
    
    def cancel_task(self, task_id: str):
        """Cancel a pending task"""
        with self.lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                
                if task.status == TaskStatus.PENDING:
                    self.queue.remove(task)
                    heapq.heapify(self.queue)
                    
                    task.status = TaskStatus.CANCELLED
                    task.completed_at = datetime.utcnow().isoformat()
                    
                    self.logger.info(f"Cancelled task {task_id}")
                else:
                    self.logger.warning(
                        f"Cannot cancel task {task_id} "
                        f"(status: {task.status.value})"
                    )
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID"""
        with self.lock:
            return self.tasks.get(task_id)
    
    def get_project_tasks(self, project_id: str) -> List[Task]:
        """Get all tasks for a project"""
        with self.lock:
            return [
                task for task in self.tasks.values()
                if task.project_id == project_id
            ]
    
    def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks"""
        with self.lock:
            return [task for task in self.queue]
    
    def get_running_tasks(self) -> List[Task]:
        """Get all running tasks"""
        with self.lock:
            return list(self.running_tasks.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get queue statistics"""
        with self.lock:
            return {
                'pending': len(self.queue),
                'running': len(self.running_tasks),
                'completed': len(self.completed_tasks),
                'failed': len(self.failed_tasks),
                'total': len(self.tasks)
            }
    
    def clear_completed(self, project_id: Optional[str] = None):
        """Clear completed tasks to free memory"""
        with self.lock:
            if project_id:
                # Clear for specific project
                to_remove = [
                    task_id for task_id, task in self.completed_tasks.items()
                    if task.project_id == project_id
                ]
                for task_id in to_remove:
                    del self.completed_tasks[task_id]
                    del self.tasks[task_id]
            else:
                # Clear all
                for task_id in list(self.completed_tasks.keys()):
                    del self.tasks[task_id]
                self.completed_tasks.clear()
            
            self.logger.info(f"Cleared completed tasks for project {project_id or 'all'}")


if __name__ == '__main__':
    # Test the task queue
    logging.basicConfig(level=logging.INFO)
    
    queue = TaskQueue()
    
    # Enqueue tasks with dependencies
    task1_id = queue.enqueue(
        project_id="proj-123",
        stage_name="product_interpretation",
        agent_type="product_interpreter",
        inputs={'prompt': 'Build a recipe app'},
        priority=TaskPriority.HIGH
    )
    
    task2_id = queue.enqueue(
        project_id="proj-123",
        stage_name="frontend_generation",
        agent_type="frontend_engineer",
        inputs={'requirements': {}},
        priority=TaskPriority.NORMAL,
        dependencies=[task1_id]  # Depends on product interpretation
    )
    
    task3_id = queue.enqueue(
        project_id="proj-123",
        stage_name="backend_generation",
        agent_type="backend_engineer",
        inputs={'requirements': {}},
        priority=TaskPriority.NORMAL,
        dependencies=[task1_id]  # Also depends on product interpretation
    )
    
    print(f"Enqueued 3 tasks")
    print(f"Statistics: {queue.get_statistics()}")
    
    # Dequeue and complete task 1
    task1 = queue.dequeue()
    print(f"\nDequeued: {task1.stage_name}")
    queue.mark_completed(task1.task_id, {'product_name': 'Recipe App'})
    
    # Now tasks 2 and 3 should be ready
    task2 = queue.dequeue()
    print(f"Dequeued: {task2.stage_name}")
    
    task3 = queue.dequeue()
    print(f"Dequeued: {task3.stage_name}")
    
    print(f"\nFinal statistics: {queue.get_statistics()}")
