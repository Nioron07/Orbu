# AcuNexus - Multi-Client Acumatica Manager

**AcuNexus** is a self-hosted Docker application for managing multiple Acumatica ERP connections, browsing services and models, and building integrations.

## Features

- 🔗 **Multi-Client Management**: Connect and manage multiple Acumatica instances
- 🔐 **Secure Credential Storage**: Encrypted storage of connection credentials
- 📊 **Service Browser**: Explore available REST API services
- 📋 **Model Browser**: Browse data models and schemas
- 🐳 **Docker-Based**: Easy deployment with Docker Compose
- 🔄 **Session Management**: Persistent sessions with automatic reconnection
- 🎨 **Modern UI**: Vue 3 + Vuetify Material Design interface
- 🌙 **Dark Mode**: Built-in theme switching

## Architecture

AcuNexus v2.0 is built as a containerized web application:

- **Frontend**: Vue 3 + Vuetify 3 + TypeScript
- **Backend**: Flask + SQLAlchemy + EasyAcumatica
- **Database**: PostgreSQL for persistent storage
- **Web Server**: Nginx reverse proxy
- **Deployment**: Docker Compose orchestration

## Prerequisites

- Docker Engine 24.0+
- Docker Compose 2.0+
- 2GB RAM minimum
- 1GB disk space

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/acunexus.git
cd acunexus
```

### 2. Set Up Environment

```bash
# Copy environment template
cp .env.example .env

# Generate encryption keys
python scripts/generate_keys.py

# Or manually generate keys:
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. Run Setup Script

```bash
# Make script executable
chmod +x scripts/setup.sh

# Run setup
./scripts/setup.sh
```

### 4. Start Services

```bash
# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### 5. Access AcuNexus

Open your browser and navigate to:
- **Application**: http://localhost:8080
- **API Health**: http://localhost:8080/api/health

## Manual Setup

If you prefer manual setup over the script:

### Build Frontend

```bash
cd frontend
npm install
npm run build
cd ..
```

### Start Docker Services

```bash
# Start services
docker compose up -d

# Initialize database (first time only)
docker compose exec backend flask db upgrade
```

## Configuration

### Environment Variables

Key environment variables in `.env`:

```env
# Database
POSTGRES_DB=acunexus
POSTGRES_USER=acunexus
POSTGRES_PASSWORD=your-secure-password

# Encryption (REQUIRED - Generate with script)
ENCRYPTION_KEY=your-encryption-key

# Flask
SECRET_KEY=your-secret-key
FLASK_ENV=production

# Ports
NGINX_PORT=8080
```

### Client Configuration

Each Acumatica client connection includes:

- **Basic Settings**:
  - Name and Description
  - Base URL
  - Tenant/Company
  - Branch (optional)

- **Credentials**:
  - Username
  - Password (encrypted)

- **Advanced Options**:
  - SSL Verification
  - Session Persistence
  - Rate Limiting
  - Caching Settings

## Usage

### Managing Clients

1. Navigate to **Clients** page
2. Click **Add Client**
3. Enter connection details
4. Test connection
5. Save and connect

### Browsing Services

1. Connect to a client
2. Navigate to **Services**
3. Search or browse available APIs
4. View method signatures and documentation

### Browsing Models

1. Connect to a client
2. Navigate to **Models**
3. Explore data models
4. View field definitions

## Development

### Local Development Setup

```bash
# Backend development
cd backend
pip install -r requirements.txt
flask run --debug

# Frontend development
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm run test
```

### Building for Production

```bash
# Build all images
docker compose build

# Or build individually
docker compose build backend
docker compose build nginx
```

## Backup & Restore

### Backup Database

```bash
./scripts/backup.sh
```

### Restore Database

```bash
./scripts/restore.sh
```

Backups are stored in `./backups/` with optional encryption.

## API Documentation

### Base URL
```
http://localhost:8080/api/v1
```

### Endpoints

#### Client Management
- `GET /clients` - List all clients
- `POST /clients` - Create client
- `GET /clients/{id}` - Get client details
- `PUT /clients/{id}` - Update client
- `DELETE /clients/{id}` - Delete client

#### Connection
- `POST /clients/{id}/connect` - Connect to client
- `POST /clients/{id}/disconnect` - Disconnect
- `POST /clients/{id}/test` - Test connection

#### Browsing
- `GET /clients/{id}/services` - List services
- `GET /clients/{id}/services/{name}` - Service details
- `GET /clients/{id}/models` - List models
- `GET /clients/{id}/models/{name}` - Model details

## Troubleshooting

### Common Issues

**Cannot connect to database**
```bash
# Check PostgreSQL container
docker compose logs postgres
docker compose restart postgres
```

**Frontend not loading**
```bash
# Rebuild frontend
cd frontend && npm run build
docker compose restart nginx
```

**Connection to Acumatica fails**
- Verify URL is accessible
- Check credentials
- Ensure SSL certificates are valid
- Review firewall settings

### Logs

View logs for debugging:

```bash
# All services
docker compose logs

# Specific service
docker compose logs backend
docker compose logs postgres
docker compose logs nginx

# Follow logs
docker compose logs -f backend
```

## Security

- Credentials are encrypted using Fernet symmetric encryption
- Database passwords are never exposed in logs
- Session tokens expire after 24 hours
- HTTPS recommended for production
- Regular security updates recommended

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).

Key points:
- You can use, modify, and distribute this software
- Any modifications must be open-sourced under AGPL-3.0
- Network use constitutes distribution
- Commercial use is allowed

See [LICENSE](LICENSE) for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/acunexus/issues)
- **Documentation**: [Wiki](https://github.com/yourusername/acunexus/wiki)
- **Email**: support@example.com

## Credits

- Built with [Easy-Acumatica](https://github.com/GISMentors/easy-acumatica)
- Icons by [Material Design Icons](https://materialdesignicons.com/)
- UI Framework: [Vuetify](https://vuetifyjs.com/)

---

**AcuNexus v2.0** - Self-Hosted Docker Edition
Transform from desktop to cloud-ready multi-client management system.