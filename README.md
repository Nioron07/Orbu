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
- **Database**: PostgreSQL
- **Deployment**: Docker Compose

## Quick Start

### Automated Setup (Recommended)

**Windows (PowerShell):**
```powershell
# Clone repository
git clone https://github.com/Nioron07/Orbu.git
cd Orbu

# Run setup script
.\scripts\setup.ps1
```

**Linux/macOS (Bash):**
```bash
# Clone repository
git clone https://github.com/Nioron07/Orbu.git
cd Orbu

# Run setup script
bash scripts/setup.sh
```

The setup script will:
- Check Docker and Docker Compose installation
- Create `.env` file from template
- Generate encryption and secret keys
- Start all services
- Wait for services to be healthy

Access the application at http://localhost:8080

### Manual Setup

If you prefer manual setup:

**Windows (PowerShell):**
```powershell
# 1. Clone repository
git clone https://github.com/Nioron07/Orbu.git
cd Orbu

# 2. Create and configure environment
Copy-Item .env.example .env
python scripts/generate_keys.py  # Generates keys and saves to .env

# 3. Update database password in .env (important!)
# Edit .env and change POSTGRES_PASSWORD to a secure password

# 4. Start services
docker compose up -d

# 5. Check status
docker compose ps
```

**Linux/macOS (Bash):**
```bash
# 1. Clone repository
git clone https://github.com/Nioron07/Orbu.git
cd Orbu

# 2. Create and configure environment
cp .env.example .env
python3 scripts/generate_keys.py  # Generates keys and saves to .env

# 3. Update database password in .env (important!)
# Edit .env and change POSTGRES_PASSWORD to a secure password

# 4. Start services
docker compose up -d

# 5. Check status
docker compose ps
```

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

Key environment variables in `.env`:

```env
# Database
POSTGRES_DB=orbu
POSTGRES_USER=orbu
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
