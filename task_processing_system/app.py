"""Main entry point for the task queue system."""

import threading
import time
from flask import Flask


from services.task_generator import start_task_generator
from services.thread_monitor import start_thread_monitor
import config
from core.queue_manager import worker_threads, shutdown
from core.worker import worker_thread
from api import create_api


def create_app():
    """Create and configure the Flask application.
    
    Returns:
        Flask: The configured Flask application.
    """
    app = Flask(__name__)
    app = create_api(app)
    return app


def start_workers(num_workers=None):
    """Start the worker threads.
    
    Args:
        num_workers (int, optional): Number of worker threads to start.
        
    Returns:
        list: List of worker thread objects.
    """
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


def start_application():
    """Start all components of the task queue system.
    
    Returns:
        tuple: (worker_threads, generator_thread, monitor_thread, app)
    """
    # Start worker threads
    worker_threads = start_workers()
    
    # Start task generator
    generator_thread = start_task_generator()
    
    # Start thread monitor
    monitor_thread = start_thread_monitor()
    
    # Create Flask app
    app = create_app()
    
    return worker_threads, generator_thread, monitor_thread, app


def main():
    """Main entry point for the application."""
    worker_threads, generator_thread, monitor_thread, app = start_application()
    
    try:
        # Start the Flask app
        app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT)
    finally:
        # Clean shutdown
        print("\nShutting down...")
        shutdown()
        
        # Wait for threads to exit
        generator_thread.join(timeout=2)
        monitor_thread.join(timeout=2)
        for t in worker_threads:
            t.join(timeout=2)
            
        print("Application shutdown complete")


if __name__ == "__main__":
    main()