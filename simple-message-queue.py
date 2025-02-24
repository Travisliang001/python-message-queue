import queue
import threading
import time

# create（FIFO）queue
msg_queue = queue.Queue()

# producer thread
def producer():
    for i in range(5):
        time.sleep(1)  
        msg = f"message{i}"
        msg_queue.put(msg)  # put message into queue
        print(f"producer send：{msg}")

# consumer thread
def consumer():
    while True:
        msg = msg_queue.get()  # get message from queue
        if msg is None:  # termination signal
            break
        print(f"消费者处理：{msg}")
        msg_queue.task_done()  # indicate that the message has been processed
# create threads for producer and consumer
producer_thread = threading.Thread(target=producer)
consumer_thread = threading.Thread(target=consumer)

# start producer and consumer threads
producer_thread.start()
consumer_thread.start()

# wait for producer thread to finish
producer_thread.join()

# send termination signal to consumer thread
msg_queue.put(None)

# waiting for consumer thread to finish
consumer_thread.join()