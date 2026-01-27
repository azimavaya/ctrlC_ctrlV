"""
Panther Cloud Air Backend API
Entry point for running the Flask application
"""

from app import create_app
import os

# Create Flask application instance
app = create_app()

if __name__ == '__main__':
    # Get configuration from environment or use defaults
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    
    print(f"Starting Panther Cloud Air Backend API")
    print(f"Running on http://{host}:{port}")
    print(f"Debug mode: {debug}")
    
    app.run(host=host, port=port, debug=debug)
