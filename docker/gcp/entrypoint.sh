#!/bin/bash
set -e

echo "============================================"
echo "   Orbu Container Initialization"
echo "============================================"
echo "Timestamp: $(date)"
echo "============================================"

# Step 1: Initialize secrets (for GCP, fetches from Secret Manager)
echo ""
echo "[1/3] Initializing secrets..."
python3 /app/docker/gcp/init-secrets.py

# Source the generated secrets
if [ -f /tmp/orbu-secrets.env ]; then
    echo "Loading secrets into environment..."
    source /tmp/orbu-secrets.env
else
    echo "WARNING: Secrets file not found, using environment variables"
fi

# Step 2: Wait for database and run migrations
echo ""
echo "[2/3] Database setup..."

# Don't set DATABASE_URL here - let database.py handle the connection logic
# It will detect CLOUD_SQL_CONNECTION or POSTGRES_HOST and choose the right method
echo "  Database: ${POSTGRES_DB} (user: ${POSTGRES_USER})"
if [ -n "${CLOUD_SQL_CONNECTION}" ]; then
    echo "  Connection: Cloud SQL Python Connector"
    echo "  Instance: ${CLOUD_SQL_CONNECTION}"
elif [[ "${POSTGRES_HOST}" == /cloudsql/* ]]; then
    echo "  Connection: Cloud SQL Unix socket"
    echo "  Socket: ${POSTGRES_HOST}"
else
    echo "  Connection: TCP to ${POSTGRES_HOST}:${POSTGRES_PORT:-5432}"
fi

# Wait for database to be ready (skip for Cloud SQL, handled by connector/socket)
echo "  Waiting for database..."
sleep 5

# Create database schema
cd /app/backend
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/app/backend')

try:
    from app import app, db
    print("  Creating/verifying database tables...")
    with app.app_context():
        db.create_all()
        print("  Database schema ready!")
except Exception as e:
    print(f"  WARNING: Schema setup failed: {e}")
    print("  Will retry on first request")
PYEOF

# Step 3: Start services
echo ""
echo "[3/3] Starting services..."
echo "  Nginx (frontend) + Gunicorn (backend)"
echo ""
echo "============================================"
echo "Initialization complete!"
echo "============================================"
echo ""

# Execute supervisord as PID 1
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
