from flask import Flask
from threading import Event
import queue
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create a shared task queue for producer and consumers
task_queue = queue.Queue(maxsize=100)

# Create shutdown event for coordinated shutdown
shutdown_event = Event()

def create_app(config_object="app.config.DevelopmentConfig"):
    """
    Flask application factory
    """
    app = Flask(__name__)
    app.config.from_object(config_object)
    
    # Register routes
    from app.routes import api
    app.register_blueprint(api)
    
    logger.info("Flask application created")
    return app