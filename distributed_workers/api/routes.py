"""
API routes for the application.
"""
from flask import jsonify, request
from api import api_bp
from worker.queue_manager import (
    task_queue, start_producer, stop_producer, 
    workers_running, producer_running, producer_thread
)

@api_bp.route('/add_task', methods=['POST'])
def add_task():
    """Add a single task to the queue."""
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'URL not provided'}), 400
    
    url = data['url']
    task_queue.put(url)
    return jsonify({
        'message': f'Task added for URL: {url}', 
        'queue_size': task_queue.qsize()
    })

@api_bp.route('/add_multiple', methods=['POST'])
def add_multiple():
    """Add multiple tasks to the queue."""
    data = request.get_json()
    if not data or 'urls' not in data:
        return jsonify({'error': 'URLs not provided'}), 400
    
    urls = data['urls']
    for url in urls:
        task_queue.put(url)
    
    return jsonify({
        'message': f'Added {len(urls)} tasks to queue',
        'queue_size': task_queue.qsize()
    })

@api_bp.route('/queue_status', methods=['GET'])
def queue_status():
    """Get the current status of the queue and threads."""
    from worker.queue_manager import consumer_threads, thread_health
    
    return jsonify({
        'queue_size': task_queue.qsize(),
        'workers_running': workers_running,
        'producer_running': producer_running and producer_thread and producer_thread.is_alive(),
        'worker_count': len([t for t in consumer_threads if t.is_alive()]),
    })

@api_bp.route('/start_producer', methods=['POST'])
def api_start_producer():
    """Start the producer thread."""
    data = request.get_json() or {}
    interval = data.get('interval', 5)
    urls = data.get('urls', None)
    
    result = start_producer(interval, urls)
    return jsonify(result)

@api_bp.route('/stop_producer', methods=['POST'])
def api_stop_producer():
    """Stop the producer thread."""
    result = stop_producer()
    return jsonify(result)