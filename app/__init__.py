"""
Flask Application Factory
Creates and configures the Flask application.
"""
from flask import Flask, render_template
from pathlib import Path
from app.config import Config


def create_app():
    """
    Create and configure Flask application.
    
    Returns:
        Configured Flask application instance
    """
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Ensure necessary folders exist
    Config.ensure_folders_exist()
    
    # Validate configuration
    try:
        Config.validate_config()
    except FileNotFoundError as e:
        print(f"WARNING: {e}")
        print("Please place your trained YOLOv11 model (best.pt) in the weights folder.")
    
    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    # Register index route
    @app.route('/')
    def index():
        """Render main page."""
        return render_template('index.html')
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return render_template('index.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        return render_template('index.html'), 500
    
    return app