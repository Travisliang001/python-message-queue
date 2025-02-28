import threading
import time
import logging
import atexit
from flask import current_app

logger = logging.getLogger(__name__)

class ThreadMonitorBase:
    """Base class for thread monitors."""
    def __init__(self, interval=5.0):
        self.interval = interval
        self.pool = None
        self.app = None
        self._stop_event = threading.Event()
        self._monitor_thread = None
        self._started = False
        
    def init_app(self, app, pool):
        """Initialize with Flask application and thread pool."""
        self.app = app
        self.pool = pool
        self.interval = app.config.get('MONITOR_INTERVAL', self.interval)
        
        # Create the monitor thread
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name=f"{self.__class__.__name__}-Thread"
        )
        
        # Register with Flask app's after_request to start monitoring
        app.after_request_funcs.setdefault(None, []).append(self._ensure_started)
        
        # Register for cleanup
        atexit.register(self.stop)
        
        logger.info(f"{self.__class__.__name__} initialized with interval {self.interval}s")
        
    def _ensure_started(self, response):
        """Ensure monitor is started after first request."""
        if not self._started:
            self.start()
        return response
        
    def start(self):
        """Start the monitor thread."""
        if not self._started and self._monitor_thread and not self._monitor_thread.is_alive():
            self._started = True
            self._monitor_thread.start()
            logger.info(f"{self.__class__.__name__} started")
            
    def stop(self):
        """Stop the monitor thread."""
        if self._started and self._monitor_thread and self._monitor_thread.is_alive():
            self._stop_event.set()
            self._monitor_thread.join(timeout=2.0)
            self._started = False
            logger.info(f"{self.__class__.__name__} stopped")
            
    def _monitor_loop(self):
        """Main monitoring loop."""
        if self.app:
            with self.app.app_context():
                self._run_monitor_loop()
        else:
            self._run_monitor_loop()
            
    def _run_monitor_loop(self):
        """Monitor and maintain the thread pool."""
        logger.info(f"{self.__class__.__name__} monitoring thread started")
        
        while not self._stop_event.is_set():
            try:
                if self.pool:
                    # Check and replace dead threads
                    dead_count = self.pool.get_dead_count()
                    if dead_count > 0:
                        logger.warning(f"Found {dead_count} dead threads in {self.pool.__class__.__name__}")
                        self.pool.replace_dead_threads()
                    
                    # Log current pool status
                    logger.debug(
                        f"{self.pool.__class__.__name__} status: "
                        f"{self.pool.get_alive_count()} alive, "
                        f"{dead_count} dead"
                    )
            except Exception as e:
                logger.error(f"Error in {self.__class__.__name__}: {e}")
                
            # Wait before next check
            time.sleep(self.interval)
            
        logger.info(f"{self.__class__.__name__} monitoring thread stopped")


class ProducerMonitor(ThreadMonitorBase):
    """Monitor for the producer thread pool."""
    pass


class ConsumerMonitor(ThreadMonitorBase):
    """Monitor for the consumer thread pool."""
    pass