import threading
import time
import random
import logging
from typing import Optional
from app.models.task import Task
from app import task_queue, shutdown_event

logger = logging.getLogger(__name__)

class TaskProducer(threading.Thread):
    """
    Task producer thread that generates simulated tasks and puts them in the queue.
    
    In a real application, this could pull tasks from a database, message broker,
    or another source.
    """
    
    def __init__(self, task_queue, shutdown_event, interval=2.0, demo_mode=False):
        """
        Initialize the producer thread.
        
        Args:
            task_queue: The shared task queue
            shutdown_event: Event to signal thread shutdown
            interval: Time between task generation attempts in seconds
            demo_mode: If True, automatically generate random demo tasks
        """
        super().__init__(name="TaskProducer", daemon=True)
        self.task_queue = task_queue
        self.shutdown_event = shutdown_event
        self.interval = interval
        self.demo_mode = demo_mode
        self.last_activity = time.time()
        self.lock = threading.Lock()
        self.paused = False
        self.pause_event = threading.Event()
        logger.info(f"TaskProducer initialized with interval {interval}s")
    
    def pause(self):
        """Pause the producer."""
        with self.lock:
            self.paused = True
            self.pause_event.clear()
        logger.info("TaskProducer paused")
    
    def resume(self):
        """Resume the producer."""
        with self.lock:
            self.paused = False
            self.pause_event.set()
        logger.info("TaskProducer resumed")
    
    def is_active(self) -> bool:
        """Check if this thread has been active recently."""
        with self.lock:
            return time.time() - self.last_activity < 80
    
    def update_activity(self):
        """Update the last activity timestamp."""
        with self.lock:
            self.last_activity = time.time()
    
    def generate_demo_task(self) -> Task:
        """Generate a random demo task."""
        task_types = ["calculation", "processing", "validation", "analysis"]
        task_type = random.choice(task_types)
        task_data = {
            "type": task_type,
            "complexity": random.randint(1, 10),
            "input_value": random.randint(1, 100),
        }
        priority = random.randint(1, 10)
        return Task(task_data, priority=priority)
    
    def run(self):
        """Run the producer thread."""
        logger.info(f"TaskProducer started")
        
        while not self.shutdown_event.is_set():
            try:
                # Check if paused
                if self.paused:
                    self.pause_event.wait(1)  # Wait for resume or 1 second
                    continue
                
                # In demo mode, automatically generate tasks
                if self.demo_mode and not self.task_queue.full():
                    task = self.generate_demo_task()
                    logger.info(f"Generated demo task: {task.id} (Type: {task.data['type']})")
                    
                    # Try to put task in queue with timeout
                    try:
                        self.task_queue.put(task, timeout=1)
                        logger.info(f"Added task to queue: {task.id}")
                        self.update_activity()
                    except Exception as e:
                        logger.error(f"Error adding task to queue: {e}")
                self.last_activity = time.time()
                # Sleep between production cycles
                time.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"Error in TaskProducer: {e}")
                time.sleep(1)  # Avoid tight loop in case of recurring errors
        
        logger.info("TaskProducer shutting down")