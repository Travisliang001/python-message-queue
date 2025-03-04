"""Data models for the task queue system."""

import uuid
from datetime import datetime


class Task:
    """Task model representing a unit of work to be processed."""
    
    def __init__(self, task_id=None, description=""):
        self.task_id = task_id or str(uuid.uuid4())
        self.description = description
        self.status = "pending"  # pending, processing, completed, failed
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.worker_id = None
        self.error_message = None

    def to_dict(self):
        """Convert task to dictionary for serialization."""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "worker_id": self.worker_id,
            "error_message": self.error_message
        }

    def __repr__(self):
        return f"<Task {self.task_id}: {self.status}>"