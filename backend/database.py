"""
Database configuration and initialization for AcuNexus.
"""

import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize SQLAlchemy without app
db = SQLAlchemy()
migrate = Migrate()

def init_database(app):
    """
    Initialize database with Flask app.

    Args:
        app: Flask application instance
    """
    # Configure database URL
    database_url = os.getenv('DATABASE_URL')

    # Handle Docker Compose PostgreSQL URL format
    if not database_url:
        # Build URL from individual components for local development
        db_user = os.getenv('POSTGRES_USER', 'acunexus')
        db_pass = os.getenv('POSTGRES_PASSWORD', 'changeme')
        db_host = os.getenv('POSTGRES_HOST', 'localhost')
        db_port = os.getenv('POSTGRES_PORT', '5432')
        db_name = os.getenv('POSTGRES_DB', 'acunexus')
        database_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    # SQLAlchemy configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)

    return db