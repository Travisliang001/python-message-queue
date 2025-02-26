"""
Configuration for the Flask Queue Worker application.
"""

# Default number of worker threads
DEFAULT_WORKER_COUNT = 3

# Default producer settings
DEFAULT_PRODUCER_INTERVAL = 5
DEFAULT_URLS = [
    "https://jsonplaceholder.typicode.com/posts/1",
    "https://jsonplaceholder.typicode.com/posts/2",
    "https://jsonplaceholder.typicode.com/posts/3"
]

# Request timeout in seconds
REQUEST_TIMEOUT = 10

# Health monitor check interval in seconds
HEALTH_CHECK_INTERVAL = 5

# Flask app settings
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
FLASK_DEBUG = False