"""API schemas and serializers for the task queue system."""

from datetime import datetime


def serialize_worker_status(worker_status, worker_threads):
    """Serialize worker status for API responses.
    
    Args:
        worker_status (dict): Dictionary of worker status information.
        worker_threads (list): List of worker thread objects.
        
    Returns:
        dict: Serialized worker status data.
    """
    serialized = {}
    
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
        
        serialized[worker_id] = {
            "status": data["status"],
            "last_active": last_active,
            "current_task": data.get("current_task"),
            "is_alive": is_alive
        }
    
    return serialized