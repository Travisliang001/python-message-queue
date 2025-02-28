import threading
import time
import random
import logging
from typing import Optional
from app.models.task import Task
from app import shutdown_event

logger = logging.getLogger(__name__)

class TaskConsumer(threading.Thread):
    """
    Task consumer thread that processes tasks from the queue.
    """
    
    def __init__(self, task_queue, worker_id, shutdown_event, processing_time=(1, 5)):
        """
        Initialize a consumer worker thread.
        
        Args:
            task_queue: The shared task queue
            worker_id: Unique identifier for this worker
            shutdown_event: Event to signal thread shutdown
            processing_time: Tuple of (min, max) seconds to simulate processing time
        """
        super().__init__(name=f"TaskConsumer-{worker_id}", daemon=True)
        self.task_queue = task_queue
        self.worker_id = worker_id
        self.shutdown_event = shutdown_event
        self.processing_time = processing_time
        self.last_activity = time.time()
        self.tasks_processed = 0
        self.lock = threading.Lock()
        self.paused = False
        self.pause_event = threading.Event()
        self.pause_event.set()  # Initially not paused
        logger.info(f"TaskConsumer-{worker_id} initialized")
    
    def pause(self):
        """Pause the consumer."""
        with self.lock:
            self.paused = True
            self.pause_event.clear()
        logger.info(f"TaskConsumer-{self.worker_id} paused")
    
    def resume(self):
        """Resume the consumer."""
        with self.lock:
            self.paused = False
            self.pause_event.set()
        logger.info(f"TaskConsumer-{self.worker_id} resumed")
    
    def is_active(self) -> bool:
        """Check if this thread has been active recently."""
        with self.lock:
            
            return time.time() - self.last_activity < 80
    
    def update_activity(self):
        """Update the last activity timestamp."""
        with self.lock:
            self.last_activity = time.time()
    
    def process_task(self, task: Task) -> Task:
        """
        Process a task. This is where the actual work happens.
        
        In a real application, this would implement the actual business logic.
        Here we just simulate processing with a sleep.
        """
        # Mark task as processing
        task.mark_processing()
        
        # Simulate processing time
        processing_duration = random.uniform(*self.processing_time)
        logger.info(f"Worker {self.worker_id} processing task {task.id} "
                   f"(type: {task.data.get('type', 'unknown')}, "
                   f"estimated duration: {processing_duration:.2f}s)")
        
        # Simulate task processing
        time.sleep(processing_duration)
        
        # Simulate occasional failures (10% chance)
        if random.random() < 0.5:
            logger.warning(f"Worker {self.worker_id} failed to process task {task.id}")
            return task.mark_failed("Simulated random failure")
        
        # For demo tasks, apply some transformation
        if isinstance(task.data, dict) and "input_value" in task.data:
            result = task.data["input_value"] * task.data.get("complexity", 1)
            logger.info(f"Worker {self.worker_id} completed task {task.id} with result {result}")
            return task.mark_completed({"result": result})
        
        # For other tasks
        logger.info(f"Worker {self.worker_id} completed task {task.id}")
        return task.mark_completed("Task processed successfully")
    
    def run(self):
        """Run the consumer thread."""
        logger.info(f"TaskConsumer-{self.worker_id} started")
        
        while not self.shutdown_event.is_set():

            try:
                # Check if paused
                if self.paused:
                    self.pause_event.wait(10)  # Wait for resume or 1 second
                    continue
                
                # Try to get a task with timeout to allow for checking shutdown_event
                try:
                    task = self.task_queue.get(timeout=5)
                    self.update_activity()
                    
                    # Process the task
                    task = self.process_task(task)
                    
                    # In a real application, you might want to save results to a database
                    # or send them to another system
                    
                    # Mark task as done in the queue
                    
                    self.task_queue.task_done()
                    self.tasks_processed += 1
                    
                except Exception as e:
                    # If queue.Empty or other exception, just continue
                    continue
                
            except Exception as e:
                logger.error(f"Error in TaskConsumer-{self.worker_id}: {e}")
                time.sleep(1)  # Avoid tight loop in case of recurring errors
        
        logger.info(f"TaskConsumer-{self.worker_id} shutting down after processing {self.tasks_processed} tasks")