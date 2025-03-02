from flask import Flask
from .extensions import init_extensions
from .api import api_bp
import atexit
import signal
import threading
import sys

# Global variables for thread control
workers_running = True
producer_running = False
consumer_threads = []
producer_thread = None

def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load default configuration
    app.config.from_mapping(
        PRODUCER_THREADS=1,
        CONSUMER_THREADS=5,
        MONITOR_INTERVAL=5.0,  # seconds
        TASK_QUEUE_MAXSIZE=100
    )
    
    # Override with provided config
    if config:
        app.config.update(config)
    
    # Register extensions
    init_extensions(app)
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Register cleanup for various exit scenarios
    atexit.register(cleanup)
    
    return app

def signal_handler(sig, frame):
    """Handle termination signals."""
    print(f"Received signal {sig}, shutting down...")
    cleanup()
    sys.exit(0)

def cleanup():
    """Clean up all threads and queue resources."""
    global workers_running, producer_running
    
    print("Running cleanup...")
    
    # Stop the producer
    producer_running = False
    
    # Stop workers
    workers_running = False
    
    # Wait for all threads to finish
    for t in consumer_threads:
        t.join(timeout=2)
    
    if producer_thread:
        producer_thread.join(timeout=2)
    
    print("Cleanup complete")