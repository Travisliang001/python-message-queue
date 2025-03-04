import random
import threading
import time
import queue
import uuid
import traceback
from datetime import datetime, timedelta
from flask import Flask, jsonify

# Task queue and tracking data structures
task_queue = queue.Queue()
tasks_status = {}
task_lock = threading.Lock()
running = True  # Flag to control threads

# Thread monitoring
worker_threads = []
worker_status = {}
worker_status_lock = threading.Lock()

# Flask app setup
app = Flask(__name__)

class Task:
    def __init__(self, task_id, description):
        self.task_id = task_id
        self.description = description
        self.status = "pending"  # pending, processing, completed, failed
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None
        self.worker_id = None
        self.error_message = None

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "worker_id": self.worker_id,
            "error_message": self.error_message
        }

def create_task_batch(batch_size=5, batch_number=0):
    """Create a batch of tasks and add them to the queue"""
    print(f"\nCreating batch {batch_number} ({batch_size} tasks)...")
    for i in range(batch_size):
        task_id = str(uuid.uuid4())
        task = Task(task_id, f"Batch {batch_number} - Task {i+1}")
        
        # Add task to tracking
        with task_lock:
            tasks_status[task_id] = task
        
        # Add task to queue
        task_queue.put(task)
        
        print(f"Created task {task_id}: {task.description}")
    
    return batch_number + 1

def process_task(task, worker_id, timeout=180):
    """Process a task with timeout"""
    # Update task status to processing
    with task_lock:
        task.status = "processing"
        task.started_at = datetime.now()
        task.worker_id = worker_id
        tasks_status[task.task_id] = task

    try:
        # Simulate task processing with timeout
        deadline = datetime.now() + timedelta(seconds=timeout)
        
        # Simulate processing time based on task ID
        # This creates a mix of tasks that complete quickly and those that timeout
        # processing_time = min(timeout * (0.5 + (hash(task.task_id) % 100) / 100.0), timeout + 10)
        processing_time = random.uniform(150, 200)
        
        print(f"Worker {worker_id} processing task {task.task_id}: estimated time {processing_time:.1f}s")
        
        # Check if we would exceed the timeout
        remaining_time = (deadline - datetime.now()).total_seconds()
        if processing_time > remaining_time:
            # We'll exceed the timeout, so fail early
            raise TimeoutError(f"Task would take {processing_time:.1f}s but only {remaining_time:.1f}s remaining")
            
        # Simulate work
        time.sleep(3)
        
        # Mark task as completed
        with task_lock:
            task.status = "completed"
            task.completed_at = datetime.now()
            tasks_status[task.task_id] = task
        print(f"Worker {worker_id} completed task {task.task_id}")
            
    except TimeoutError as e:
        # Mark task as failed due to timeout
        with task_lock:
            task.status = "failed"
            task.completed_at = datetime.now()
            task.error_message = str(e)
            tasks_status[task.task_id] = task
        print(f"Worker {worker_id}: Task {task.task_id} failed: {str(e)}")
        
    except Exception as e:
        # Mark task as failed for any other reason
        with task_lock:
            task.status = "failed"
            task.completed_at = datetime.now()
            task.error_message = f"{str(e)}\n{traceback.format_exc()}"
            tasks_status[task.task_id] = task
        print(f"Worker {worker_id}: Task {task.task_id} failed: {str(e)}")

def update_worker_status(worker_id, status, last_active=None, current_task=None):
    """Update the status of a worker thread"""
    with worker_status_lock:
        if last_active is None:
            last_active = datetime.now()
                
        worker_status[worker_id] = {
            "status": status,
            "last_active": last_active,
            "current_task": current_task
        }

def worker_thread(worker_id):
    """Worker thread function to process tasks from the queue"""
    print(f"Worker {worker_id} started")
    update_worker_status(worker_id, "idle")
    
    while running:
        try:
            # Try to get a task with a timeout (so threads can exit if needed)
            task = task_queue.get(timeout=1)
            
            # Update worker status
            update_worker_status(worker_id, "processing", current_task=task.task_id)
            
            # Process the task with timeout
            process_task(task, worker_id)
            
            # Mark task as done in the queue
            task_queue.task_done()
            
            # Update worker status
            update_worker_status(worker_id, "idle")
            
        except queue.Empty:
            # No tasks in the queue, just update worker status and continue waiting
            update_worker_status(worker_id, "idle")
            continue
        except Exception as e:
            # Log the error
            print(f"Worker {worker_id} encountered an error: {str(e)}")
            print(traceback.format_exc())
            
            # Update worker status
            update_worker_status(worker_id, "error")
            
            # Consider whether to restart the thread or continue
            # For now, we'll continue and hope the issue was task-specific
    
    print(f"Worker {worker_id} exiting")
    update_worker_status(worker_id, "terminated")

def task_generator():
    """Thread function that generates new tasks every 3 minutes"""
    batch_number = 0
    print("Task generator started")
    
    # Create initial batch of tasks
    batch_number = create_task_batch(batch_number=batch_number)
    
    # Continue creating batches at regular intervals
    while running:
        # Wait for 3 minutes
        for _ in range(10):  # 3 minutes = 180 seconds
            if not running:
                break
            time.sleep(1)
            
        if running:
            # Create a new batch of tasks
            batch_number = create_task_batch(batch_number=batch_number)
    
    print("Task generator exiting")

