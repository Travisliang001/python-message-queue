import threading
import time
import logging
from typing import List, Dict, Any
from app import shutdown_event

logger = logging.getLogger(__name__)

class ThreadMonitor(threading.Thread):
    """
    Thread monitor that watches other threads and restarts them if they become inactive.
    """
    
    def __init__(self, threads_to_monitor, shutdown_event, check_interval=10, inactivity_threshold=30):
        """
        Initialize the thread monitor.
        
        Args:
            threads_to_monitor: List of threads to monitor (must implement is_active method)
            shutdown_event: Event to signal thread shutdown
            check_interval: How often to check threads (seconds)
            inactivity_threshold: How long a thread can be inactive before restart (seconds)
        """
        super().__init__(name="ThreadMonitor", daemon=True)
        self.threads_to_monitor = threads_to_monitor
        self.shutdown_event = shutdown_event
        self.check_interval = check_interval
        self.inactivity_threshold = inactivity_threshold
        self.stats: Dict[str, Any] = {
            "restarts": {},
            "last_check": time.time(),
            "total_restarts": 0
        }
        logger.info(f"ThreadMonitor initialized with check interval {check_interval}s "
                   f"and inactivity threshold {inactivity_threshold}s")
    
    def check_threads(self):
        """Check all monitored threads and restart if needed."""
        current_time = time.time()
        self.stats["last_check"] = current_time
        
        for thread in self.threads_to_monitor:
            thread_name = thread.name
            
            # Skip if thread is not started yet
            if not thread.is_alive():
                logger.warning(f"Thread {thread_name} is not alive, skipping check")
                continue
            
            # Check if thread is active
            if not thread.is_active():
                logger.warning(f"Thread {thread_name} appears to be inactive, restarting")
                
                # Track restart statistics
                if thread_name not in self.stats["restarts"]:
                    self.stats["restarts"][thread_name] = 0
                self.stats["restarts"][thread_name] += 1
                self.stats["total_restarts"] += 1
                
                # Create and start a new thread of the same class with same parameters
                # Note: This assumes the thread class's __init__ accepts the same parameters
                # and that the thread can be safely restarted
                new_thread = thread.__class__(*thread._args, **thread._kwargs)
                new_thread.start()
                
                # Replace old thread in the list
                idx = self.threads_to_monitor.index(thread)
                self.threads_to_monitor[idx] = new_thread
                
                logger.info(f"Thread {thread_name} restarted")
            else:
                logger.debug(f"Thread {thread_name} is active")
    
    def get_stats(self):
        """Get monitoring statistics."""
        return {
            "restarts": dict(self.stats["restarts"]),
            "last_check": self.stats["last_check"],
            "total_restarts": self.stats["total_restarts"],
            "uptime": time.time() - self.stats.get("start_time", time.time()),
            "monitored_threads": len(self.threads_to_monitor),
            "active_threads": sum(1 for t in self.threads_to_monitor if t.is_active())
        }
    
    def run(self):
        """Run the monitor thread."""
        logger.info("ThreadMonitor started")
        self.stats["start_time"] = time.time()
        
        while not self.shutdown_event.is_set():

            try:
                # Check all threads
                self.check_threads()
                
                # Sleep until next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in ThreadMonitor: {e}")
                time.sleep(1)  # Avoid tight loop in case of recurring errors
        
        logger.info("ThreadMonitor shutting down")