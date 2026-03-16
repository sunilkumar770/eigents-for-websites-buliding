"""
Message Bus

Inter-agent communication via publish/subscribe pattern.
"""

import threading
from datetime import datetime
from typing import Dict, List, Any, Callable, Optional
from enum import Enum
from dataclasses import dataclass
import logging
import uuid


class MessageType(Enum):
    """Message types"""
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    ESCALATION_REQUIRED = "escalation_required"
    PROGRESS_UPDATE = "progress_update"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"


@dataclass
class Message:
    """Message representation"""
    message_id: str
    message_type: MessageType
    project_id: str
    payload: Dict[str, Any]
    timestamp: str
    sender: str


class MessageBus:
    """
    Event-driven message bus for inter-agent communication.
    
    Features:
    - Publish/subscribe pattern
    - Message persistence for audit trail
    - WebSocket support for real-time updates
    - Thread-safe operations
    """
    
    def __init__(self, persist_messages: bool = True):
        self.subscribers: Dict[MessageType, List[Callable]] = {}
        self.message_history: List[Message] = []
        self.persist_messages = persist_messages
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
        # Initialize subscriber lists for all message types
        for msg_type in MessageType:
            self.subscribers[msg_type] = []
    
    def publish(
        self,
        message_type: MessageType,
        project_id: str,
        payload: Dict[str, Any],
        sender: str = "system"
    ) -> str:
        """
        Publish a message to all subscribers.
        
        Args:
            message_type: Type of message
            project_id: Project identifier
            payload: Message data
            sender: Message sender identifier
        
        Returns:
            Message ID
        """
        message = Message(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            project_id=project_id,
            payload=payload,
            timestamp=datetime.utcnow().isoformat(),
            sender=sender
        )
        
        # Persist message
        if self.persist_messages:
            with self.lock:
                self.message_history.append(message)
        
        # Notify subscribers
        subscribers = self.subscribers.get(message_type, [])
        
        self.logger.debug(
            f"Publishing {message_type.value} for project {project_id} "
            f"to {len(subscribers)} subscribers"
        )
        
        for callback in subscribers:
            try:
                callback(message)
            except Exception as e:
                self.logger.error(
                    f"Error in subscriber callback: {e}",
                    exc_info=True
                )
        
        return message.message_id
    
    def subscribe(
        self,
        message_type: MessageType,
        callback: Callable[[Message], None]
    ):
        """
        Subscribe to a message type.
        
        Args:
            message_type: Type of message to subscribe to
            callback: Function to call when message is published
        """
        with self.lock:
            if callback not in self.subscribers[message_type]:
                self.subscribers[message_type].append(callback)
                
                self.logger.info(
                    f"Added subscriber for {message_type.value}"
                )
    
    def unsubscribe(
        self,
        message_type: MessageType,
        callback: Callable[[Message], None]
    ):
        """
        Unsubscribe from a message type.
        
        Args:
            message_type: Type of message to unsubscribe from
            callback: Callback function to remove
        """
        with self.lock:
            if callback in self.subscribers[message_type]:
                self.subscribers[message_type].remove(callback)
                
                self.logger.info(
                    f"Removed subscriber for {message_type.value}"
                )
    
    def get_messages(
        self,
        project_id: Optional[str] = None,
        message_type: Optional[MessageType] = None,
        limit: int = 100
    ) -> List[Message]:
        """
        Get message history with optional filters.
        
        Args:
            project_id: Filter by project ID
            message_type: Filter by message type
            limit: Maximum number of messages to return
        
        Returns:
            List of messages
        """
        with self.lock:
            messages = self.message_history
            
            # Apply filters
            if project_id:
                messages = [m for m in messages if m.project_id == project_id]
            
            if message_type:
                messages = [m for m in messages if m.message_type == message_type]
            
            # Return most recent messages
            return messages[-limit:]
    
    def clear_history(self, project_id: Optional[str] = None):
        """
        Clear message history.
        
        Args:
            project_id: If provided, only clear messages for this project
        """
        with self.lock:
            if project_id:
                self.message_history = [
                    m for m in self.message_history
                    if m.project_id != project_id
                ]
            else:
                self.message_history.clear()
            
            self.logger.info(
                f"Cleared message history for project {project_id or 'all'}"
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get message bus statistics"""
        with self.lock:
            message_counts = {}
            for msg_type in MessageType:
                count = sum(
                    1 for m in self.message_history
                    if m.message_type == msg_type
                )
                message_counts[msg_type.value] = count
            
            subscriber_counts = {
                msg_type.value: len(callbacks)
                for msg_type, callbacks in self.subscribers.items()
            }
            
            return {
                'total_messages': len(self.message_history),
                'message_counts': message_counts,
                'subscriber_counts': subscriber_counts
            }


# Global message bus instance
_message_bus = None


def get_message_bus() -> MessageBus:
    """Get the global message bus instance"""
    global _message_bus
    if _message_bus is None:
        _message_bus = MessageBus()
    return _message_bus


if __name__ == '__main__':
    # Test the message bus
    logging.basicConfig(level=logging.INFO)
    
    bus = MessageBus()
    
    # Define a subscriber
    def on_task_completed(message: Message):
        print(f"Task completed: {message.payload.get('stage_name')}")
    
    def on_task_failed(message: Message):
        print(f"Task failed: {message.payload.get('error')}")
    
    # Subscribe
    bus.subscribe(MessageType.TASK_COMPLETED, on_task_completed)
    bus.subscribe(MessageType.TASK_FAILED, on_task_failed)
    
    # Publish messages
    bus.publish(
        MessageType.TASK_STARTED,
        project_id="proj-123",
        payload={'stage_name': 'product_interpretation'},
        sender="orchestrator"
    )
    
    bus.publish(
        MessageType.TASK_COMPLETED,
        project_id="proj-123",
        payload={'stage_name': 'product_interpretation', 'confidence': 95.0},
        sender="product_agent"
    )
    
    bus.publish(
        MessageType.TASK_FAILED,
        project_id="proj-123",
        payload={'stage_name': 'frontend_generation', 'error': 'LLM timeout'},
        sender="frontend_agent"
    )
    
    # Get statistics
    stats = bus.get_statistics()
    print(f"\nStatistics: {stats}")
    
    # Get message history
    messages = bus.get_messages(project_id="proj-123")
    print(f"\nMessage history: {len(messages)} messages")
