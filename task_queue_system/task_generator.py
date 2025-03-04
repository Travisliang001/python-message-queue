"""Task generation service for the task queue system."""

import time
import threading

import config
from models import Task, add_task, is_running


def create_task_batch(batch_size=None, batch_number=0):
    """Create a batch of tasks and add them to the queue."""
    if batch_size is None:
        batch_size = config.INITIAL_BATCH_SIZE

    print(f"\nCreating batch {batch_number} ({batch_size} tasks)...")
    for i in range(batch_size):
        task = Task(description=f"Batch {batch_number} - Task {i+1}")
        
        # Add task to the system
        add_task(task)
        
        print(f"Created task {task.task_id}: {task.description}")
    
    return batch_number + 1


def task_generator():
    """Thread function that generates new tasks at regular intervals."""
    batch_number = 0
    print("Task generator started")
    
    # Create initial batch of tasks
    batch_number = create_task_batch(batch_number=batch_number)
    
    # Continue creating batches at regular intervals
    while is_running():
        # Wait for the configured interval
        for _ in range(config.BATCH_INTERVAL):
            if not is_running():
                break
            time.sleep(1)
            
        if is_running():
            # Create a new batch of tasks
            batch_number = create_task_batch(batch_number=batch_number)
    
    print("Task generator exiting")


def start_task_generator():
    """Start the task generator thread."""
    generator_thread = threading.Thread(target=task_generator)
    generator_thread.daemon = True
    generator_thread.start()
    
    return generator_thread