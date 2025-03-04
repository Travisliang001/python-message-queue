"""Main entry point for the task queue system."""

import threading

import config
from models import worker_threads, shutdown
from consumer import start_workers
from task_generator import start_task_generator
from thread_monitor import start_thread_monitor
from api import create_app


def start_application():
    """Start all components of the task queue system."""
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