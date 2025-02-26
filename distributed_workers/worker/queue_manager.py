"""
Queue and thread management for the application.
"""
import queue
import threading
import time
from worker.worker import handle_request
from worker.producer import producer
from utils.thread_monitor import health_monitor

# Create a global queue
task_queue = queue.Queue()

# Control flags
workers_running = True
producer_running = False

# Thread references
consumer_threads = []
producer_thread = None

# Thread management lock
thread_lock = threading.Lock()

# Thread health tracking
thread_health = {}

def start_workers(num_workers):
    """Start worker threads and health monitor."""
    global consumer_threads, thread_health
    
    consumer_threads = []
    
    for i in range(num_workers):
        t = threading.Thread(target=handle_request, 
                             args=(task_queue, thread_lock, thread_health))
        t.daemon = True
        t.start()
        consumer_threads.append(t)
    
    # Start health monitor thread
    monitor_thread = threading.Thread(
        target=health_monitor,
        args=(thread_lock, thread_health, consumer_threads, 
              producer_thread, workers_running, producer_running)
    )
    monitor_thread.daemon = True
    monitor_thread.start()
    
    return consumer_threads

def start_producer(interval=5, urls=None):
    """Start the producer thread."""
    global producer_running, producer_thread
    
    # Stop any existing producer
    stop_producer()
    
    # Start new producer
    producer_running = True
    producer_thread = threading.Thread(
        target=producer, 
        args=(task_queue, producer_running, thread_lock, thread_health, interval, urls)
    )
    producer_thread.daemon = True
    producer_thread.start()
    
    return {
        "status": "Producer started", 
        "interval": interval, 
        "urls_count": len(urls) if urls else 3
    }

def stop_producer():
    """Stop the producer thread."""
    global producer_running, producer_thread
    
    if producer_thread and producer_thread.is_alive():
        producer_running = False
        producer_thread.join(timeout=2)
        return {"status": "Producer stopped"}
    else:
        return {"status": "No producer running"}

def cleanup():
    """Clean up all threads and queue resources."""
    global workers_running, producer_running
    
    print("Running cleanup...")
    
    # Stop the producer
    producer_running = False
    
    # Stop workers
    workers_running = False
    
    # Drain the queue
    try:
        while not task_queue.empty():
            task_queue.get_nowait()
            task_queue.task_done()
    except:
        pass
    
    print("Cleanup complete")