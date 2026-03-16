"""
Rate Limiter

Controls concurrent API calls to prevent overload and rate limit errors.
Uses semaphore-based concurrency control with metrics tracking.
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock


@dataclass
class APICallMetrics:
    """Metrics for API call tracking"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rate_limited_calls: int = 0
    total_wait_time: float = 0.0  # seconds
    current_active_calls: int = 0
    queue_depth: int = 0
    avg_call_duration: float = 0.0
    last_call_time: Optional[str] = None


@dataclass
class APICallRecord:
    """Record of an individual API call"""
    call_id: str
    agent_type: str
    start_time: float
    end_time: Optional[float] = None
    wait_time: float = 0.0
    duration: Optional[float] = None
    status: str = "pending"  # pending, active, completed, failed
    error: Optional[str] = None


class RateLimiter:
    """
    Rate limiter for API calls using semaphore-based concurrency control.
    
    Features:
    - Limits concurrent API calls to a configurable maximum
    - Tracks metrics (queue depth, wait times, throughput)
    - Thread-safe operation
    - Singleton pattern for global rate limiting
    """
    
    _instance: Optional['RateLimiter'] = None
    _lock = Lock()
    
    def __new__(cls, max_concurrent_calls: int = 2):
        """Singleton pattern - only one instance per process"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, max_concurrent_calls: int = 2):
        """
        Initialize rate limiter
        
        Args:
            max_concurrent_calls: Maximum number of concurrent API calls allowed
        """
        # Only initialize once
        if hasattr(self, '_initialized'):
            return
        
        self.max_concurrent_calls = max_concurrent_calls
        self.semaphore = asyncio.Semaphore(max_concurrent_calls)
        self.metrics = APICallMetrics()
        self.active_calls: Dict[str, APICallRecord] = {}
        self.call_history: list[APICallRecord] = []
        self.logger = logging.getLogger(__name__)
        
        self._initialized = True
        self.logger.info(f"Rate limiter initialized with max {max_concurrent_calls} concurrent calls")
    
    async def acquire(self, call_id: str, agent_type: str) -> APICallRecord:
        """
        Acquire permission to make an API call
        
        Args:
            call_id: Unique identifier for this call
            agent_type: Type of agent making the call
        
        Returns:
            APICallRecord tracking this call
        """
        record = APICallRecord(
            call_id=call_id,
            agent_type=agent_type,
            start_time=time.time(),
            status="queued"
        )
        
        # Track queuing
        self.metrics.queue_depth += 1
        
        self.logger.debug(f"Call {call_id} queued (queue depth: {self.metrics.queue_depth})")
        
        # Wait for semaphore
        queue_start = time.time()
        await self.semaphore.acquire()
        
        # Calculate wait time
        record.wait_time = time.time() - queue_start
        record.status = "active"
        
        # Update metrics
        self.metrics.queue_depth -= 1
        self.metrics.current_active_calls += 1
        self.metrics.total_calls += 1
        self.metrics.total_wait_time += record.wait_time
        self.metrics.last_call_time = datetime.utcnow().isoformat()
        
        # Store active call
        self.active_calls[call_id] = record
        
        self.logger.info(
            f"Call {call_id} started (waited {record.wait_time:.2f}s, "
            f"active: {self.metrics.current_active_calls}/{self.max_concurrent_calls})"
        )
        
        return record
    
    def release(self, call_id: str, success: bool = True, error: Optional[str] = None):
        """
        Release API call slot
        
        Args:
            call_id: Unique identifier for this call
            success: Whether the call succeeded
            error: Error message if failed
        """
        if call_id not in self.active_calls:
            self.logger.warning(f"Attempted to release unknown call {call_id}")
            return
        
        record = self.active_calls.pop(call_id)
        
        # Update record
        record.end_time = time.time()
        record.duration = record.end_time - record.start_time - record.wait_time
        record.status = "completed" if success else "failed"
        record.error = error
        
        # Update metrics
        self.metrics.current_active_calls -= 1
        if success:
            self.metrics.successful_calls += 1
        else:
            self.metrics.failed_calls += 1
            if error and "rate limit" in error.lower():
                self.metrics.rate_limited_calls += 1
        
        # Calculate average duration
        completed_calls = self.metrics.successful_calls + self.metrics.failed_calls
        if completed_calls > 0:
            total_duration = sum(
                r.duration for r in self.call_history + [record] 
                if r.duration is not None
            )
            self.metrics.avg_call_duration = total_duration / completed_calls
        
        # Store in history (keep last 100)
        self.call_history.append(record)
        if len(self.call_history) > 100:
            self.call_history.pop(0)
        
        # Release semaphore
        self.semaphore.release()
        
        self.logger.info(
            f"Call {call_id} released (duration: {record.duration:.2f}s, "
            f"status: {record.status}, active: {self.metrics.current_active_calls})"
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        return {
            'max_concurrent_calls': self.max_concurrent_calls,
            'current_active_calls': self.metrics.current_active_calls,
            'queue_depth': self.metrics.queue_depth,
            'total_calls': self.metrics.total_calls,
            'successful_calls': self.metrics.successful_calls,
            'failed_calls': self.metrics.failed_calls,
            'rate_limited_calls': self.metrics.rate_limited_calls,
            'avg_wait_time': (
                self.metrics.total_wait_time / self.metrics.total_calls 
                if self.metrics.total_calls > 0 else 0.0
            ),
            'avg_call_duration': self.metrics.avg_call_duration,
            'last_call_time': self.metrics.last_call_time,
            'active_calls': [
                {
                    'call_id': call_id,
                    'agent_type': record.agent_type,
                    'elapsed': time.time() - record.start_time - record.wait_time
                }
                for call_id, record in self.active_calls.items()
            ]
        }
    
    def get_call_history(self, limit: int = 20) -> list[Dict[str, Any]]:
        """
        Get recent call history
        
        Args:
            limit: Maximum number of records to return
        
        Returns:
            List of call records
        """
        recent = self.call_history[-limit:] if limit else self.call_history
        return [
            {
                'call_id': r.call_id,
                'agent_type': r.agent_type,
                'wait_time': r.wait_time,
                'duration': r.duration,
                'status': r.status,
                'error': r.error
            }
            for r in recent
        ]
    
    def reset_metrics(self):
        """Reset all metrics (useful for testing)"""
        self.metrics = APICallMetrics()
        self.call_history.clear()
        self.logger.info("Metrics reset")


# Global instance getter
_global_rate_limiter: Optional[RateLimiter] = None

def get_rate_limiter(max_concurrent_calls: int = 2) -> RateLimiter:
    """
    Get or create global rate limiter instance
    
    Args:
        max_concurrent_calls: Maximum concurrent calls (only used on first call)
    
    Returns:
        Global RateLimiter instance
    """
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimiter(max_concurrent_calls)
    return _global_rate_limiter


if __name__ == '__main__':
    # Test the rate limiter
    import asyncio
    
    async def test_rate_limiter():
        limiter = get_rate_limiter(max_concurrent_calls=2)
        
        async def mock_api_call(call_id: str, agent: str, duration: float):
            record = await limiter.acquire(call_id, agent)
            print(f"  [{agent}] Call {call_id} executing...")
            await asyncio.sleep(duration)
            limiter.release(call_id, success=True)
            print(f"  [{agent}] Call {call_id} completed")
        
        print("Testing rate limiter with 5 concurrent calls (limit: 2)")
        
        tasks = [
            mock_api_call(f"call-{i}", f"agent-{i}", 1.0)
            for i in range(5)
        ]
        
        await asyncio.gather(*tasks)
        
        print("\n=== Final Metrics ===")
        metrics = limiter.get_metrics()
        print(f"Total calls: {metrics['total_calls']}")
        print(f"Successful: {metrics['successful_calls']}")
        print(f"Avg wait time: {metrics['avg_wait_time']:.2f}s")
        print(f"Avg call duration: {metrics['avg_call_duration']:.2f}s")
    
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_rate_limiter())
