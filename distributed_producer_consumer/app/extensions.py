from .threads.monitor import ProducerMonitor, ConsumerMonitor
from .threads.pools import ProducerPool, ConsumerPool
from .threads.task import TaskQueue

# Global objects that will be initialized with the Flask app
producer_monitor = ProducerMonitor()
consumer_monitor = ConsumerMonitor()
task_queue = TaskQueue()
producer_pool = ProducerPool()
consumer_pool = ConsumerPool()

def init_extensions(app):
    """Initialize all extensions with the Flask app."""
    # Initialize the task queue first
    task_queue.init_app(app)
    
    # Initialize thread pools
    producer_pool.init_app(app, task_queue)
    consumer_pool.init_app(app, task_queue)
    
    # Initialize monitors last
    producer_monitor.init_app(app, producer_pool)
    consumer_monitor.init_app(app, consumer_pool)