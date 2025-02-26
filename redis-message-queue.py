import redis
import requests
import time
import threading

# Create Redis connection
r = redis.StrictRedis(host='localhost', port=6379, db=0)

# Producer: Add HTTP requests to the queue
def producer():
    urls = [
        "https://jsonplaceholder.typicode.com/posts/1",
        "https://jsonplaceholder.typicode.com/posts/2",
        "https://jsonplaceholder.typicode.com/posts/3"
    ]
    
    for url in urls:
        print(f"Adding URL {url} to Redis queue")
        r.lpush('task_queue', url)
        time.sleep(1)  # Simulate delay in task generation

# Consumer: Fetch requests from the queue and execute them
def consumer():
    while True:
        url = r.brpop('task_queue')[1].decode('utf-8')  # Get task from the queue
        try:
            response = requests.get(url)
            print(f"Response status for {url}: {response.status_code}")
        except Exception as e:
            print(f"Request failed for {url}: {e}")

# Start producer and consumer
producer_thread = threading.Thread(target=producer)
consumer_thread = threading.Thread(target=consumer)

producer_thread.start()
consumer_thread.start()

# Wait for producer thread to finish
producer_thread.join()

# Since the Redis queue will keep blocking and waiting for tasks, add an exit condition if needed.
