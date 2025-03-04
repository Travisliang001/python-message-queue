"""Thread monitoring service for the task queue system."""

import time
import threading
import random
from datetime import datetime

from core.queue_manager import (
    worker_threads, worker_status, tasks_status, task_lock, 
    update_worker_status, is_running
)
import config


def thread_monitor():
    """Monitor worker threads and restart any that have died or are stuck."""
    print("Thread monitor started")
    
    while is_running():
        for i, thread in enumerate(worker_threads):
            worker_id = f"worker-{i+1}"
            
            # Randomly pick one to restart (simulating random failures)
            # random_number = random.randint(1, 5)
            
            # Check if thread is alive or needs random restart
            if not thread.is_alive():
                print(f"⚠️ Worker {worker_id} has died or needs restart, restarting...")
                
                # Create a new thread
                from core.worker import worker_thread
                new_thread = threading.Thread(target=worker_thread, args=(worker_id,))
                new_thread.daemon = True
                new_thread.start()
                
                # Replace in the list
                worker_threads[i] = new_thread
                update_worker_status(worker_id, "restarted")
                print(f"✅ Worker {worker_id} restarted")
            
            # Check if worker is stuck (hasn't updated status in too long)
            if worker_id in worker_status:
                last_active = worker_status[worker_id]["last_active"]
                time_since_active = (datetime.now() - last_active).total_seconds()
                
                # If a worker hasn't updated its status in the configured time, it might be stuck
                if time_since_active > config.WORKER_STUCK_THRESHOLD:
                    current_status = worker_status[worker_id]["status"]
                    current_task = worker_status[worker_id].get("current_task")
                    
                    print(f"⚠️ Worker {worker_id} appears to be stuck (status: {current_status}, " +
                          f"last active: {time_since_active:.1f}s ago)")
                    
                    # If the worker is stuck on a task, mark that task as failed
                    if current_task and current_task in tasks_status:
                        with task_lock:
                            task = tasks_status[current_task]
                            if task.status == "processing":
                                task.status = "failed"
                                task.completed_at = datetime.now()
                                task.error_message = f"Worker {worker_id} appears to be stuck"
                                tasks_status[current_task] = task
                                print(f"Marked task {current_task} as failed due to stuck worker")
                    
                    # Try to replace the stuck thread
                    try:
                        # Create a new thread to replace this one
                        from core.worker import worker_thread
                        new_thread = threading.Thread(target=worker_thread, args=(worker_id,))
                        new_thread.daemon = True
                        new_thread.start()
                        
                        # Replace in the list
                        worker_threads[i] = new_thread
                        update_worker_status(worker_id, "replaced")
                        print(f"✅ Worker {worker_id} replaced")
                    except Exception as e:
                        print(f"❌ Failed to replace worker {worker_id}: {str(e)}")
            
        # Wait before checking again
        time.sleep(config.THREAD_CHECK_INTERVAL)
    
    print("Thread monitor exiting")


def start_thread_monitor():
    """Start the thread monitor.
    
    Returns:
        Thread: The thread monitor thread.
    """
    monitor_thread = threading.Thread(target=thread_monitor)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    return monitor_thread