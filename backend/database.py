"""
Database configuration and initialization for Orbu.
Supports local PostgreSQL, Cloud SQL via Unix socket, and Cloud SQL via Python Connector.
"""

import os
from urllib.parse import quote_plus
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize SQLAlchemy without app
db = SQLAlchemy()
migrate = Migrate()


def get_cloud_sql_connector():
    """Create a Cloud SQL Connector connection factory for cross-project access."""
    try:
        from google.cloud.sql.connector import Connector
        import pg8000

        connector = Connector()

        def getconn():
            instance_connection = os.getenv('CLOUD_SQL_CONNECTION')
            conn = connector.connect(
                instance_connection,
                "pg8000",
                user=os.getenv('POSTGRES_USER', 'orbu'),
                password=os.getenv('POSTGRES_PASSWORD'),
                db=os.getenv('POSTGRES_DB', 'orbu'),
            )
            return conn

        return getconn
    except ImportError:
        return None


def init_database(app):
    """
    Initialize database with Flask app.

    Connection methods (in priority order):
    1. DATABASE_URL env var - direct connection string
    2. CLOUD_SQL_CONNECTION env var - use Cloud SQL Python Connector (cross-project)
    3. POSTGRES_HOST starting with /cloudsql/ - Unix socket (same-project Cloud Run)
    4. Individual POSTGRES_* env vars - standard TCP connection (local dev)

    Args:
        app: Flask application instance
    """
    database_url = os.getenv('DATABASE_URL')
    engine_options = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }

    if database_url:
        # Direct DATABASE_URL provided
        pass

    elif os.getenv('CLOUD_SQL_CONNECTION'):
        # Cross-project Cloud SQL via Python Connector
        connector_factory = get_cloud_sql_connector()
        if connector_factory:
            # Use pg8000 with connector
            database_url = "postgresql+pg8000://"
            engine_options['creator'] = connector_factory
            app.logger.info(f"Using Cloud SQL Connector for: {os.getenv('CLOUD_SQL_CONNECTION')}")
        else:
            raise RuntimeError(
                "CLOUD_SQL_CONNECTION is set but google-cloud-sql-connector is not installed. "
                "Install with: pip install cloud-sql-python-connector[pg8000]"
            )

    else:
        # Build URL from individual components
        db_user = os.getenv('POSTGRES_USER', 'orbu')
        db_pass = os.getenv('POSTGRES_PASSWORD', 'changeme')
        db_host = os.getenv('POSTGRES_HOST', 'localhost')
        db_port = os.getenv('POSTGRES_PORT', '5432')
        db_name = os.getenv('POSTGRES_DB', 'orbu')

        # URL-encode the password to handle special characters like @
        db_pass_encoded = quote_plus(db_pass)

        if db_host.startswith('/cloudsql/'):
            # Cloud SQL Unix socket (same-project Cloud Run)
            # Format: postgresql://user:pass@/dbname?host=/cloudsql/project:region:instance
            database_url = f"postgresql://{db_user}:{db_pass_encoded}@/{db_name}?host={db_host}"
            app.logger.info(f"Using Cloud SQL Unix socket: {db_host}")
        else:
            # Standard TCP connection (local development)
            database_url = f"postgresql://{db_user}:{db_pass_encoded}@{db_host}:{db_port}/{db_name}"

    # SQLAlchemy configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = engine_options

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)

    return db
