"""Data models and shared state for the task queue system."""

import uuid
import queue
import threading
from datetime import datetime

# Task queue and tracking data structures
task_queue = queue.Queue()
tasks_status = {}
task_lock = threading.Lock()

# Thread monitoring
worker_threads = []
worker_status = {}
worker_status_lock = threading.Lock()

# Global control flag
running = True


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


def update_worker_status(worker_id, status, last_active=None, current_task=None):
    """Update the status of a worker thread."""
    if last_active is None:
        last_active = datetime.now()
    
    with worker_status_lock:
        worker_status[worker_id] = {
            "status": status,
            "last_active": last_active,
            "current_task": current_task
        }


def add_task(task):
    """Add a task to the queue and tracking system."""
    # Add task to tracking
    with task_lock:
        tasks_status[task.task_id] = task
    
    # Add task to queue
    task_queue.put(task)


def update_task_status(task):
    """Update the status of a task in the tracking system."""
    with task_lock:
        tasks_status[task.task_id] = task


def get_task():
    """Get a task from the queue with a timeout."""
    try:
        return task_queue.get(timeout=1)
    except queue.Empty:
        return None


def mark_task_done():
    """Mark the current task as done in the queue."""
    task_queue.task_done()


def shutdown():
    """Signal all threads to shutdown."""
    global running
    running = False


def is_running():
    """Check if the system is still running."""
    return running