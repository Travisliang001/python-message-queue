import logging
import sys
import uuid
from flask import Flask, jsonify
import threading
import time

# Flask app
app = Flask(__name__)
logger = logging.getLogger(__name__)

# Global variables to track tasks and threads
tasks = {}  # Stores task details
threads = []  # Stores active threads
running = True  # Flag to control thread execution

def task_executor(task_id):
    """Simulate a task execution."""
    tasks[task_id] = {"status": "running", "progress": 0}
    print(f"Task {task_id} started.")

    # Simulate task execution
    for i in range(10):
        if not running:
            break
        time.sleep(1)
        tasks[task_id]["progress"] = (i + 1) * 10  # Update progress percentage

    if running:
        tasks[task_id]["status"] = "completed"
        print(f"Task {task_id} finished.")
    else:
        tasks[task_id]["status"] = "stopped"
        print(f"Task {task_id} stopped.")

def thread_creator():
    """Creates new threads periodically to execute tasks."""
    while running:
        for i in range(5):
            if not running:
                break
            task_id = str(uuid.uuid4())
            thread = threading.Thread(target=task_executor, args=(task_id,))
            thread.start()
            threads.append(thread)

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        time.sleep(15)  # Create new threads every 60 seconds

@app.route("/start_task", methods=["POST"])
def start_task():
    """API to start a new task."""
    task_id = str(len(tasks) + 1)
    thread = threading.Thread(target=task_executor, args=(task_id,))
    thread.start()
    threads.append(thread)

    print(f"Started Task {task_id}.")
    return jsonify({"message": f"Task {task_id} started.", "task_id": task_id})

@app.route("/task_progress", methods=["GET"])
def task_progress():
    """API to get the progress of all tasks."""
    return jsonify(tasks)

@app.route("/stop_tasks", methods=["POST"])
def stop_tasks():
    """API to stop all running tasks."""
    global running
    running = False

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    print("All tasks stopped.")
    return jsonify({"message": "All tasks stopped."})

if __name__ == "__main__":
    try:
        # Start the thread creator in a separate thread
        creator_thread = threading.Thread(target=thread_creator)
        creator_thread.start()

        # Run the Flask server in the main thread
        app.run(debug=False)
    except KeyboardInterrupt:
        print("Program interrupted by user.")
    finally:
        print("Program terminating...")
        running = False
        creator_thread.join(timeout=2)
        for t in threads:
            t.join(timeout=2)
        logger.info("Exiting...")
        sys.exit(0)
