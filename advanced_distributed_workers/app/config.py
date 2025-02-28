import os

class Config:
    """Base config."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
    DEBUG = False
    TESTING = False
    
    # Thread settings
    CONSUMER_COUNT = 2
    PRODUCER_COUNT = 1
    MONITOR_CHECK_INTERVAL = 5  # seconds
    THREAD_INACTIVITY_THRESHOLD = 60  # seconds


class DevelopmentConfig(Config):
    """Development config."""
    DEBUG = True
    FLASK_ENV = 'development'


class TestingConfig(Config):
    """Testing config."""
    TESTING = True
    DEBUG = True
    FLASK_ENV = 'testing'
    # Use a smaller queue for testing
    TASK_QUEUE_SIZE = 10
    # Faster monitor checks for testing
    MONITOR_CHECK_INTERVAL = 2
    THREAD_INACTIVITY_THRESHOLD = 5


class ProductionConfig(Config):
    """Production config."""
    FLASK_ENV = 'production'
    SECRET_KEY = os.environ.get("SECRET_KEY")
    print(f"SECRET_KEY: {SECRET_KEY}")
    # Ensure this is set in production environment
    assert SECRET_KEY, "SECRET_KEY environment variable must be set in production"