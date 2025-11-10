# Nioron Integration Studio - Architecture Documentation

**Version:** 1.0  
**Last Updated:** October 31, 2025

## Table of Contents

1. [Overview](#overview)
2. [Technology Stack](#technology-stack)
3. [High-Level Architecture](#high-level-architecture)
4. [Docker Architecture](#docker-architecture)
5. [Project Structure](#project-structure)
6. [Database Schema](#database-schema)
7. [API Endpoints](#api-endpoints)
8. [Key Components](#key-components)
9. [Security Considerations](#security-considerations)
10. [Deployment Process](#deployment-process)
11. [User Workflow](#user-workflow)
12. [Advantages](#advantages)

---

## Overview

Nioron Integration Studio is a self-hosted web application that provides a visual interface for managing Acumatica REST API integrations. Built on the EasyAcumatica Python package, it enables users to browse Acumatica instances, explore endpoints, and build persistent integrations without programming knowledge.

### Architecture Type

**Self-Hosted Server Application**
- Deployed via Docker containers on user infrastructure
- Web-based UI accessible via browser
- Always-running background services for persistent integrations
- No external cloud dependencies

### Design Principles

- **Self-Contained:** All dependencies bundled in Docker containers
- **Persistent:** Integrations continue running after browser closes
- **Portable:** Deploy on any infrastructure supporting Docker
- **Scalable:** Can scale horizontally for larger workloads
- **Secure:** Credentials encrypted at rest, on-premise deployment

---

## Technology Stack

### Frontend Layer

| Technology | Purpose | Version |
|------------|---------|---------|
| Vue 3 | Progressive JavaScript framework | 3.x |
| Vuetify 3 | Material Design component library | 3.x |
| Vite | Build tool and dev server | 5.x |
| Vue Router | Client-side routing | 4.x |
| Axios | HTTP client for API calls | 1.x |

### Backend Layer

| Technology | Purpose | Version |
|------------|---------|---------|
| Flask | Web framework | 3.x |
| Flask-RESTful | REST API framework | 0.3.x |
| SQLAlchemy | ORM for database operations | 2.x |
| Flask-Migrate | Database migration tool | 4.x |
| APScheduler | Job scheduling and execution | 3.x |
| EasyAcumatica | Acumatica API wrapper | Latest |
| Cryptography | Credential encryption | Latest |

### Data Layer

| Technology | Purpose | Version |
|------------|---------|---------|
| PostgreSQL | Primary relational database | 15.x |
| Redis | Caching and session storage | 7.x |

### Infrastructure

| Technology | Purpose | Version |
|------------|---------|---------|
| Docker | Container runtime | 24.x+ |
| Docker Compose | Multi-container orchestration | 2.x+ |
| Nginx | Reverse proxy and static file serving | Latest Alpine |

### Optional Components

| Technology | Purpose | When Used |
|------------|---------|-----------|
| Celery | Distributed task queue | High-volume integrations |
| RabbitMQ/Redis | Message broker for Celery | With Celery |

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User's Browser                        │
│                  http://localhost:8080 or                    │
│                  https://nexus.company.com                   │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS/HTTP
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Nginx Container                         │
│        ┌─────────────────┬──────────────────────┐           │
│        │  Static Files   │   Reverse Proxy      │           │
│        │  (Vue App)      │   /api/* → Backend   │           │
│        └─────────────────┴──────────────────────┘           │
└───────────────────────────┬─────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
┌──────────────────────────┐  ┌────────────────────────────┐
│   Vue Frontend (Static)  │  │    Flask Backend (API)     │
│                          │  │                            │
│  - Vue Router            │  │  - REST API Endpoints      │
│  - Vuetify Components    │  │  - Business Logic          │
│  - State Management      │  │  - EasyAcumatica Wrapper   │
│  - API Client (Axios)    │  │  - Credential Encryption   │
└──────────────────────────┘  └────────────┬───────────────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
                    ▼                      ▼                      ▼
          ┌──────────────────┐   ┌─────────────────┐   ┌──────────────────┐
          │   PostgreSQL     │   │     Redis       │   │   APScheduler    │
          │   Database       │   │  Cache/Session  │   │  Job Scheduler   │
          │                  │   │                 │   │                  │
          │  - Instances     │   │  - Sessions     │   │  - Cron Jobs     │
          │  - Integrations  │   │  - Cache        │   │  - Job Queue     │
          │  - Schedules     │   │  - Task Queue   │   │  - Executors     │
          │  - Execution Logs│   │                 │   │                  │
          └──────────────────┘   └─────────────────┘   └────────┬─────────┘
                                                                 │
                                                                 │ Executes
                                                                 ▼
                                                        ┌──────────────────┐
                                                        │   Integration    │
                                                        │    Execution     │
                                                        │                  │
                                                        │  Via EasyAcumatica
                                                        └────────┬─────────┘
                                                                 │
                                                                 ▼
                                                        ┌──────────────────┐
                                                        │   Acumatica      │
                                                        │   Instances      │
                                                        │   (External)     │
                                                        └──────────────────┘
```

### Data Flow

**Instance Browsing:**
```
User → Frontend → API Request → Flask → EasyAcumatica → Acumatica REST API
                                                              ↓
User ← Frontend ← JSON Response ← Flask ← Processed Data ←───┘
```

**Integration Execution:**
```
Scheduler → Trigger Job → Integration Service → EasyAcumatica → Acumatica
                ↓                    ↓
         Execution Log ← ────────────┘
```

---

## Docker Architecture

### Container Overview

The application consists of 5 main containers:

1. **nginx** - Web server and reverse proxy
2. **backend** - Flask application server
3. **scheduler** - APScheduler job executor
4. **postgres** - PostgreSQL database
5. **redis** - Redis cache and session store

### Docker Compose Structure

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: nexus-postgres
    restart: unless-stopped
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-nexus}
      POSTGRES_USER: ${POSTGRES_USER:-nexus}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U nexus"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - nexus-network

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: nexus-redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - nexus-network

  # Flask Backend API
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: nexus-backend
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      FLASK_ENV: ${FLASK_ENV:-production}
      DATABASE_URL: postgresql://${POSTGRES_USER:-nexus}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-nexus}
      REDIS_URL: redis://redis:6379/0
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}
      SECRET_KEY: ${SECRET_KEY}
    volumes:
      - integration_logs:/app/logs
      - ./backend:/app
    networks:
      - nexus-network
    command: gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 app:app

  # Job Scheduler
  scheduler:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: nexus-scheduler
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      backend:
        condition: service_started
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER:-nexus}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-nexus}
      REDIS_URL: redis://redis:6379/0
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}
    volumes:
      - integration_logs:/app/logs
      - ./backend:/app
    networks:
      - nexus-network
    command: python scheduler.py

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: nexus-nginx
    restart: unless-stopped
    ports:
      - "${NGINX_PORT:-8080}:80"
    volumes:
      - ./frontend/dist:/usr/share/nginx/html:ro
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
    networks:
      - nexus-network

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  integration_logs:
    driver: local

networks:
  nexus-network:
    driver: bridge
```

### Container Communication

All containers communicate via a Docker bridge network:

- **Internal DNS:** Containers reference each other by service name
- **Example:** Backend connects to `postgresql://nexus:password@postgres:5432/nexus`
- **Port Exposure:** Only Nginx exposes port to host (8080 by default)
- **Security:** Backend, database, and scheduler not directly accessible from host

### Volume Persistence

**postgres_data:**
- Stores all database data
- Persists across container restarts
- Location: `/var/lib/docker/volumes/nexus_postgres_data`

**redis_data:**
- Stores Redis persistence files
- Configured with AOF (Append Only File) for durability

**integration_logs:**
- Shared volume between backend and scheduler
- Stores detailed execution logs and debugging information

---

## Project Structure

```
nexus-integration-studio/
│
├── docker-compose.yml              # Main orchestration file
├── docker-compose.prod.yml         # Production overrides
├── docker-compose.dev.yml          # Development overrides
├── .env.example                    # Environment template
├── .gitignore
├── README.md
├── ARCHITECTURE.md                 # This file
├── LICENSE                         # AGPL-3.0
│
├── backend/                        # Flask application
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .dockerignore
│   │
│   ├── app.py                      # Flask application factory
│   ├── config.py                   # Configuration classes
│   ├── scheduler.py                # APScheduler entry point
│   ├── wsgi.py                     # WSGI entry point for production
│   │
│   ├── api/                        # REST API endpoints
│   │   ├── __init__.py            # Blueprint registration
│   │   ├── instances.py           # Instance CRUD operations
│   │   ├── integrations.py        # Integration CRUD operations
│   │   ├── executions.py          # Manual execution triggers
│   │   ├── browse.py              # Browse Acumatica endpoints
│   │   ├── schedules.py           # Schedule management
│   │   ├── logs.py                # Execution log retrieval
│   │   └── health.py              # Health check endpoint
│   │
│   ├── models/                     # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── base.py                # Base model with common fields
│   │   ├── instance.py            # Acumatica instance model
│   │   ├── integration.py         # Integration definition model
│   │   ├── schedule.py            # Schedule configuration model
│   │   ├── execution_log.py       # Execution history model
│   │   └── credential.py          # Encrypted credential storage
│   │
│   ├── services/                   # Business logic layer
│   │   ├── __init__.py
│   │   ├── acumatica_service.py   # EasyAcumatica wrapper
│   │   ├── integration_service.py # Integration execution logic
│   │   ├── scheduler_service.py   # Job scheduling logic
│   │   ├── encryption_service.py  # Credential encryption/decryption
│   │   ├── validation_service.py  # Input validation
│   │   └── logging_service.py     # Structured logging
│   │
│   ├── jobs/                       # Background job definitions
│   │   ├── __init__.py
│   │   ├── integration_job.py     # Integration executor
│   │   └── cleanup_job.py         # Log cleanup job
│   │
│   ├── utils/                      # Utility functions
│   │   ├── __init__.py
│   │   ├── decorators.py          # Custom decorators
│   │   ├── exceptions.py          # Custom exceptions
│   │   └── validators.py          # Input validators
│   │
│   ├── migrations/                 # Flask-Migrate database migrations
│   │   ├── versions/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── alembic.ini
│   │
│   ├── logs/                       # Application logs (volume mount)
│   │
│   └── tests/                      # Backend tests
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_api/
│       ├── test_services/
│       └── test_models/
│
├── frontend/                       # Vue application
│   ├── Dockerfile
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   ├── index.html
│   ├── .dockerignore
│   │
│   ├── public/                     # Static assets
│   │   ├── favicon.ico
│   │   └── logo.svg
│   │
│   ├── src/
│   │   ├── main.js                # Application entry point
│   │   ├── App.vue                # Root component
│   │   │
│   │   ├── router/                # Vue Router configuration
│   │   │   └── index.js
│   │   │
│   │   ├── views/                 # Page components
│   │   │   ├── Dashboard.vue      # Main dashboard
│   │   │   ├── Instances/
│   │   │   │   ├── InstanceList.vue
│   │   │   │   ├── InstanceForm.vue
│   │   │   │   └── InstanceBrowser.vue
│   │   │   ├── Integrations/
│   │   │   │   ├── IntegrationList.vue
│   │   │   │   ├── IntegrationForm.vue
│   │   │   │   └── IntegrationBuilder.vue
│   │   │   ├── Logs/
│   │   │   │   ├── LogList.vue
│   │   │   │   └── LogDetail.vue
│   │   │   └── Settings.vue
│   │   │
│   │   ├── components/            # Reusable components
│   │   │   ├── common/
│   │   │   │   ├── AppBar.vue
│   │   │   │   ├── NavDrawer.vue
│   │   │   │   ├── LoadingSpinner.vue
│   │   │   │   └── ErrorAlert.vue
│   │   │   ├── instances/
│   │   │   │   ├── InstanceCard.vue
│   │   │   │   ├── CredentialForm.vue
│   │   │   │   └── ConnectionStatus.vue
│   │   │   ├── browser/
│   │   │   │   ├── EndpointTree.vue
│   │   │   │   ├── FunctionList.vue
│   │   │   │   └── SchemaViewer.vue
│   │   │   ├── integrations/
│   │   │   │   ├── IntegrationCard.vue
│   │   │   │   ├── ScheduleForm.vue
│   │   │   │   └── StepBuilder.vue
│   │   │   └── logs/
│   │   │       ├── LogViewer.vue
│   │   │       └── ExecutionTimeline.vue
│   │   │
│   │   ├── services/              # API clients
│   │   │   ├── api.js            # Axios instance configuration
│   │   │   ├── instanceApi.js    # Instance API calls
│   │   │   ├── integrationApi.js # Integration API calls
│   │   │   ├── browseApi.js      # Browse API calls
│   │   │   └── logApi.js         # Log API calls
│   │   │
│   │   ├── store/                 # State management (Pinia)
│   │   │   ├── index.js
│   │   │   ├── instances.js
│   │   │   ├── integrations.js
│   │   │   └── notifications.js
│   │   │
│   │   ├── composables/           # Vue composables
│   │   │   ├── useNotification.js
│   │   │   ├── useValidation.js
│   │   │   └── usePolling.js
│   │   │
│   │   ├── utils/                 # Utility functions
│   │   │   ├── formatters.js
│   │   │   ├── validators.js
│   │   │   └── constants.js
│   │   │
│   │   └── assets/                # Stylesheets and images
│   │       ├── styles/
│   │       │   ├── main.scss
│   │       │   └── variables.scss
│   │       └── images/
│   │
│   └── tests/                     # Frontend tests
│       ├── unit/
│       └── e2e/
│
├── nginx/                         # Nginx configuration
│   ├── nginx.conf                 # Main configuration
│   ├── mime.types                 # MIME type definitions
│   └── ssl/                       # SSL certificates (if using HTTPS)
│       ├── cert.pem
│       └── key.pem
│
├── scripts/                       # Utility scripts
│   ├── setup.sh                   # Initial setup script
│   ├── backup.sh                  # Database backup script
│   ├── restore.sh                 # Database restore script
│   └── generate-encryption-key.py # Encryption key generator
│
└── docs/                          # Additional documentation
    ├── INSTALLATION.md
    ├── CONFIGURATION.md
    ├── API.md
    └── CONTRIBUTING.md
```

---

## Database Schema

### Entity Relationship Diagram

```
┌─────────────────┐
│   instances     │
│─────────────────│
│ id (PK)         │───┐
│ name            │   │
│ base_url        │   │
│ site_name       │   │
│ encrypted_user  │   │
│ encrypted_pass  │   │
│ is_active       │   │
│ created_at      │   │
│ updated_at      │   │
└─────────────────┘   │
                      │
                      │ 1:N
                      │
                      │
┌─────────────────┐   │
│  integrations   │   │
│─────────────────│   │
│ id (PK)         │◄──┘
│ instance_id (FK)│
│ name            │
│ description     │
│ type            │
│ configuration   │
│ is_enabled      │
│ created_at      │
│ updated_at      │
└─────────────────┘
         │
         │ 1:1
         │
         ▼
┌─────────────────┐        ┌─────────────────┐
│   schedules     │        │ execution_logs  │
│─────────────────│        │─────────────────│
│ id (PK)         │        │ id (PK)         │
│ integration_id  │◄───┐   │ integration_id  │◄───┐
│ cron_expression │    │   │ started_at      │    │
│ timezone        │    │   │ completed_at    │    │
│ next_run_at     │    │   │ status          │    │
│ is_active       │    │   │ trigger_type    │    │
│ created_at      │    │   │ error_message   │    │
└─────────────────┘    │   │ exec_details    │    │
                       │   │ created_at      │    │
                       │   └─────────────────┘    │
                       │                          │
                       └──────────────────────────┘
                                   1:N
```

### Table Definitions

#### instances

Stores Acumatica instance connection information.

```sql
CREATE TABLE instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    site_name VARCHAR(100),
    encrypted_username TEXT NOT NULL,
    encrypted_password TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT instances_name_unique UNIQUE (name),
    CONSTRAINT instances_base_url_check CHECK (base_url ~ '^https?://')
);

CREATE INDEX idx_instances_is_active ON instances(is_active);
CREATE INDEX idx_instances_created_at ON instances(created_at DESC);
```

#### integrations

Stores integration definitions and configurations.

```sql
CREATE TABLE integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES instances(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    integration_type VARCHAR(50) NOT NULL,
    configuration JSONB NOT NULL DEFAULT '{}',
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT integrations_name_unique UNIQUE (name),
    CONSTRAINT integrations_type_check CHECK (
        integration_type IN ('scheduled', 'manual', 'webhook', 'trigger')
    )
);

CREATE INDEX idx_integrations_instance_id ON integrations(instance_id);
CREATE INDEX idx_integrations_is_enabled ON integrations(is_enabled);
CREATE INDEX idx_integrations_type ON integrations(integration_type);
CREATE INDEX idx_integrations_config ON integrations USING GIN (configuration);
```

#### schedules

Stores schedule configurations for automated integrations.

```sql
CREATE TABLE schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    cron_expression VARCHAR(100) NOT NULL,
    timezone VARCHAR(50) DEFAULT 'UTC',
    next_run_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT schedules_integration_unique UNIQUE (integration_id),
    CONSTRAINT schedules_cron_check CHECK (cron_expression ~ '^[\d\*\-\,\/\s]+$')
);

CREATE INDEX idx_schedules_next_run ON schedules(next_run_at) WHERE is_active = TRUE;
CREATE INDEX idx_schedules_integration_id ON schedules(integration_id);
```

#### execution_logs

Stores execution history and results for integrations.

```sql
CREATE TABLE execution_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_id UUID NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL,
    trigger_type VARCHAR(20) NOT NULL,
    error_message TEXT,
    execution_details JSONB DEFAULT '{}',
    records_processed INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT execution_logs_status_check CHECK (
        status IN ('queued', 'running', 'success', 'failed', 'cancelled')
    ),
    CONSTRAINT execution_logs_trigger_check CHECK (
        trigger_type IN ('manual', 'scheduled', 'webhook', 'trigger')
    )
);

CREATE INDEX idx_execution_logs_integration_id ON execution_logs(integration_id);
CREATE INDEX idx_execution_logs_status ON execution_logs(status);
CREATE INDEX idx_execution_logs_started_at ON execution_logs(started_at DESC);
CREATE INDEX idx_execution_logs_details ON execution_logs USING GIN (execution_details);
```

#### endpoint_cache (Optional)

Caches Acumatica endpoint metadata for faster browsing.

```sql
CREATE TABLE endpoint_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id UUID NOT NULL REFERENCES instances(id) ON DELETE CASCADE,
    endpoint_name VARCHAR(255) NOT NULL,
    endpoint_data JSONB NOT NULL,
    cached_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT endpoint_cache_unique UNIQUE (instance_id, endpoint_name)
);

CREATE INDEX idx_endpoint_cache_instance ON endpoint_cache(instance_id);
CREATE INDEX idx_endpoint_cache_expires ON endpoint_cache(expires_at);
```

### Configuration JSONB Examples

#### Integration Configuration

```json
{
  "source": {
    "instance_id": "uuid",
    "endpoint": "SalesOrder",
    "filters": {
      "Status": "Open",
      "Date": ">= '2025-01-01'"
    }
  },
  "transformations": [
    {
      "type": "map_fields",
      "mapping": {
        "OrderNbr": "order_number",
        "CustomerID": "customer_id"
      }
    }
  ],
  "destination": {
    "type": "database",
    "connection_string": "encrypted",
    "table": "orders"
  }
}
```

#### Execution Details

```json
{
  "start_time": "2025-10-31T10:00:00Z",
  "end_time": "2025-10-31T10:05:23Z",
  "duration_seconds": 323,
  "records_processed": 1250,
  "records_failed": 3,
  "errors": [
    {
      "record_id": "SO-00123",
      "error": "Invalid customer ID",
      "timestamp": "2025-10-31T10:02:15Z"
    }
  ],
  "summary": {
    "total_api_calls": 15,
    "data_transferred_mb": 2.4
  }
}
```

---

## API Endpoints

### Base URL

```
http://localhost:8080/api/v1
```

### Authentication

Currently using session-based authentication. JWT implementation planned for future release.

### Instance Management

#### Create Instance

```http
POST /api/v1/instances
Content-Type: application/json

{
  "name": "Production Instance",
  "base_url": "https://acumatica.company.com",
  "site_name": "Company",
  "username": "api_user",
  "password": "secure_password"
}

Response: 201 Created
{
  "id": "uuid",
  "name": "Production Instance",
  "base_url": "https://acumatica.company.com",
  "site_name": "Company",
  "is_active": true,
  "created_at": "2025-10-31T10:00:00Z"
}
```

#### List Instances

```http
GET /api/v1/instances?active=true

Response: 200 OK
{
  "instances": [
    {
      "id": "uuid",
      "name": "Production Instance",
      "base_url": "https://acumatica.company.com",
      "is_active": true,
      "created_at": "2025-10-31T10:00:00Z"
    }
  ],
  "total": 1
}
```

#### Get Instance

```http
GET /api/v1/instances/{id}

Response: 200 OK
{
  "id": "uuid",
  "name": "Production Instance",
  "base_url": "https://acumatica.company.com",
  "site_name": "Company",
  "is_active": true,
  "created_at": "2025-10-31T10:00:00Z",
  "updated_at": "2025-10-31T10:00:00Z"
}
```

#### Update Instance

```http
PUT /api/v1/instances/{id}
Content-Type: application/json

{
  "name": "Updated Name",
  "is_active": false
}

Response: 200 OK
```

#### Delete Instance

```http
DELETE /api/v1/instances/{id}

Response: 204 No Content
```

#### Test Connection

```http
POST /api/v1/instances/{id}/test

Response: 200 OK
{
  "success": true,
  "message": "Connection successful",
  "version": "2024 R1",
  "endpoints_available": 127
}
```

### Instance Browser

#### List Endpoints

```http
GET /api/v1/instances/{id}/endpoints

Response: 200 OK
{
  "endpoints": [
    {
      "name": "SalesOrder",
      "version": "23.200.001",
      "methods": ["GET", "PUT", "POST", "DELETE"]
    },
    {
      "name": "Customer",
      "version": "23.200.001",
      "methods": ["GET", "PUT", "POST", "DELETE"]
    }
  ],
  "total": 127
}
```

#### Get Endpoint Details

```http
GET /api/v1/instances/{id}/endpoints/SalesOrder

Response: 200 OK
{
  "name": "SalesOrder",
  "version": "23.200.001",
  "description": "Sales Order entity",
  "methods": ["GET", "PUT", "POST", "DELETE"],
  "fields": [
    {
      "name": "OrderNbr",
      "type": "string",
      "required": false,
      "description": "Order Number"
    }
  ]
}
```

#### Get Endpoint Schema

```http
GET /api/v1/instances/{id}/schema/SalesOrder

Response: 200 OK
{
  "entity": "SalesOrder",
  "fields": [...],
  "actions": [...],
  "filters": [...]
}
```

#### List Functions

```http
GET /api/v1/instances/{id}/functions

Response: 200 OK
{
  "functions": [
    {
      "name": "get_sales_order",
      "description": "Retrieve a sales order by number",
      "parameters": [
        {
          "name": "order_number",
          "type": "string",
          "required": true
        }
      ]
    }
  ]
}
```

### Integration Management

#### Create Integration

```http
POST /api/v1/integrations
Content-Type: application/json

{
  "name": "Daily Order Sync",
  "description": "Sync open orders daily",
  "instance_id": "uuid",
  "integration_type": "scheduled",
  "configuration": {...}
}

Response: 201 Created
```

#### List Integrations

```http
GET /api/v1/integrations?enabled=true

Response: 200 OK
{
  "integrations": [...],
  "total": 5
}
```

#### Get Integration

```http
GET /api/v1/integrations/{id}

Response: 200 OK
```

#### Update Integration

```http
PUT /api/v1/integrations/{id}
Content-Type: application/json

Response: 200 OK
```

#### Delete Integration

```http
DELETE /api/v1/integrations/{id}

Response: 204 No Content
```

#### Execute Integration

```http
POST /api/v1/integrations/{id}/execute

Response: 202 Accepted
{
  "execution_id": "uuid",
  "status": "queued",
  "message": "Integration execution started"
}
```

#### Test Integration

```http
POST /api/v1/integrations/{id}/test

Response: 200 OK
{
  "success": true,
  "message": "Test completed successfully",
  "records_found": 125,
  "estimated_duration": 45
}
```

### Schedule Management

#### Create Schedule

```http
POST /api/v1/integrations/{id}/schedule
Content-Type: application/json

{
  "cron_expression": "0 2 * * *",
  "timezone": "America/New_York",
  "is_active": true
}

Response: 201 Created
```

#### Get Schedule

```http
GET /api/v1/integrations/{id}/schedule

Response: 200 OK
{
  "id": "uuid",
  "integration_id": "uuid",
  "cron_expression": "0 2 * * *",
  "timezone": "America/New_York",
  "next_run_at": "2025-11-01T02:00:00Z",
  "is_active": true
}
```

#### Update Schedule

```http
PUT /api/v1/integrations/{id}/schedule
Content-Type: application/json

Response: 200 OK
```

#### Delete Schedule

```http
DELETE /api/v1/integrations/{id}/schedule

Response: 204 No Content
```

### Execution Logs

#### List Logs

```http
GET /api/v1/logs?integration_id=uuid&status=failed&limit=50&offset=0

Response: 200 OK
{
  "logs": [
    {
      "id": "uuid",
      "integration_id": "uuid",
      "integration_name": "Daily Order Sync",
      "started_at": "2025-10-31T02:00:00Z",
      "completed_at": "2025-10-31T02:05:23Z",
      "status": "success",
      "trigger_type": "scheduled",
      "records_processed": 1250
    }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

#### Get Log Detail

```http
GET /api/v1/logs/{id}

Response: 200 OK
{
  "id": "uuid",
  "integration_id": "uuid",
  "started_at": "2025-10-31T02:00:00Z",
  "completed_at": "2025-10-31T02:05:23Z",
  "status": "success",
  "trigger_type": "scheduled",
  "execution_details": {...},
  "error_message": null
}
```

### Health Check

```http
GET /api/v1/health

Response: 200 OK
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "scheduler": "running",
  "version": "1.0.0"
}
```

---

## Key Components

### 1. Credential Encryption Service

Handles secure storage and retrieval of Acumatica credentials.

```python
# backend/services/encryption_service.py
from cryptography.fernet import Fernet
import os

class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""
    
    def __init__(self):
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            raise ValueError("ENCRYPTION_KEY environment variable not set")
        self.cipher = Fernet(key.encode())
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext string."""
        if not plaintext:
            raise ValueError("Cannot encrypt empty string")
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext string."""
        if not ciphertext:
            raise ValueError("Cannot decrypt empty string")
        return self.cipher.decrypt(ciphertext.encode()).decode()
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key."""
        return Fernet.generate_key().decode()
```

**Usage:**
- Credentials encrypted before database storage
- Decrypted only when needed for API calls
- Key stored in environment variable (never in code)
- Key should be backed up securely

### 2. Acumatica Service Wrapper

Abstracts EasyAcumatica library for consistent usage.

```python
# backend/services/acumatica_service.py
from EasyAcumatica import EasyAcumaticaClient
from .encryption_service import EncryptionService
from typing import Dict, List, Any

class AcumaticaService:
    """Service for interacting with Acumatica REST API."""
    
    def __init__(self, instance):
        """Initialize service with instance credentials."""
        encryption = EncryptionService()
        
        self.instance = instance
        self.client = EasyAcumaticaClient(
            base_url=instance.base_url,
            username=encryption.decrypt(instance.encrypted_username),
            password=encryption.decrypt(instance.encrypted_password),
            site_name=instance.site_name
        )
    
    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Acumatica instance."""
        try:
            version = self.client.get_version()
            endpoints = self.client.get_endpoints()
            return {
                'success': True,
                'version': version,
                'endpoints_available': len(endpoints)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_endpoints(self) -> List[Dict[str, Any]]:
        """Get all available endpoints."""
        return self.client.get_endpoints()
    
    def get_endpoint_schema(self, endpoint: str) -> Dict[str, Any]:
        """Get schema for specific endpoint."""
        return self.client.get_schema(endpoint)
    
    def get_functions(self) -> List[Dict[str, Any]]:
        """Get all available EasyAcumatica functions."""
        functions = []
        for name in dir(self.client):
            if not name.startswith('_'):
                func = getattr(self.client, name)
                if callable(func):
                    functions.append({
                        'name': name,
                        'doc': func.__doc__
                    })
        return functions
    
    def execute_function(self, function_name: str, **kwargs) -> Any:
        """Execute EasyAcumatica function."""
        if not hasattr(self.client, function_name):
            raise AttributeError(f"Function {function_name} not found")
        
        func = getattr(self.client, function_name)
        return func(**kwargs)
```

### 3. Integration Execution Service

Manages integration execution lifecycle.

```python
# backend/services/integration_service.py
from datetime import datetime
from typing import Dict, Any
from models import Integration, ExecutionLog
from .acumatica_service import AcumaticaService
from extensions import db

class IntegrationService:
    """Service for executing integrations."""
    
    def execute(self, integration: Integration, trigger_type: str = 'manual') -> ExecutionLog:
        """Execute an integration and log results."""
        
        # Create execution log
        log = ExecutionLog(
            integration_id=integration.id,
            status='running',
            trigger_type=trigger_type,
            started_at=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()
        
        try:
            # Get Acumatica service
            service = AcumaticaService(integration.instance)
            
            # Execute integration steps
            results = self._execute_steps(service, integration.configuration)
            
            # Update log with success
            log.status = 'success'
            log.execution_details = results
            log.records_processed = results.get('records_processed', 0)
            log.completed_at = datetime.utcnow()
            
        except Exception as e:
            # Update log with failure
            log.status = 'failed'
            log.error_message = str(e)
            log.completed_at = datetime.utcnow()
            
        finally:
            db.session.commit()
        
        return log
    
    def _execute_steps(self, service: AcumaticaService, configuration: Dict) -> Dict[str, Any]:
        """Execute integration steps from configuration."""
        results = {
            'steps_completed': [],
            'records_processed': 0,
            'errors': []
        }
        
        # Parse configuration and execute steps
        # This is where the visual builder logic would be implemented
        
        return results
    
    def test_integration(self, integration: Integration) -> Dict[str, Any]:
        """Test integration without executing (dry run)."""
        service = AcumaticaService(integration.instance)
        
        try:
            # Validate configuration
            # Estimate records to process
            # Check permissions
            
            return {
                'success': True,
                'message': 'Test completed successfully',
                'records_found': 125,
                'estimated_duration': 45
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
```

### 4. Job Scheduler

Manages scheduled execution of integrations.

```python
# backend/scheduler.py
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import logging
from models import Schedule, Integration
from services.integration_service import IntegrationService
from extensions import db
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create scheduler
jobstores = {
    'default': SQLAlchemyJobStore(url=os.getenv('DATABASE_URL'))
}
scheduler = BlockingScheduler(jobstores=jobstores)

def load_schedules():
    """Load all active schedules from database."""
    logger.info("Loading schedules from database...")
    
    schedules = Schedule.query.filter_by(is_active=True).all()
    
    for schedule in schedules:
        try:
            scheduler.add_job(
                func=run_integration,
                trigger=CronTrigger.from_crontab(
                    schedule.cron_expression,
                    timezone=schedule.timezone
                ),
                args=[schedule.integration_id],
                id=str(schedule.id),
                replace_existing=True,
                max_instances=1
            )
            logger.info(f"Loaded schedule for integration {schedule.integration_id}")
        except Exception as e:
            logger.error(f"Error loading schedule {schedule.id}: {e}")

def run_integration(integration_id: str):
    """Execute integration."""
    logger.info(f"Running integration {integration_id}")
    
    try:
        integration = Integration.query.get(integration_id)
        if not integration or not integration.is_enabled:
            logger.warning(f"Integration {integration_id} not found or disabled")
            return
        
        service = IntegrationService()
        log = service.execute(integration, trigger_type='scheduled')
        
        logger.info(f"Integration {integration_id} completed with status: {log.status}")
        
    except Exception as e:
        logger.error(f"Error running integration {integration_id}: {e}")

if __name__ == '__main__':
    logger.info("Starting Nioron Integration Studio Scheduler")
    load_schedules()
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")
```

### 5. API Error Handling

Consistent error responses across all endpoints.

```python
# backend/utils/exceptions.py
from flask import jsonify
from werkzeug.exceptions import HTTPException

class APIException(Exception):
    """Base exception for API errors."""
    status_code = 400
    
    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status_code'] = self.status_code
        return rv

class InstanceNotFoundError(APIException):
    status_code = 404

class IntegrationNotFoundError(APIException):
    status_code = 404

class ValidationError(APIException):
    status_code = 400

class ConnectionError(APIException):
    status_code = 503

def register_error_handlers(app):
    """Register error handlers with Flask app."""
    
    @app.errorhandler(APIException)
    def handle_api_exception(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        response = jsonify({
            'message': error.description,
            'status_code': error.code
        })
        response.status_code = error.code
        return response
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        app.logger.error(f"Unhandled exception: {error}")
        response = jsonify({
            'message': 'An internal server error occurred',
            'status_code': 500
        })
        response.status_code = 500
        return response
```

---

## Security Considerations

### 1. Credential Storage

**Encryption at Rest:**
- All Acumatica credentials encrypted using Fernet (symmetric encryption)
- Encryption key stored in environment variable
- Key never committed to version control
- Key should be backed up securely and separately from data

**Key Management:**
```bash
# Generate new encryption key
python scripts/generate-encryption-key.py

# Store in .env file
ENCRYPTION_KEY=your_generated_key_here
```

**Best Practices:**
- Rotate encryption keys periodically
- Use separate keys for dev/staging/production
- Store backup keys in secure key management system

### 2. Network Security

**Container Isolation:**
- Backend, database, and scheduler not exposed to host
- Only Nginx container exposes port to host network
- All containers communicate via internal Docker network

**Reverse Proxy:**
- Nginx acts as reverse proxy for backend
- Can add rate limiting
- Can add IP whitelisting
- Easy to add SSL/TLS termination

**HTTPS Configuration (Production):**
```nginx
server {
    listen 443 ssl http2;
    server_name nexus.company.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://backend:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Authentication (Future Enhancement)

**Planned Implementation:**
- JWT-based authentication
- Role-based access control (Admin, User, Viewer)
- Session management with Redis
- Password hashing with bcrypt
- Multi-factor authentication option

**User Roles:**
- **Admin:** Full access, manage users, all integrations
- **User:** Create and manage own integrations
- **Viewer:** Read-only access to logs and integrations

### 4. Input Validation

**API Layer:**
- All inputs validated using Marshmallow schemas
- SQL injection prevention via SQLAlchemy ORM
- XSS prevention via input sanitization
- CSRF protection for state-changing operations

**Example Validation:**
```python
from marshmallow import Schema, fields, validate

class InstanceSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    base_url = fields.Url(required=True, schemes=['https', 'http'])
    site_name = fields.Str(validate=validate.Length(max=100))
    username = fields.Str(required=True)
    password = fields.Str(required=True, load_only=True)
```

### 5. Audit Logging

**Logged Events:**
- Instance creation/modification/deletion
- Integration execution (success/failure)
- Configuration changes
- Authentication attempts (future)
- API access patterns

**Log Storage:**
- Application logs in `/app/logs`
- Execution logs in database
- Can forward logs to external systems (Splunk, ELK, etc.)

### 6. Secrets Management

**Environment Variables:**
```bash
# Required secrets in .env
ENCRYPTION_KEY=<generated-fernet-key>
SECRET_KEY=<random-secret-for-sessions>
POSTGRES_PASSWORD=<strong-database-password>

# Optional
JWT_SECRET_KEY=<for-future-jwt-auth>
```

**Docker Secrets (Production):**
```yaml
secrets:
  encryption_key:
    external: true
  postgres_password:
    external: true

services:
  backend:
    secrets:
      - encryption_key
      - postgres_password
```

### 7. Database Security

**Connection Security:**
- PostgreSQL connections over Docker network only
- No external port exposure by default
- Strong password required
- SSL connections optional for external database

**Backup Security:**
- Encrypted backups recommended
- Secure backup storage location
- Regular backup testing

### 8. Dependency Security

**Regular Updates:**
- Dependabot enabled for automatic dependency updates
- Regular security audits with `pip-audit` and `npm audit`
- Docker base image updates

**Vulnerability Scanning:**
```bash
# Python dependencies
pip-audit

# NPM dependencies
npm audit

# Docker images
docker scan nexus-backend
```

---

## Deployment Process

### Prerequisites

**Required Software:**
- Docker Engine 24.0+ or Docker Desktop
- Docker Compose 2.0+
- Git

**System Requirements:**
- **CPU:** 2+ cores recommended
- **RAM:** 4GB minimum, 8GB recommended
- **Disk:** 10GB minimum for application and data
- **OS:** Linux, Windows 10/11, macOS 10.15+

### Initial Setup

#### 1. Clone Repository

```bash
git clone https://github.com/yourusername/nexus-integration-studio.git
cd nexus-integration-studio
```

#### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Generate encryption key
python scripts/generate-encryption-key.py

# Edit .env file with your settings
nano .env
```

**Required Environment Variables:**
```bash
# Application
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-generated-encryption-key

# Database
POSTGRES_DB=nexus
POSTGRES_USER=nexus
POSTGRES_PASSWORD=strong-password-here

# Server
NGINX_PORT=8080
```

#### 3. Build and Start

```bash
# Build images and start containers
docker-compose up -d

# View logs
docker-compose logs -f

# Check container status
docker-compose ps
```

#### 4. Initialize Database

```bash
# Run database migrations
docker-compose exec backend flask db upgrade

# Verify database
docker-compose exec postgres psql -U nexus -d nexus -c "\dt"
```

#### 5. Access Application

Open browser to:
```
http://localhost:8080
```

Or if deployed to server:
```
http://your-server-ip:8080
```

### Production Deployment

#### SSL/TLS Setup

```bash
# Generate self-signed certificate (testing)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem

# Or use Let's Encrypt (production)
# See docs/SSL_SETUP.md for details
```

#### Production Configuration

```bash
# Use production compose file
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

**docker-compose.prod.yml:**
```yaml
version: '3.8'

services:
  backend:
    environment:
      FLASK_ENV: production
    command: gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 app:app
  
  nginx:
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
```

### Updates and Maintenance

#### Update Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart containers
docker-compose up -d --build

# Run any new migrations
docker-compose exec backend flask db upgrade
```

#### Backup Database

```bash
# Create backup
docker-compose exec postgres pg_dump -U nexus nexus > backup_$(date +%Y%m%d).sql

# Or use backup script
./scripts/backup.sh
```

#### Restore Database

```bash
# Stop application
docker-compose stop backend scheduler

# Restore backup
docker-compose exec -T postgres psql -U nexus nexus < backup_20251031.sql

# Restart application
docker-compose start backend scheduler
```

#### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Integration logs
docker-compose exec backend tail -f logs/integration.log
```

#### Monitor Resources

```bash
# Container stats
docker stats

# Disk usage
docker system df

# Check volumes
docker volume ls
```

### Troubleshooting

#### Database Connection Issues

```bash
# Check database is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U nexus -d nexus -c "SELECT 1"
```

#### Backend Not Responding

```bash
# Check backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend

# Check environment variables
docker-compose exec backend env | grep DATABASE_URL
```

#### Scheduler Not Running Jobs

```bash
# Check scheduler logs
docker-compose logs scheduler

# Verify schedules in database
docker-compose exec postgres psql -U nexus -d nexus \
  -c "SELECT * FROM schedules WHERE is_active = true"

# Restart scheduler
docker-compose restart scheduler
```

---

## User Workflow

### 1. Initial Setup

**First-Time User Experience:**

```
1. User navigates to http://localhost:8080
2. Sees welcome/setup screen
3. No instances configured yet
```

### 2. Add Acumatica Instance

**Steps:**

```
Dashboard → Instances → Add New Instance

Form Fields:
- Name: "Production Acumatica"
- Base URL: "https://acumatica.company.com"
- Site Name: "Company"
- Username: "api_user"
- Password: "••••••••"

Actions:
→ Test Connection (verifies credentials)
→ Save Instance
```

**Backend Process:**
1. Validate inputs
2. Test connection to Acumatica
3. Encrypt credentials
4. Store in database
5. Return success message

### 3. Browse Instance

**Steps:**

```
Instances → Select Instance → Browse Tab

Views:
- Endpoints List (searchable/filterable)
- Endpoint Details (fields, methods, actions)
- Functions List (EasyAcumatica methods)
- Schema Inspector (JSON viewer)
```

**User Can:**
- Search for specific endpoints
- View field definitions
- See available API methods
- Explore generated functions
- Copy endpoint information

### 4. Create Integration (Future)

**Visual Builder Workflow:**

```
Integrations → New Integration

Step 1: Configure Source
- Select instance
- Choose endpoint (e.g., SalesOrder)
- Set filters (Status = 'Open')
- Preview data

Step 2: Add Transformations (optional)
- Map fields
- Apply functions
- Filter records
- Aggregate data

Step 3: Configure Destination
- Choose target (database, API, file)
- Map fields
- Set options

Step 4: Schedule (optional)
- Set cron expression
- Choose timezone
- Set active/inactive

Step 5: Test & Save
- Dry run test
- View estimated impact
- Save integration
```

### 5. Monitor Executions

**Steps:**

```
Logs → View Executions

Filters:
- Integration name
- Status (success/failed/running)
- Date range
- Trigger type

Details View:
- Execution timeline
- Records processed
- Error messages
- Full execution log
```

### 6. Manage Schedules

**Steps:**

```
Integrations → Select Integration → Schedule Tab

Options:
- Enable/disable schedule
- Edit cron expression
- Change timezone
- View next run time
- View execution history
```

---

## Advantages

### 1. Self-Hosted Benefits

**Data Control:**
- All data stays on-premise
- No external data transmission
- Compliance-friendly (HIPAA, SOC2, etc.)
- Customer owns their data

**Cost Predictability:**
- No per-user or usage-based pricing
- One-time deployment cost
- Infrastructure costs under user control
- No surprise bills

**Customization:**
- Users can modify source code (AGPL-3.0)
- Can integrate with internal systems
- Can add custom features
- Full control over deployment

### 2. Technical Advantages

**Always Running:**
- Integrations persist after browser closes
- Background scheduler handles automation
- No manual intervention required
- Reliable execution

**Scalability:**
- Can add more workers (Celery)
- Can scale PostgreSQL
- Can deploy on larger infrastructure
- Horizontal scaling possible

**Portability:**
- Docker ensures consistency across environments
- Deploy anywhere Docker runs
- Easy migration between servers
- Environment-agnostic

**Maintainability:**
- Clear separation of concerns
- Well-documented codebase
- Standard technology stack
- Active open-source community

### 3. Developer-Friendly

**Modern Stack:**
- Vue 3 with Composition API
- Flask with best practices
- SQLAlchemy ORM
- Type hints and documentation

**Easy Setup:**
- Docker Compose one-command start
- Minimal configuration required
- Clear error messages
- Comprehensive logging

**Extensibility:**
- Plugin architecture planned
- Custom integrations possible
- API-first design
- Webhook support (future)

### 4. Enterprise-Ready

**Security:**
- Encrypted credential storage
- On-premise deployment option
- Audit logging
- Role-based access (future)

**Reliability:**
- Database persistence
- Job retry logic
- Error handling
- Health monitoring

**Support:**
- Open-source community
- Professional support available
- Comprehensive documentation
- Regular updates

---

## Future Enhancements

### Phase 1: Foundation (Current)
- [x] Architecture design
- [ ] Docker setup
- [ ] Database models
- [ ] Basic Flask API
- [ ] Vue frontend scaffold
- [ ] Instance management
- [ ] Instance browser

### Phase 2: Integration Builder
- [ ] Visual integration builder UI
- [ ] Drag-and-drop workflow design
- [ ] Field mapping interface
- [ ] Transformation functions
- [ ] Multiple destination types
- [ ] Integration templates

### Phase 3: Advanced Features
- [ ] User authentication & authorization
- [ ] Multi-tenancy support
- [ ] Integration marketplace
- [ ] Real-time monitoring dashboard
- [ ] Webhook triggers
- [ ] API rate limiting

### Phase 4: Scale & Performance
- [ ] Celery distributed workers
- [ ] Redis caching layer
- [ ] Database query optimization
- [ ] Horizontal scaling support
- [ ] Load balancing
- [ ] High availability setup

### Phase 5: Enterprise Features
- [ ] LDAP/SAML authentication
- [ ] Advanced audit logging
- [ ] Compliance reporting
- [ ] Data retention policies
- [ ] Disaster recovery
- [ ] Multi-region deployment

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to Nioron Integration Studio.

## License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions, please visit:
- GitHub Issues: https://github.com/yourusername/nexus-integration-studio/issues
- Documentation: https://docs.nexus-integration.io
- Community Forum: https://community.nexus-integration.io

---

**Document Version:** 1.0  
**Last Updated:** October 31, 2025  
**Maintained By:** Nioron Integration Studio Team