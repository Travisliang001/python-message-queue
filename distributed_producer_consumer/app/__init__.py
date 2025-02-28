from flask import Flask
from .extensions import init_extensions
from .api import api_bp

def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load default configuration
    app.config.from_mapping(
        PRODUCER_THREADS=1,
        CONSUMER_THREADS=5,
        MONITOR_INTERVAL=5.0,  # seconds
        TASK_QUEUE_MAXSIZE=100
    )
    
    # Override with provided config
    if config:
        app.config.update(config)
    
    # Register extensions
    init_extensions(app)
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    return app