import threading
import time
import logging
import uuid
import random
from datetime import datetime
from flask import current_app

from app.threads.task import Task

logger = logging.getLogger(__name__)

class FlaskThreadBase(threading.Thread):
    """Base thread class with Flask context support."""
    def __init__(self, app=None, name=None):
        super().__init__(name=name, daemon=True)
        self.app = app
        self._stop_event = threading.Event()
        
    def stop(self):
        """Signal the thread to stop."""
        self._stop_event.set()
        
    def stopped(self):
        """Check if thread is signaled to stop."""
        return self._stop_event.is_set()
        
    def run(self):
        """Main thread execution with Flask context."""
        if self.app:
            with self.app.app_context():
                self._run_with_context()
        else:
            self._run_with_context()
            
    def _run_with_context(self):
        """
        Override this method in subclasses.
        This runs within Flask app context.
        """
        raise NotImplementedError("Subclasses must implement _run_with_context")


class ProducerThread(FlaskThreadBase):
    """Thread that produces tasks and adds them to the queue."""
    def __init__(self, task_queue, app=None, name=None):
        super().__init__(app=app, name=name or f"Producer-{uuid.uuid4().hex[:6]}")
        self.task_queue = task_queue
        
    def _run_with_context(self):
        """Continuously produce tasks."""
        logger.info(f"Producer thread {self.name} started")
        
        while not self.stopped():
            try:
                # This is where you'd implement your task generation logic
                # For demonstration, we'll just create random tasks
                print(f"task_queue length is {self.task_queue.size()}")
                if not self.task_queue.full():
                    task_id = uuid.uuid4().hex
                    priority = random.randint(1, 10)
                    payload = {
                        "data": f"Task data {task_id}",
                        "timestamp": datetime.now().isoformat()
                    }
                    task = Task(task_id, payload, priority)

                    self.task_queue.push(task)
                    print(f"new task id  is {task.id}")

                    logger.debug(f"Produced task {task_id} with priority {priority}")
                
                # Sleep for a bit to avoid overloading
                time.sleep(random.uniform(0.5, 2.0))
                
            except Exception as e:
                logger.error(f"Error in producer thread {self.name}: {e}")
                # Sleep a bit longer after an error
                time.sleep(2.0)
                
        logger.info(f"Producer thread {self.name} stopped")


class ConsumerThread(FlaskThreadBase):
    """Thread that consumes tasks from the queue."""
    def __init__(self, task_queue, app=None, name=None):
        super().__init__(app=app, name=name or f"Consumer-{uuid.uuid4().hex[:6]}")
        self.task_queue = task_queue
        
    def _run_with_context(self):
        """Continuously consume and process tasks."""
        logger.info(f"Consumer thread {self.name} started")
        
        while not self.stopped():
            try:
                # Try to get a task from the queue
                task = self.task_queue.pop(timeout=2)
                
                if task:
                    # Process the task - this is where your task handling logic goes
                    logger.debug(f"Processing task {task.id} in {self.name}")
                    
                    # Simulate processing time
                    processing_time = random.uniform(1, 10)
                    time.sleep(processing_time)
                    
                    # Mark task as done
                    task.processed_at = datetime.now()
                    self.task_queue.task_done()
                    
                    print(f"Completed task {task.id} in {processing_time:.2f}s")
                    
                    # Occasionally simulate a thread crash (for testing)
                    if random.random() < 0.02:  # 2% chance
                        logger.warning(f"Simulating thread crash in {self.name}")
                        break

                    time.sleep(5)
                        
            except Exception as e:
                print(f"Error in consumer thread {self.name}: {e}")

                logger.error(f"Error in consumer thread {self.name}: {e}")
                # Sleep a bit after an error
                time.sleep(1.0)
                
        logger.info(f"Consumer thread {self.name} stopped")