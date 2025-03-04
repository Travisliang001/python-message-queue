from flask import Flask

def create_api(app):
    """Register API blueprints with the Flask app."""
    from api.routes import api
    app.register_blueprint(api)
    return app