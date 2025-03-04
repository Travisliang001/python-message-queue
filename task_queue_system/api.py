"""API endpoints for the task queue system."""

from flask import Blueprint, jsonify, Flask
from datetime import datetime

from models import (
    worker_status, worker_threads, tasks_status, task_queue
)


def create_api_blueprint():
    """Create the API blueprint."""
    api = Blueprint('api', __name__, url_prefix='/api')
    
    @api.route('/tasks', methods=['GET'])
    def get_tasks():
        """API endpoint to get all tasks and their status."""
        return jsonify({
            "tasks": [task.to_dict() for task in tasks_status.values()],
            "queue_size": task_queue.qsize()
        })

    @api.route('/tasks/<task_id>', methods=['GET'])
    def get_task(task_id):
        """API endpoint to get a specific task's status."""
        if task_id in tasks_status:
            return jsonify(tasks_status[task_id].to_dict())
        else:
            return jsonify({"error": "Task not found"}), 404

    @api.route('/workers', methods=['GET'])
    def get_workers():
        """API endpoint to get worker thread status."""
        serialized_workers = {}
        
        for worker_id, data in worker_status.items():
            # Determine if the worker thread is alive
            is_alive = False
            if worker_id.startswith("worker-"):
                index = int(worker_id.split('-')[1]) - 1
                if 0 <= index < len(worker_threads):
                    is_alive = worker_threads[index].is_alive()
            
            # Format the last_active timestamp
            last_active = data["last_active"]
            if isinstance(last_active, datetime):
                last_active = last_active.isoformat()
            
            serialized_workers[worker_id] = {
                "status": data["status"],
                "last_active": last_active,
                "current_task": data.get("current_task"),
                "is_alive": is_alive
            }
        
        return jsonify({
            "workers": serialized_workers
        })

    @api.route('/stats', methods=['GET'])
    def get_stats():
        """API endpoint to get summary statistics."""
        tasks = list(tasks_status.values())
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
            "queue_size": task_queue.qsize()
        })
    
    return api


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.register_blueprint(create_api_blueprint())
    return app