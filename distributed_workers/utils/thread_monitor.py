"""
Thread health monitoring utility.
"""
import threading
import time
from config import HEALTH_CHECK_INTERVAL

def health_monitor(thread_lock, thread_health, consumer_threads, 
                  producer_thread, workers_running, producer_running):
    """
    Monitor thread health and restart dead threads.
    
    Args:
        thread_lock: Lock for thread-safe operations
        thread_health: Dictionary to track thread health
        consumer_threads: List of worker threads
        producer_thread: Producer thread reference
        workers_running: Flag controlling worker threads
        producer_running: Flag controlling producer thread
    """
    thread_id = threading.get_ident()
    
    with thread_lock:
        thread_health[thread_id] = {
            'last_active': time.time(),
            'status': 'monitoring',
            'type': 'monitor'
        }
    
    try:
        while workers_running:
            current_time = time.time()
            
            with thread_lock:
                # Update monitor status
                thread_health[thread_id]['last_active'] = current_time
                
                # Check worker threads
                workers_to_restart = []
                for i, thread in enumerate(consumer_threads):
                    if not thread.is_alive():
                        print(f"Worker thread {i} is no longer alive, will restart")
                        workers_to_restart.append(i)
                
                # Check producer thread
                producer_needs_restart = False
                if producer_running and (producer_thread is None or not producer_thread.is_alive()):
                    print("Producer thread is no longer alive, will restart")
                    producer_needs_restart = True
            
            # Restart any dead worker threads
            for i in workers_to_restart:
                print(f"Restarting worker thread {i}")
                from worker.worker import handle_request
                consumer_threads[i] = threading.Thread(
                    target=handle_request,
                    args=(task_queue, thread_lock, thread_health)
                )
                consumer_threads[i].daemon = True
                consumer_threads[i].start()
            
            # Restart producer if needed
            if producer_needs_restart:
                print("Restarting producer thread")
                from worker.producer import producer
                producer_thread = threading.Thread(
                    target=producer,
                    args=(task_queue, producer_running, thread_lock, thread_health)
                )
                producer_thread.daemon = True
                producer_thread.start()
            
            # Sleep before next check
            time.sleep(HEALTH_CHECK_INTERVAL)
    finally:
        with thread_lock:
            if thread_id in thread_health:
                thread_health[thread_id]['status'] = 'exited'