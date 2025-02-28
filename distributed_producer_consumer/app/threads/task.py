import queue
import logging
from flask import current_app

logger = logging.getLogger(__name__)

class Task:
    """Represents a task to be processed."""
    def __init__(self, task_id, payload, priority=0):
        self.id = task_id
        self.payload = payload
        self.priority = priority
        self.created_at = None  # Will be set when added to queue
        self.processed_at = None  # Will be set when processed
        
    def __lt__(self, other):
        """For priority queue comparison."""
        return self.priority < other.priority


class TaskQueue:
    """Thread-safe task queue with priority support."""
    def __init__(self):
        self.queue = None
        self.app = None
    
    def init_app(self, app):
        """Initialize with Flask application."""
        self.app = app
        maxsize = app.config.get('TASK_QUEUE_MAXSIZE', 100)
        self.queue = queue.PriorityQueue(maxsize=maxsize)
        
        logger.info(f"Task queue initialized with max size: {maxsize}")
        
    def push(self, task):
        """Add a task to the queue."""
        try:
            self.queue.put((task.priority, task), block=False)
            logger.debug(f"Task {task.id} added to queue")
            return True
        except queue.Full:
            logger.warning(f"Queue is full, task {task.id} not added")
            return False
            
    def pop(self, timeout=0.5):
        """Get a task from the queue with timeout."""
        try:
            _, task = self.queue.get(timeout=timeout)
            logger.debug(f"Task {task.id} retrieved from queue")
            return task
        except queue.Empty:
            return None
            
    def task_done(self):
        """Mark a task as done."""
        self.queue.task_done()
        
    def size(self):
        """Get current queue size."""
        return self.queue.qsize()
        
    def empty(self):
        """Check if queue is empty."""
        return self.queue.empty()
        
    def full(self):
        """Check if queue is full."""
        return self.queue.full()
        
    def wait_completion(self):
        """Wait for all tasks to be processed."""
        self.queue.join()