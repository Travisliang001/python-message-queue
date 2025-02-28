from flask import Blueprint, jsonify, request
from app import task_queue, logger
from app.models.task import Task
import time

api = Blueprint('api', __name__)

@api.route('/status')
def status():
    """Return API status and queue size."""
    return jsonify({
        'status': 'running',
        'queue_size': task_queue.qsize(),
        'timestamp': time.time()
    })

@api.route('/tasks', methods=['POST'])
def add_task():
    """Add a task to the queue."""
    try:
        data = request.get_json()
        if not data or 'task_data' not in data:
            return jsonify({'error': 'Missing task_data field'}), 400
        
        task = Task(data['task_data'], priority=data.get('priority', 5))
        
        # Try to add to queue with a timeout to avoid blocking
        try:
            task_queue.put(task, timeout=2)  
            logger.info(f"Task added to queue: {task.id}")
            return jsonify({'status': 'success', 'task_id': task.id}), 201
        except queue.Full:
            logger.warning("Task queue full, rejecting task")
            return jsonify({'error': 'Queue full, try again later'}), 503
    
    except Exception as e:
        logger.error(f"Error adding task: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api.route('/tasks', methods=['GET'])
def get_tasks_status():
    """Get approximate queue status."""
    return jsonify({
        'queue_size': task_queue.qsize(),
        'queue_full': task_queue.full(),
        'queue_empty': task_queue.empty()
    })