def thread_monitor():
    """Monitor worker threads and restart any that have died"""
    print("Thread monitor started")
    
    while running:
        for i, thread in enumerate(worker_threads):
            worker_id = f"worker-{i+1}"
            # randomly pick one to restart
            randomNumber = random.randint(1, 5)
            # Check if thread is alive
            if not thread.is_alive() or randomNumber == i:
                print(f"⚠️ Worker {worker_id} has died, restarting...")
                
                # Create a new thread
                new_thread = threading.Thread(target=worker_thread, args=(worker_id,))
                new_thread.daemon = True
                new_thread.start()
                
                # Replace in the list
                worker_threads[i] = new_thread
                update_worker_status(worker_id, "restarted")
                print(f"✅ Worker {worker_id} restarted")
            
            # Check if worker is stuck (hasn't updated status in too long)
            if worker_id in worker_status:
                last_active = worker_status[worker_id]["last_active"]
                time_since_active = (datetime.now() - last_active).total_seconds()
                
                # If a worker hasn't updated its status in 5 minutes, it might be stuck
                if time_since_active > 300:  # 5 minutes
                    current_status = worker_status[worker_id]["status"]
                    current_task = worker_status[worker_id].get("current_task")
                    
                    print(f"⚠️ Worker {worker_id} appears to be stuck (status: {current_status}, " +
                          f"last active: {time_since_active:.1f}s ago)")
                    
                    # If the worker is stuck on a task, mark that task as failed
                    if current_task and current_task in tasks_status:
                        with task_lock:
                            task = tasks_status[current_task]
                            if task.status == "processing":
                                task.status = "failed"
                                task.completed_at = datetime.now()
                                task.error_message = f"Worker {worker_id} appears to be stuck"
                                tasks_status[current_task] = task
                                print(f"Marked task {current_task} as failed due to stuck worker")
                    
                    # Try to interrupt the thread (not always possible in Python)
                    # In a real system, you might use more robust solutions like a process-per-worker
                    try:
                        # Create a new thread to replace this one
                        new_thread = threading.Thread(target=worker_thread, args=(worker_id,))
                        new_thread.daemon = True
                        new_thread.start()
                        
                        # Replace in the list
                        worker_threads[i] = new_thread
                        update_worker_status(worker_id, "replaced")
                        print(f"✅ Worker {worker_id} replaced")
                    except Exception as e:
                        print(f"❌ Failed to replace worker {worker_id}: {str(e)}")
            
        # Wait for 5 seconds before checking again
        time.sleep(5)
    
    print("Thread monitor exiting")

# Flask routes
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """API endpoint to get all tasks and their status"""
    return jsonify({
        "tasks": [task.to_dict() for task in tasks_status.values()],
        "queue_size": task_queue.qsize()
    })

@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id):
    """API endpoint to get a specific task's status"""
    if task_id in tasks_status:
        return jsonify(tasks_status[task_id].to_dict())
    else:
        return jsonify({"error": "Task not found"}), 404

@app.route('/api/workers', methods=['GET'])
def get_workers():
    """API endpoint to get worker thread status"""
    return jsonify({
        "workers": {
            worker_id: {
                "status": data["status"],
                "last_active": data["last_active"].isoformat() if isinstance(data["last_active"], datetime) else data["last_active"],
                "current_task": data.get("current_task"),
                "is_alive": worker_threads[int(worker_id.split('-')[1]) - 1].is_alive() if worker_id.startswith("worker-") else None
            }
            for worker_id, data in worker_status.items()
        }
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """API endpoint to get summary statistics"""
    total = len(tasks_status)
    pending = sum(1 for task in tasks_status.values() if task.status == "pending")
    processing = sum(1 for task in tasks_status.values() if task.status == "processing")
    completed = sum(1 for task in tasks_status.values() if task.status == "completed")
    failed = sum(1 for task in tasks_status.values() if task.status == "failed")
    
    return jsonify({
        "total_tasks": total,
        "pending": pending,
        "processing": processing,
        "completed": completed,
        "failed": failed,
        "queue_size": task_queue.qsize()
    })

def start_application():
    """Start the worker threads, task generator, and thread monitor"""
    global running, worker_threads
    running = True
    
    # Create worker threads
    worker_threads = []
    for i in range(5):
        worker_id = f"worker-{i+1}"
        t = threading.Thread(target=worker_thread, args=(worker_id,))
        t.daemon = True
        t.start()
        worker_threads.append(t)
        print(f"Started {worker_id}")
    
    # Create task generator thread
    generator_thread = threading.Thread(target=task_generator)
    generator_thread.daemon = True
    generator_thread.start()
    
    # Create thread monitor
    monitor_thread = threading.Thread(target=thread_monitor)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    return worker_threads, generator_thread, monitor_thread

if __name__ == "__main__":
    # Start the worker threads, task generator, and thread monitor
    worker_threads, generator_thread, monitor_thread = start_application()
    
    try:
        # Start the Flask app
        app.run(debug=False, host='0.0.0.0', port=5000)
    finally:
        # Clean shutdown
        print("\nShutting down...")
        running = False
        
        # Wait for threads to exit
        generator_thread.join(timeout=2)
        monitor_thread.join(timeout=2)
        for t in worker_threads:
            t.join(timeout=2)
            
        print("Application shutdown complete")