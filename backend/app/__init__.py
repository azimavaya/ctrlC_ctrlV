"""
Panther Cloud Air Backend API
Flask application factory
"""

from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize extensions
db = SQLAlchemy()

def create_app():
    """
    Create and configure the Flask application
    """
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database configuration
    db_host = os.getenv('DATABASE_HOST', 'localhost')
    db_port = os.getenv('DATABASE_PORT', '3306')
    db_name = os.getenv('DATABASE_NAME', 'panther_cloud_air')
    db_user = os.getenv('DATABASE_USER', 'panther_user')
    db_password = os.getenv('DATABASE_PASSWORD', 'panther_password')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = True  # Log SQL queries in development
    
    # Initialize extensions with app
    db.init_app(app)
    CORS(app)  # Enable CORS for frontend communication
    
    # Register blueprints
    from app.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            print("Database tables created successfully")
        except Exception as e:
            print(f"Error creating database tables: {e}")
    
    # Health check route
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Panther Cloud Air API is running'}
    
    return app