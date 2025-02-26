"""
Worker thread implementation.
"""
import threading
import time
import requests
import queue
from config import REQUEST_TIMEOUT

def handle_request(task_queue, thread_lock, thread_health):
    """
    Worker thread function to process URLs from the queue.
    
    Args:
        task_queue: Queue containing URLs to process
        thread_lock: Lock for thread-safe operations
        thread_health: Dictionary to track thread health
    """
    global workers_running
    workers_running = True  # Local reference for this thread
    thread_id = threading.get_ident()
    
    # Register this thread in health monitoring
    with thread_lock:
        thread_health[thread_id] = {
            'last_active': time.time(),
            'status': 'starting',
            'type': 'worker'
        }
    
    try:
        while workers_running:
            # Update health status
            with thread_lock:
                thread_health[thread_id]['last_active'] = time.time()
                thread_health[thread_id]['status'] = 'waiting'
            
            try:
                # Use timeout to allow checking the workers_running flag periodically
                url = task_queue.get(timeout=1)
                
                # Update health status
                with thread_lock:
                    thread_health[thread_id]['status'] = 'processing'
                    thread_health[thread_id]['current_url'] = url
                
                if url is None:  # Termination condition
                    task_queue.task_done()
                    continue
                    
                try:
                    response = requests.get(url, timeout=REQUEST_TIMEOUT)
                    print(f"Response status for {url}: {response.status_code}")
                except Exception as e:
                    print(f"Request failed for {url}: {e}")
                
                # Update health status
                with thread_lock:
                    thread_health[thread_id]['status'] = 'completed'
                    if 'current_url' in thread_health[thread_id]:
                        del thread_health[thread_id]['current_url']
                
                task_queue.task_done()
            except queue.Empty:
                # Queue is empty, continue checking workers_running flag
                continue
            except Exception as e:
                print(f"Worker thread error: {e}")
                # Update health status
                with thread_lock:
                    thread_health[thread_id]['status'] = 'error'
                    thread_health[thread_id]['error'] = str(e)
    finally:
        # Clean up health monitoring when thread exits
        with thread_lock:
            if thread_id in thread_health:
                thread_health[thread_id]['status'] = 'exited'