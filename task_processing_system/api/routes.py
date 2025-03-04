"""API routes for the task queue system."""

from flask import Blueprint, jsonify

from core.queue_manager import (
    get_all_tasks, get_task_by_id, get_queue_size,
    worker_status, worker_threads
)
from api.schemas import serialize_worker_status
from datetime import datetime

api = Blueprint('api', __name__, url_prefix='/api')


@api.route('/tasks', methods=['GET'])
def get_tasks():
    """API endpoint to get all tasks and their status."""
    return jsonify({
        "tasks": [task.to_dict() for task in get_all_tasks()],
        "queue_size": get_queue_size()
    })


@api.route('/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """API endpoint to get a specific task's status."""
    task = get_task_by_id(task_id)
    if task:
        return jsonify(task.to_dict())
    else:
        return jsonify({"error": "Task not found"}), 404


@api.route('/workers', methods=['GET'])
def get_workers():
    """API endpoint to get worker thread status."""
    return jsonify({
        "workers": serialize_worker_status(worker_status, worker_threads)
    })


@api.route('/stats', methods=['GET'])
def get_stats():
    """API endpoint to get summary statistics."""
    tasks = get_all_tasks()
    total = len(tasks)
    pending = sum(1 for task in tasks if task.status == "pending")
    processing = sum(1 for task in tasks if task.status == "processing")
    completed = sum(1 for task in tasks if task.status == "completed")
    failed = sum(1 for task in tasks if task.status == "failed")
    
    return jsonify({
        "total_tasks": total,
        "pending": pending,
        "processing": processing,
        "completed": completed,
        "failed": failed,
        "queue_size": get_queue_size()
    })