import pika
import requests
import time
import threading

# Connect to RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declare queue
channel.queue_declare(queue='http_requests')

# Producer: Add HTTP requests to the queue
def producer():
    urls = [
        "https://jsonplaceholder.typicode.com/posts/1",
        "https://jsonplaceholder.typicode.com/posts/2",
        "https://jsonplaceholder.typicode.com/posts/3"
    ]
    
    for url in urls:
        print(f"Adding URL {url} to RabbitMQ queue")
        channel.basic_publish(exchange='',
                              routing_key='http_requests',
                              body=url)
        time.sleep(1)  # Simulate delay in task generation

# Consumer: Process HTTP requests
def consumer(ch, method, properties, body):
    url = body.decode('utf-8')
    try:
        response = requests.get(url)
        print(f"Response status for {url}: {response.status_code}")
    except Exception as e:
        print(f"Request failed for {url}: {e}")

# Start consumer
channel.basic_consume(queue='http_requests', on_message_callback=consumer, auto_ack=True)

# Start producer
producer_thread = threading.Thread(target=producer)
producer_thread.start()

# Start consumer and wait for messages
print('Waiting for consumer to process HTTP requests...')
producer_thread.join()
channel.start_consuming()
