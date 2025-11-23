#!/bin/bash

# Orbu Setup Script
# This script helps set up the Orbu Docker environment

set -e

echo "=========================================="
echo "     Orbu Docker Setup Script"
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
        print_success ".env file created"

        # Use the dedicated key generation script
        print_info "Generating encryption and secret keys..."
        if command -v python3 &> /dev/null; then
            python3 scripts/generate_keys.py
            print_success "Keys generated and saved to .env file"
        else
            print_warning "Python3 not found. Skipping key generation."
            print_info "Please run: python3 scripts/generate_keys.py"
        fi

        print_warning "Please review and update the .env file with your specific settings"
        print_info "Especially update the database password!"
    else
        print_success ".env file already exists"
    fi
}

# Create necessary directories
create_directories() {
    print_info "Creating necessary directories..."
    mkdir -p backups
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
        if docker exec orbu-postgres pg_isready -U orbu &> /dev/null; then
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
    echo "Starting Orbu setup..."
    echo

    # Check prerequisites
    check_docker
    check_docker_compose

    # Setup environment
    setup_env

    # Create directories
    create_directories

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
        echo "Orbu is now running!"
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