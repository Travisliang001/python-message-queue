"""
Main Flask application entry point.
"""
import signal
import sys
import atexit
from flask import Flask
from api import api_bp
from worker.queue_manager import (
    start_workers, start_producer, cleanup, 
    thread_health, thread_lock
)
from config import (
    DEFAULT_WORKER_COUNT, FLASK_HOST, FLASK_PORT, FLASK_DEBUG
)

# Create Flask application
app = Flask(__name__)

# Register API blueprint
app.register_blueprint(api_bp, url_prefix='/api')

# Signal handlers
def signal_handler(sig, frame):
    print(f"Received signal {sig}, shutting down...")
    cleanup()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Register cleanup for various exit scenarios
atexit.register(cleanup)

@app.route('/')
def index():
    """Simple root endpoint."""
    return {
        "status": "running",
        "endpoints": [
            "/api/add_task",
            "/api/add_multiple",
            "/api/queue_status",
            "/api/thread_health",
            "/api/start_producer",
            "/api/stop_producer",
            "/api/restart"
        ]
    }

if __name__ == '__main__':
    # Start worker threads before running the app
    consumer_threads = start_workers(DEFAULT_WORKER_COUNT)
    
    # Start the producer thread automatically
    start_producer()
    
    try:
        # Run the Flask app
        app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
    finally:
        # Run cleanup
        cleanup()
        print("Application terminated")