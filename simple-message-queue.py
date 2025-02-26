import queue
import threading
import time
import requests

# Create a queue
task_queue = queue.Queue()

# HTTP request handler function
def handle_request():
    while True:
        url = task_queue.get()  # Get task from the queue
        if url is None:  # Termination condition
            break
        try:
            response = requests.get(url)
            print(f"Response status for {url}: {response.status_code}")
        except Exception as e:
            print(f"Request failed for {url}: {e}")
        task_queue.task_done()  # Mark task as done

# Producer: Add HTTP requests to the queue
def producer():
    urls = [
        "https://jsonplaceholder.typicode.com/posts/1",
        "https://jsonplaceholder.typicode.com/posts/2",
        "https://jsonplaceholder.typicode.com/posts/3"
    ]
    
    for url in urls:
        print(f"Adding URL {url} to queue")
        task_queue.put(url)
        time.sleep(1)  # Simulate delay in task generation

# Create multiple consumer threads
consumer_threads = []
for i in range(3):
    t = threading.Thread(target=handle_request)
    t.start()
    consumer_threads.append(t)

# Start producer thread
producer_thread = threading.Thread(target=producer)
producer_thread.start()

# Wait for producer thread to finish
producer_thread.join()

# Send termination signal to consumer threads
for _ in range(3):
    task_queue.put(None)

# Wait for consumer threads to finish
for t in consumer_threads:
    t.join()
