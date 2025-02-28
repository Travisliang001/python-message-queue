import sys
import os
import signal
import time
import threading
import logging
import argparse
from app import create_app, task_queue, shutdown_event
from app.producer.task_producer import TaskProducer
from app.consumer.task_consumer import TaskConsumer
from app.monitor.thread_monitor import ThreadMonitor
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run the multithreaded Flask application')
    parser.add_argument('--config', type=str, default='app.config.DevelopmentConfig',
                        help='Config class to use (default: app.config.DevelopmentConfig)')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run on')
    parser.add_argument('--port', type=int, default=5000, help='Port to run on')
    parser.add_argument('--demo', action='store_true', help='Run in demo mode with auto-generated tasks')
    return parser.parse_args()

def handle_shutdown(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    shutdown_event.set()
    
    # Give threads a chance to shut down gracefully
    time.sleep(2)
    logger.info("Exiting...")
    sys.exit(0)

def main():
    """Main entry point for the application."""
    # Parse command line arguments
    args = parse_args()
    load_dotenv()
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Create the Flask app
    app = create_app(config_object=args.config)
    print("task queue size: ", task_queue.qsize())
    # Get thread settings from config
    consumer_count = app.config.get('CONSUMER_COUNT', 5)
    monitor_check_interval = app.config.get('MONITOR_CHECK_INTERVAL', 10)
    inactivity_threshold = app.config.get('THREAD_INACTIVITY_THRESHOLD', 30)
    
    # Initialize and start producer thread
    producer = TaskProducer(task_queue, shutdown_event, interval=2.0, demo_mode=args.demo)
    producer.start()
    logger.info("Started producer thread")
    
    # Initialize and start consumer threads
    consumers = []
    for i in range(consumer_count):
        consumer = TaskConsumer(task_queue, i+1, shutdown_event)
        consumer.start()
        consumers.append(consumer)
    logger.info(f"Started {consumer_count} consumer threads")
    
    # Create a list of all worker threads for monitoring
    worker_threads = [producer] + consumers
    
    # Initialize and start monitor thread
    monitor = ThreadMonitor(worker_threads, shutdown_event, 
                            check_interval=monitor_check_interval,
                            inactivity_threshold=inactivity_threshold)
    monitor.start()
    logger.info("Started monitor thread")
    
    # Add a route to get thread status
    @app.route('/thread-status')
    def thread_status():
        from flask import jsonify
        status = {
            "producer": {
                "active": producer.is_active(),
                "alive": producer.is_alive(),
                "name": producer.name,
            },
            "consumers": [
                {
                    "id": c.worker_id,
                    "active": c.is_active(),
                    "alive": c.is_alive(),
                    "name": c.name,
                    "tasks_processed": c.tasks_processed
                } for c in consumers
            ],
            "monitor": monitor.get_stats(),
            "queue": {
                "size": task_queue.qsize(),
                "empty": task_queue.empty(),
                "full": task_queue.full()
            }
        }
        return jsonify(status)
    
    # Run the Flask app
    logger.info(f"Starting Flask app on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug, use_reloader=False, threaded=True)

if __name__ == "__main__":
    main()