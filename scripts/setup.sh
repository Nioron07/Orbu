#!/bin/bash

# AcuNexus Setup Script
# This script helps set up the AcuNexus Docker environment

set -e

echo "=========================================="
echo "     AcuNexus Docker Setup Script"
echo "=========================================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }
print_info() { echo -e "ℹ $1"; }

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    print_success "Docker is installed"
}

# Check if Docker Compose is installed
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    print_success "Docker Compose is installed"
}

# Create .env file if it doesn't exist
setup_env() {
    if [ ! -f .env ]; then
        print_info "Creating .env file from template..."
        cp .env.example .env

        # Generate encryption key
        print_info "Generating encryption key..."
        ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" 2>/dev/null || echo "")

        if [ -z "$ENCRYPTION_KEY" ]; then
            print_warning "Could not generate encryption key automatically."
            print_info "Please run: python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            print_info "And add it to your .env file as ENCRYPTION_KEY="
        else
            # Update .env file with generated key
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                sed -i '' "s/ENCRYPTION_KEY=your-encryption-key-here/ENCRYPTION_KEY=$ENCRYPTION_KEY/" .env
            else
                # Linux
                sed -i "s/ENCRYPTION_KEY=your-encryption-key-here/ENCRYPTION_KEY=$ENCRYPTION_KEY/" .env
            fi
            print_success "Encryption key generated and saved"
        fi

        # Generate secret key
        print_info "Generating Flask secret key..."
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "")

        if [ -z "$SECRET_KEY" ]; then
            print_warning "Could not generate secret key automatically."
            print_info "Please generate a secure secret key and add it to your .env file"
        else
            # Update .env file with generated key
            if [[ "$OSTYPE" == "darwin"* ]]; then
                # macOS
                sed -i '' "s/SECRET_KEY=your-secret-key-here-generate-with-script/SECRET_KEY=$SECRET_KEY/" .env
            else
                # Linux
                sed -i "s/SECRET_KEY=your-secret-key-here-generate-with-script/SECRET_KEY=$SECRET_KEY/" .env
            fi
            print_success "Secret key generated and saved"
        fi

        print_warning "Please review and update the .env file with your specific settings"
        print_info "Especially update the database password!"
    else
        print_success ".env file already exists"
    fi
}

# Build frontend
build_frontend() {
    print_info "Building frontend..."

    if [ ! -d "frontend/dist" ]; then
        cd frontend

        # Install dependencies
        if [ ! -d "node_modules" ]; then
            print_info "Installing frontend dependencies..."
            npm install
        fi

        # Build for production
        print_info "Building frontend for production..."
        npm run build

        cd ..
        print_success "Frontend built successfully"
    else
        print_success "Frontend dist folder already exists"
    fi
}

# Create necessary directories
create_directories() {
    print_info "Creating necessary directories..."
    mkdir -p frontend/dist
    mkdir -p backend/logs
    mkdir -p nginx/logs
    print_success "Directories created"
}

# Start Docker services
start_services() {
    print_info "Starting Docker services..."

    # Use docker compose v2 if available, otherwise fall back to docker-compose
    if docker compose version &> /dev/null; then
        docker compose up -d
    else
        docker-compose up -d
    fi

    print_success "Docker services started"
}

# Wait for services to be healthy
wait_for_services() {
    print_info "Waiting for services to be healthy..."

    # Wait for PostgreSQL
    echo -n "Waiting for PostgreSQL..."
    for i in {1..30}; do
        if docker exec acunexus-postgres pg_isready -U acunexus &> /dev/null; then
            echo " Ready!"
            break
        fi
        echo -n "."
        sleep 2
    done

    # Wait for Backend
    echo -n "Waiting for Backend API..."
    for i in {1..30}; do
        if curl -s http://localhost:8080/api/health > /dev/null; then
            echo " Ready!"
            break
        fi
        echo -n "."
        sleep 2
    done

    print_success "All services are healthy"
}

# Main setup flow
main() {
    echo "Starting AcuNexus setup..."
    echo

    # Check prerequisites
    check_docker
    check_docker_compose

    # Setup environment
    setup_env

    # Create directories
    create_directories

    # Build frontend (optional, can be skipped if using development mode)
    read -p "Do you want to build the frontend for production? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        build_frontend
    fi

    # Start services
    read -p "Do you want to start the Docker services now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        start_services
        wait_for_services

        echo
        print_success "Setup completed successfully!"
        echo
        echo "=========================================="
        echo "AcuNexus is now running!"
        echo
        echo "Access the application at:"
        echo "  → http://localhost:8080"
        echo
        echo "API endpoints:"
        echo "  → http://localhost:8080/api/health"
        echo "  → http://localhost:8080/api/v1/clients"
        echo
        echo "To stop services: docker compose down"
        echo "To view logs: docker compose logs -f"
        echo "=========================================="
    else
        echo
        print_success "Setup completed!"
        echo
        echo "To start services manually, run:"
        echo "  docker compose up -d"
    fi
}

# Run main function
main