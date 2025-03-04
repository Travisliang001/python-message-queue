"""Configuration settings for the task queue system."""

# Application settings
DEBUG = False
HOST = '0.0.0.0'
PORT = 5000

# Worker settings
NUM_WORKERS = 5
WORKER_TIMEOUT = 180  # seconds

# Task settings
INITIAL_BATCH_SIZE = 5
BATCH_INTERVAL = 10  # seconds (10 seconds for testing, would be 180 seconds in production)

# Monitoring settings
THREAD_CHECK_INTERVAL = 5  # seconds
WORKER_STUCK_THRESHOLD = 300  # seconds