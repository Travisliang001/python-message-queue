"""
Health monitoring endpoints for the application.
"""
from flask import jsonify, request
from api import api_bp
from worker.queue_manager import (
    thread_health, start_workers, start_producer,
    consumer_threads, producer_running, cleanup
)
import time

@api_bp.route('/thread_health', methods=['GET'])
def get_thread_health():
    """Get detailed health information for all threads."""
    return jsonify(thread_health)

@api_bp.route('/restart', methods=['POST'])
def restart_threads():
    """Force cleanup and restart all threads."""
    global consumer_threads
    
    # Stop all threads
    cleanup()
    
    # Wait for threads to stop
    time.sleep(2)
    
    # Restart workers
    from worker.queue_manager import workers_running
    workers_running = True
    consumer_threads = start_workers(len(consumer_threads))
    
    # Restart producer if it was running
    if producer_running:
        start_producer()
    
    return jsonify({
        'status': 'All threads restarted',
        'worker_count': len(consumer_threads),
        'producer_running': producer_running
    })