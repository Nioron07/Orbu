# Orbu Cloud Deployment (GCP Cloud Run)
# Nginx (Vue frontend) + Flask (API backend)
# Platform-specific files in docker/gcp/, docker/azure/, docker/aws/

# ============================================
# Stage 1: Build Frontend
# ============================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --silent

# Copy frontend source
COPY frontend/ ./

# Build production assets
RUN npm run build

# ============================================
# Stage 2: Python Dependencies
# ============================================
FROM python:3.11-slim AS python-deps

WORKDIR /app

# Copy requirements
COPY backend/requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# Stage 3: Final Image (Nginx + Flask)
# ============================================
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    curl \
    dos2unix \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create application directory
WORKDIR /app

# Copy Python dependencies from build stage
COPY --from=python-deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-deps /usr/local/bin /usr/local/bin

# Make easy_acumatica package directory writable for metadata caching
RUN chmod -R 777 /usr/local/lib/python3.11/site-packages/easy_acumatica || true

# Copy backend application
COPY backend/ /app/backend/

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# Copy Nginx configuration
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf

# Copy initialization scripts (GCP-specific)
RUN mkdir -p /app/docker/gcp
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/gcp/entrypoint.sh /app/entrypoint.sh
COPY docker/gcp/init-secrets.py /app/docker/gcp/init-secrets.py

# Create directories and set permissions
RUN mkdir -p \
    /var/log/supervisor \
    /var/log/nginx \
    /tmp/flask_session \
    /tmp/.easy_acumatica_cache \
    && dos2unix /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh \
    && chown -R www-data:www-data /usr/share/nginx/html \
    && chown -R www-data:www-data /var/log/nginx \
    && chmod -R 777 /tmp/flask_session \
    && chmod -R 777 /tmp/.easy_acumatica_cache

# Default environment variables
ENV FLASK_APP=app.py \
    DOCKER_ENV=true \
    POSTGRES_HOST=postgres \
    POSTGRES_PORT=5432 \
    POSTGRES_DB=orbu \
    POSTGRES_USER=orbu \
    HOME=/tmp

# Expose port 8080 (Cloud Run default)
EXPOSE 8080

# Health check (Cloud Run also has built-in health checks)
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/api/health || exit 1

# Set working directory to backend
WORKDIR /app/backend

# Entrypoint handles secrets and starts supervisor
ENTRYPOINT ["/app/entrypoint.sh"]
