"""
Producer thread implementation.
"""
import threading
import time
from config import DEFAULT_URLS

def producer(task_queue, producer_running_flag, thread_lock, thread_health, 
             interval=5, urls=None):
    """
    Producer thread function to generate URL tasks.
    
    Args:
        task_queue: Queue to add URLs to
        producer_running_flag: Flag to control producer execution
        thread_lock: Lock for thread-safe operations
        thread_health: Dictionary to track thread health
        interval: Time between task generation in seconds
        urls: List of URLs to cycle through
    """
    thread_id = threading.get_ident()
    
    # Register this thread in health monitoring
    with thread_lock:
        thread_health[thread_id] = {
            'last_active': time.time(),
            'status': 'starting',
            'type': 'producer'
        }
    
    try:
        if urls is None:
            # Default URLs if none provided
            urls = DEFAULT_URLS
        
        print(f"Producer started with {len(urls)} URLs")
        
        # Keep track of the index to cycle through URLs
        url_index = 0
        
        # Note: We need to check the external flag, not a local variable
        while producer_running_flag:
            # Update health status
            with thread_lock:
                thread_health[thread_id]['last_active'] = time.time()
                thread_health[thread_id]['status'] = 'producing'
            
            # Get the next URL in the cycle
            url = urls[url_index % len(urls)]
            url_index += 1
            
            # Add URL to the queue
            print(f"Producer adding URL {url} to queue")
            task_queue.put(url)
            
            # Update health status
            with thread_lock:
                thread_health[thread_id]['status'] = 'waiting'
                thread_health[thread_id]['last_url'] = url
            
            # Wait for the next interval
            time.sleep(interval)
    finally:
        # Clean up health monitoring when thread exits
        with thread_lock:
            if thread_id in thread_health:
                thread_health[thread_id]['status'] = 'exited'
        
        print("Producer thread exiting")