"""Queue management for the task queue system."""

import queue
import threading

# Global task queue and tracking data structures
task_queue = queue.Queue()
tasks_status = {}
task_lock = threading.Lock()

# Thread monitoring
worker_threads = []
worker_status = {}
worker_status_lock = threading.Lock()

# Global control flag
running = True


def update_worker_status(worker_id, status, last_active=None, current_task=None):
    """Update the status of a worker thread.
    
    Args:
        worker_id (str): The ID of the worker.
        status (str): Current status (idle, processing, error, etc.).
        last_active (datetime, optional): When the worker was last active.
        current_task (str, optional): ID of the task currently being processed.
    """
    from datetime import datetime
    
    with worker_status_lock:
        if last_active is None:
            last_active = datetime.now()
                
        worker_status[worker_id] = {
            "status": status,
            "last_active": last_active,
            "current_task": current_task
        }


def add_task(task):
    """Add a task to the queue and tracking system.
    
    Args:
        task (Task): The task object to add.
    """
    # Add task to tracking
    with task_lock:
        tasks_status[task.task_id] = task
    
    # Add task to queue
    task_queue.put(task)


def get_task():
    """Get a task from the queue with a timeout.
    
    Returns:
        Task or None: A task from the queue, or None if the queue is empty.
    """
    try:
        # Try to get a task with a timeout (so threads can exit if needed)
        return task_queue.get(timeout=1)
    except queue.Empty:
        return None


def update_task_status(task):
    """Update the status of a task in the tracking system.
    
    Args:
        task (Task): The task object to update.
    """
    with task_lock:
        tasks_status[task.task_id] = task


def mark_task_done():
    """Mark the current task as done in the queue."""
    task_queue.task_done()


def get_queue_size():
    """Get the current size of the task queue.
    
    Returns:
        int: Number of tasks in the queue.
    """
    return task_queue.qsize()


def get_all_tasks():
    """Get all tasks in the system.
    
    Returns:
        list: List of all task objects.
    """
    return list(tasks_status.values())


def get_task_by_id(task_id):
    """Get a specific task by ID.
    
    Args:
        task_id (str): The ID of the task to retrieve.
        
    Returns:
        Task or None: The task object, or None if not found.
    """
    return tasks_status.get(task_id)


def shutdown():
    """Signal all threads to shutdown."""
    global running
    running = False


def is_running():
    """Check if the system is still running.
    
    Returns:
        bool: True if the system is running, False otherwise.
    """
    return running