import queue
import threading
import time
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# Create a global queue
task_queue = queue.Queue()

# Flag to control worker threads
workers_running = True
producer_running = False
producer_thread = None

# HTTP request handler function
def handle_request(worker_id):
    global workers_running
    print(f"Worker thread {worker_id} started")
    while workers_running:
        try:
            # Use timeout to allow checking the workers_running flag periodically
            url = task_queue.get(timeout=1)
            if url is None:  # Termination condition
                task_queue.task_done()
                continue
                
            try:
                response = requests.get(url)
                print(f"Worker {worker_id} - Response status for {url}: {response.status_code}")
            except Exception as e:
                print(f"Worker {worker_id} - Request failed for {url}: {e}")
            task_queue.task_done()
        except queue.Empty:
            # Queue is empty, continue checking workers_running flag
            continue

# Start worker threads
def start_workers(num_workers=3):
    consumer_threads = []
    for i in range(num_workers):
        t = threading.Thread(target=handle_request, args=(i,))
        t.daemon = True  # Set as daemon so threads exit when main thread exits
        t.start()
        consumer_threads.append(t)
    return consumer_threads

# Add task to queue
@app.route('/add_task', methods=['POST'])
def add_task():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'URL not provided'}), 400
    
    url = data['url']
    task_queue.put(url)
    return jsonify({'message': f'Task added for URL: {url}', 'queue_size': task_queue.qsize()})

# Get queue status
@app.route('/queue_status', methods=['GET'])
def queue_status():
    return jsonify({
        'queue_size': task_queue.qsize(),
        'workers_running': workers_running
    })

# Add multiple tasks (like the producer function)
@app.route('/add_multiple', methods=['POST'])
def add_multiple():
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

@app.route('/stop_producer', methods=['POST'])
def api_stop_producer():
    result = stop_producer()
    return jsonify(result)

@app.route('/queue_status', methods=['GET'])
def queue_status():
    return jsonify({
        'queue_size': task_queue.qsize(),
        'workers_running': workers_running,
        'producer_running': producer_running and producer_thread and producer_thread.is_alive()
    })

def stop_producer():
    global producer_running, producer_thread
    
    if producer_thread and producer_thread.is_alive():
        producer_running = False
        producer_thread.join(timeout=2)
        return {"status": "Producer stopped"}
    else:
        return {"status": "No producer running"}
    

def start_producer(interval=5, urls=None):
    global producer_running, producer_thread
    
    # Stop any existing producer
    stop_producer()
    
    # Start new producer
    producer_running = True
    producer_thread = threading.Thread(target=producer, args=(interval, urls))
    producer_thread.daemon = True
    producer_thread.start()
    
    return {"status": "Producer started", "interval": interval, "urls_count": len(urls) if urls else 3}

# Producer function to generate tasks
def producer(interval=5, urls=None):
    global producer_running
    
    if urls is None:
        # Default URLs if none provided
        urls = [
            "https://jsonplaceholder.typicode.com/posts/1",
            "https://jsonplaceholder.typicode.com/posts/2",
            "https://jsonplaceholder.typicode.com/posts/3"
        ]
    
    print(f"Producer started with {len(urls)} URLs")
    
    # Keep track of the index to cycle through URLs
    url_index = 0
    
    while producer_running:
        # Get the next URL in the cycle
        url = urls[url_index % len(urls)]
        url_index += 1
        
        # Add URL to the queue
        print(f"Producer adding URL {url} to queue")
        task_queue.put(url)
        
        # Wait for the next interval
        time.sleep(interval)
    
    print("Producer thread exiting")

@app.route('/start_producer', methods=['POST'])
def api_start_producer():
    data = request.get_json() or {}
    interval = data.get('interval', 5)
    urls = data.get('urls', None)
    
    result = start_producer(interval, urls)
    return jsonify(result)

if __name__ == '__main__':
    # Start worker threads before running the app
    # start a thread to produce the tasks
    
    consumer_threads = start_workers(3)
     # Start the producer thread automatically
    start_producer()
    try:
        # Run the Flask app
        app.run(debug=False, host='0.0.0.0', port=5000)
    finally:
        # The global declaration should NOT be here
        workers_running = False
        producer_running = False

        # Give threads time to terminate gracefully
        print("Shutting down worker threads...")
        time.sleep(2)
        print("Application terminated")