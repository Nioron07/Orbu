"""
AcuNexus Backend API
Flask application for managing multiple Acumatica connections
"""

import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS
from flask_session import Session
from dotenv import load_dotenv
import logging
from datetime import timedelta

# Import our modules
from database import init_database
from encryption import init_encryption
from api.clients import clients_bp

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
app.config['SESSION_TYPE'] = 'filesystem'  # Will upgrade to redis later
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allow cookies to be sent with top-level navigation
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to cookies

# CORS configuration - allow all origins in development, restrict in production
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:8080')
CORS(app,
     origins=cors_origins.split(',') if ',' in cors_origins else [cors_origins],
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

# Initialize extensions
Session(app)
db = init_database(app)
init_encryption(app)

# Register blueprints
app.register_blueprint(clients_bp)


@app.errorhandler(Exception)
def handle_error(error):
    """Global error handler"""
    logger.error(f"Unhandled error: {str(error)}", exc_info=True)
    return jsonify({
        "success": False,
        "error": str(error),
        "type": type(error).__name__
    }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        db_status = 'healthy'
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = 'unhealthy'

    return jsonify({
        "status": "healthy" if db_status == 'healthy' else "degraded",
        "database": db_status,
        "version": "2.0.0"  # New Docker-based version
    })


@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        "name": "AcuNexus API",
        "version": "2.0.0",
        "description": "Multi-client Acumatica management system",
        "endpoints": {
            "health": "/api/health",
            "clients": "/api/v1/clients",
            "docs": "/api/docs"  # Future: API documentation
        }
    })


# Create database tables
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")


if __name__ == '__main__':
    # Development server
    port = int(os.environ.get('PORT', 5000))

    # For Docker, we need to bind to all interfaces
    if os.environ.get('DOCKER_ENV'):
        host = '0.0.0.0'
    else:
        host = '127.0.0.1'

    app.run(host=host, port=port, debug=True)