# AcuNexus

AcuNexus is a self-hosted web application for managing multiple Acumatica ERP instances and deploying REST API endpoints. Built on [Easy-Acumatica](https://github.com/Nioron07/Easy-Acumatica), a Python library for simplified Acumatica REST API integration.

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
- **Database**: PostgreSQL
- **Deployment**: Docker Compose

## Setup

### 1. Clone Repository

```bash
git clone https://github.com/Nioron07/AcuNexus.git
cd AcuNexus
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Update .env with generated keys
```

### 3. Start Services

```bash
# Build and start all services
docker compose up -d

# Check status
docker compose ps
```

### 4. Access Application

Open http://localhost:8080 in your browser.

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

Key environment variables in `.env`:

```env
# Database
POSTGRES_DB=acunexus
POSTGRES_USER=acunexus
POSTGRES_PASSWORD=your-secure-password

# Encryption (REQUIRED)
ENCRYPTION_KEY=your-fernet-key

# Flask
SECRET_KEY=your-secret-key
```

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
# All services
docker compose logs

# Specific service
docker compose logs backend
docker compose logs frontend
```

### Rebuild Services

```bash
# Rebuild and restart
docker compose down
docker compose up -d --build
```

## License

GNU Affero General Public License v3.0 (AGPL-3.0)

See [LICENSE](LICENSE) for details.

## Credits

Built with [Easy-Acumatica](https://github.com/Nioron07/Easy-Acumatica)
