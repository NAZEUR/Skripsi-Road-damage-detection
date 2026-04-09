"""
Main Entry Point
Run this file to start the Flask application.
Usage: python run.py
"""
import os
from app import create_app

# Create application instance
app = create_app()

if __name__ == '__main__':
    # Get host and port from environment or use defaults
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print("\n" + "="*60)
    print("🚗 Road Damage Detection System")
    print("="*60)
    print(f"Server starting on http://{host}:{port}")
    print("Press CTRL+C to stop")
    print("="*60 + "\n")
    
    # Run application
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )