"""Worker implementation for the task queue system."""

import time
import traceback
import random
import threading
from datetime import datetime, timedelta

import config
from models import (
    update_worker_status, get_task, update_task_status, 
    mark_task_done, is_running
)


def process_task(task, worker_id, timeout=None):
    """Process a task with timeout."""
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
        processing_time = random.uniform(150, 200)
        
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
    """Worker thread function to process tasks from the queue."""
    print(f"Worker {worker_id} started")
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


def start_workers(num_workers=None):
    """Start the worker threads."""
    from models import worker_threads
    
    if num_workers is None:
        num_workers = config.NUM_WORKERS
    
    worker_threads.clear()
    
    for i in range(num_workers):
        worker_id = f"worker-{i+1}"
        t = threading.Thread(target=worker_thread, args=(worker_id,))
        t.daemon = True
        t.start()
        worker_threads.append(t)
        print(f"Started {worker_id}")
    
    return worker_threads