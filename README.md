# Orbu

Orbu is a self-hosted integration studio for Acumatica ERP. Manage multiple Acumatica instances and deploy REST API endpoints with ease. Built on [Easy-Acumatica](https://github.com/Nioron07/Easy-Acumatica), a Python library for simplified Acumatica REST API integration.

## Features

- **Multi-Client Management**: Connect and manage multiple Acumatica instances with encrypted credential storage
- **Service Browser**: Explore available REST API services and their methods
- **Model Browser**: Browse data models and schemas
- **Endpoint Deployment**: Deploy service methods as REST API endpoints with automatic schema generation
- **Endpoint Testing**: Test endpoints directly from the UI with parameter validation
- **Dark Mode**: Built-in light/dark theme switching

## Architecture

- **Frontend**: Vue 3 + Vuetify 3 + TypeScript
- **Backend**: Flask + SQLAlchemy + Easy-Acumatica
- **Database**: PostgreSQL (Cloud SQL in production)
- **Deployment**: Docker Compose (local) / Cloud Run (production)

## Quick Start

**Prerequisites:** Docker and Docker Compose

```bash
# Clone repository
git clone https://github.com/Nioron07/Orbu.git
cd Orbu

# Start Orbu
docker compose up -d
```

The container will automatically:
- Start PostgreSQL database
- Generate encryption keys and secrets
- Create database schema
- Start Nginx (frontend) and Flask (backend)

Access the application at http://localhost:8080

## Usage

### Client Management

1. Navigate to Clients page
2. Click "Add Client"
3. Enter Acumatica connection details (URL, tenant, credentials)
4. Connect to the client

### Browse Services & Models

1. Connect to a client
2. Navigate to Services or Models pages
3. Search and explore available APIs and data structures

### Deploy Endpoints

1. Navigate to Services page
2. Select a service and view its methods
3. Click "Deploy as Endpoint" for any method
4. The endpoint is now available as a REST API

### Test Endpoints

1. Navigate to Endpoints page
2. Click the menu icon on any endpoint
3. Select "Test Endpoint"
4. Fill in required parameters
5. View the response

## API Endpoints

All deployed endpoints are accessible at:

```
POST http://localhost:8080/api/v1/endpoints/{client_id}/{service_name}/{method_name}
```

Headers:
```
Content-Type: application/json
X-API-Key: {your-api-key}
```

## Configuration

Configuration is optional. Sensible defaults are provided for local development.

**Environment variables** (in `.env`):

```env
# Database
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=orbu
POSTGRES_USER=orbu
POSTGRES_PASSWORD=devpassword

# Application
CORS_ORIGINS=*
PORT=8080

# GCP (production only)
# GCP_PROJECT_ID=your-project-id
```

## GCP Production Deployment

Orbu is designed for Google Cloud Run with Cloud SQL.

### Prerequisites

- GCP Project with billing enabled
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed
- Docker installed

### Automated Deployment (Recommended)

Run the interactive deployment script:

```bash
python gcp/deploy.py
```

This script will:
1. Create/configure Cloud SQL instance
2. Setup Secret Manager (PostgreSQL password)
3. Create service account with proper permissions
4. Update cloudrun-service.yaml with your values
5. Build and push Docker image
6. Deploy to Cloud Run

### Manual Deployment

<details>
<summary>Click to expand manual steps</summary>

#### Setup Cloud SQL

```bash
# Create Cloud SQL instance
gcloud sql instances create orbu-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create orbu --instance=orbu-db

# Create user
gcloud sql users create orbu --instance=orbu-db --password=YOUR_PASSWORD
```

#### Setup Secret Manager

```bash
# Store PostgreSQL password (must match Cloud SQL user password)
echo -n "YOUR_PASSWORD" | gcloud secrets create orbu-postgres-password --data-file=-

# Note: The encryption key is auto-generated on first deploy
```

#### Create Service Account

```bash
# Create service account
gcloud iam service-accounts create orbu-sa

# Grant Secret Manager Admin (to auto-create encryption key on first deploy)
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:orbu-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.admin"

# Grant Cloud SQL access
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:orbu-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"
```

#### Build & Deploy

```bash
# Build and push image
docker build -t gcr.io/${PROJECT_ID}/orbu:latest .
docker push gcr.io/${PROJECT_ID}/orbu:latest

# Update gcp/cloudrun-service.yaml with your values:
# - <PROJECT_ID>
# - <REGION>
# - <INSTANCE_NAME>

# Deploy
gcloud run services replace gcp/cloudrun-service.yaml --region=us-central1

# Get URL
gcloud run services describe orbu --region=us-central1 --format='value(status.url)'
```

</details>

## Development

### Backend

```bash
cd backend
pip install -r requirements.txt
flask run --debug
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Troubleshooting

### View Logs

```bash
docker compose logs -f
```

### Restart

```bash
docker compose down
docker compose up -d --build
```

### Clean Slate

```bash
docker compose down -v
docker compose up -d
```

## License

GNU Affero General Public License v3.0 (AGPL-3.0)

See [LICENSE](LICENSE) for details.

## Credits

Built with [Easy-Acumatica](https://github.com/Nioron07/Easy-Acumatica)
