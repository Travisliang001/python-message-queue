import uuid
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass
class Task:
    """Task data model for the queue."""
    data: Any
    priority: int = 5  # 1-10, 10 being highest priority
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=time.time)
    processed_at: Optional[float] = None
    status: str = "pending"  # pending, processing, completed, failed
    result: Any = None
    error: Optional[str] = None
    
    def mark_processing(self):
        """Mark the task as being processed."""
        self.status = "processing"
        return self
    
    def mark_completed(self, result):
        """Mark the task as completed with result."""
        self.status = "completed"
        self.processed_at = time.time()
        self.result = result
        return self
    
    def mark_failed(self, error):
        """Mark the task as failed with error."""
        self.status = "failed"
        self.processed_at = time.time()
        self.error = str(error)
        return self
    
    def to_dict(self) -> Dict:
        """Convert task to dictionary."""
        return {
            'id': self.id,
            'data': self.data,
            'priority': self.priority,
            'created_at': self.created_at,
            'processed_at': self.processed_at,
            'status': self.status,
            'result': self.result,
            'error': self.error
        }
    
    def __lt__(self, other):
        """Compare tasks by priority for priority queue support."""
        if not isinstance(other, Task):
            return NotImplemented
        return self.priority > other.priority  # Higher priority comes first