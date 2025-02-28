"""
API module initialization.
"""
from flask import Blueprint

# Create a Blueprint for the API routes
api_bp = Blueprint('api', __name__)

# Import routes to register them with the blueprint
from api import routes, health