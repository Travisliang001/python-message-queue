import threading
import logging
from flask import current_app
import atexit

from .workers import ProducerThread, ConsumerThread

logger = logging.getLogger(__name__)

class ThreadPoolBase:
    """Base class for thread pools."""
    def __init__(self):
        self.threads = []
        self.app = None
        self._lock = threading.Lock()
        
    def init_app(self, app, task_queue):
        """Initialize with Flask application."""
        self.app = app
        self.task_queue = task_queue
        
        # Register cleanup on application shutdown
        atexit.register(self.shutdown)
        
    def shutdown(self, wait=True):
        """Shutdown all threads in the pool."""
        with self._lock:
            for thread in self.threads:
                thread.stop()
                
            if wait:
                for thread in self.threads:
                    if thread.is_alive():
                        thread.join(timeout=1.0)
                        
            self.threads.clear()
            logger.info(f"{self.__class__.__name__} shutdown complete")
            
    def get_thread_count(self):
        """Get total thread count."""
        return len(self.threads)
        
    def get_alive_count(self):
        """Get count of alive threads."""
        return sum(1 for t in self.threads if t.is_alive())
        
    def get_dead_count(self):
        """Get count of dead threads."""
        return self.get_thread_count() - self.get_alive_count()


class ProducerPool(ThreadPoolBase):
    """Pool of producer threads."""
    def init_app(self, app, task_queue):
        """Initialize with Flask application."""
        super().init_app(app, task_queue)
        
        # Create initial producer threads
        num_threads = app.config.get('PRODUCER_THREADS', 1)
        self._create_threads(num_threads)
        
        logger.info(f"Producer pool initialized with {num_threads} threads")
        
    def _create_threads(self, count):
        """Create specified number of producer threads."""
        with self._lock:
            current_count = len(self.threads)
            for i in range(current_count, current_count + count):
                thread = ProducerThread(
                    task_queue=self.task_queue,
                    app=self.app,
                    name=f"Producer-{i+1}"
                )
                thread.start()
                self.threads.append(thread)
                logger.info(f"Created and started producer thread {thread.name}")
                
    def replace_dead_threads(self):
        """Check for and replace dead threads."""
        with self._lock:
            # Find and count dead threads
            alive_threads = []
            dead_count = 0
            
            for thread in self.threads:
                if thread.is_alive():
                    alive_threads.append(thread)
                else:
                    dead_count += 1
                    logger.warning(f"Producer thread {thread.name} is dead")
            
            # Replace dead threads
            if dead_count > 0:
                self.threads = alive_threads
                self._create_threads(dead_count)
                logger.info(f"Replaced {dead_count} dead producer threads")


class ConsumerPool(ThreadPoolBase):
    """Pool of consumer threads."""
    def init_app(self, app, task_queue):
        """Initialize with Flask application."""
        super().init_app(app, task_queue)
        
        # Create initial consumer threads
        num_threads = app.config.get('CONSUMER_THREADS', 5)
        self._create_threads(num_threads)
        
        logger.info(f"Consumer pool initialized with {num_threads} threads")
        
    def _create_threads(self, count):
        """Create specified number of consumer threads."""
        with self._lock:
            current_count = len(self.threads)
            for i in range(current_count, current_count + count):
                thread = ConsumerThread(
                    task_queue=self.task_queue,
                    app=self.app,
                    name=f"Consumer-{i+1}"
                )
                thread.start()
                self.threads.append(thread)
                logger.info(f"Created and started consumer thread {thread.name}")
                
    def replace_dead_threads(self):
        """Check for and replace dead threads."""
        with self._lock:
            # Find and count dead threads
            alive_threads = []
            dead_count = 0
            
            for thread in self.threads:
                if thread.is_alive():
                    alive_threads.append(thread)
                else:
                    dead_count += 1
                    logger.warning(f"Consumer thread {thread.name} is dead")
            
            # Replace dead threads
            if dead_count > 0:
                self.threads = alive_threads
                self._create_threads(dead_count)
                logger.info(f"Replaced {dead_count} dead consumer threads")