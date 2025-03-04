"""Worker implementation for the task queue system."""

import time
import traceback
import random
from datetime import datetime, timedelta

from core.queue_manager import (
    get_task, mark_task_done, update_task_status, update_worker_status, is_running
)
import config


def process_task(task, worker_id, timeout=None):
    """Process a task with timeout.
    
    Args:
        task (Task): The task to process.
        worker_id (str): The ID of the worker processing the task.
        timeout (int, optional): Maximum time in seconds for processing.
    """
    if timeout is None:
        timeout = config.WORKER_TIMEOUT

    # Update task status to processing
    task.status = "processing"
    task.started_at = datetime.now()
    task.worker_id = worker_id
    update_task_status(task)

    try:
        # Simulate task processing with timeout
        deadline = datetime.now() + timedelta(seconds=timeout)
        
        # Simulate processing time based on task ID
        # This creates a mix of tasks that complete quickly and those that timeout
        processing_time = random.uniform(1500, 2000)
        
        print(f"Worker {worker_id} processing task {task.task_id}: estimated time {processing_time:.1f}s")
        
        # Check if we would exceed the timeout
        remaining_time = (deadline - datetime.now()).total_seconds()
        if processing_time > remaining_time:
            # We'll exceed the timeout, so fail early
            raise TimeoutError(f"Task would take {processing_time:.1f}s but only {remaining_time:.1f}s remaining")
            
        # Simulate work
        time.sleep(3)
        
        # Mark task as completed
        task.status = "completed"
        task.completed_at = datetime.now()
        update_task_status(task)
        print(f"Worker {worker_id} completed task {task.task_id}")
            
    except TimeoutError as e:
        # Mark task as failed due to timeout
        task.status = "failed"
        task.completed_at = datetime.now()
        task.error_message = str(e)
        update_task_status(task)
        print(f"Worker {worker_id}: Task {task.task_id} failed: {str(e)}")
        
    except Exception as e:
        # Mark task as failed for any other reason
        task.status = "failed"
        task.completed_at = datetime.now()
        task.error_message = f"{str(e)}\n{traceback.format_exc()}"
        update_task_status(task)
        print(f"Worker {worker_id}: Task {task.task_id} failed: {str(e)}")


def worker_thread(worker_id):
    """Worker thread function to process tasks from the queue.
    
    Args:
        worker_id (str): The ID of the worker thread.
    """
    print(f"Worker {worker_id} started")
    time.sleep(2)
    update_worker_status(worker_id, "idle")
    
    while is_running():
        try:
            # Try to get a task
            task = get_task()
            
            if task is None:
                # No tasks in the queue, just update worker status and continue waiting
                update_worker_status(worker_id, "idle")
                continue
            
            # Update worker status
            update_worker_status(worker_id, "processing", current_task=task.task_id)
            
            # Process the task with timeout
            process_task(task, worker_id)
            
            # Mark task as done in the queue
            mark_task_done()
            
            # Update worker status
            update_worker_status(worker_id, "idle")
            
        except Exception as e:
            # Log the error
            print(f"Worker {worker_id} encountered an error: {str(e)}")
            print(traceback.format_exc())
            
            # Update worker status
            update_worker_status(worker_id, "error")
    
    print(f"Worker {worker_id} exiting")
    update_worker_status(worker_id, "terminated")