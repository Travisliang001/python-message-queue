from flask import jsonify, request, current_app
from . import api_bp
from ..extensions import task_queue, producer_pool, consumer_pool, producer_monitor, consumer_monitor
import uuid
from datetime import datetime

@api_bp.route('/status')
def status():
    """Get system status."""
    return jsonify({
        'producer_pool': {
            'total': producer_pool.get_thread_count(),
            'alive': producer_pool.get_alive_count(),
            'dead': producer_pool.get_dead_count()
        },
        'consumer_pool': {
            'total': consumer_pool.get_thread_count(),
            'alive': consumer_pool.get_alive_count(),
            'dead': consumer_pool.get_dead_count()
        },
        'task_queue': {
            'size': task_queue.size(),
            'empty': task_queue.empty(),
            'full': task_queue.full()
        }
    })

@api_bp.route('/manual-task', methods=['POST'])
def create_manual_task():
    """Manually create a task."""
    data = request.json or {}
    
    task_id = uuid.uuid4().hex
    priority = data.get('priority', 5)
    payload = data.get('payload', {})
    
    # Add timestamp if not provided
    if 'timestamp' not in payload:
        payload['timestamp'] = datetime.now().isoformat()
    
    from ..threads.task import Task
    task = Task(task_id, payload, priority)
    
    if task_queue.push(task):
        return jsonify({
            'status': 'success',
            'message': 'Task created successfully',
            'task_id': task_id
        }), 201
    else:
        return jsonify({
            'status': 'error',
            'message': 'Queue is full, task not created'
        }), 503

@api_bp.route('/config')
def get_config():
    """Get current configuration."""
    return jsonify({
        'producer_threads': current_app.config.get('PRODUCER_THREADS'),
        'consumer_threads': current_app.config.get('CONSUMER_THREADS'),
        'monitor_interval': current_app.config.get('MONITOR_INTERVAL'),
        'task_queue_maxsize': current_app.config.get('TASK_QUEUE_MAXSIZE')
    })