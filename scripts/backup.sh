#!/bin/bash

# AcuNexus Database Backup Script

set -e

# Configuration
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="acunexus_backup_${TIMESTAMP}.sql"
ENCRYPTED_BACKUP_FILE="acunexus_backup_${TIMESTAMP}.sql.enc"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "=========================================="
echo "     AcuNexus Database Backup"
echo "=========================================="
echo

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    print_error ".env file not found. Please create it first."
    exit 1
fi

# Check if container is running
if ! docker ps | grep -q acunexus-postgres; then
    print_error "PostgreSQL container is not running."
    echo "Please start the services with: docker compose up -d"
    exit 1
fi

# Create backup
echo "Creating database backup..."
docker exec acunexus-postgres pg_dump -U ${POSTGRES_USER:-acunexus} ${POSTGRES_DB:-acunexus} > "$BACKUP_DIR/$BACKUP_FILE"

if [ $? -eq 0 ]; then
    print_success "Backup created: $BACKUP_DIR/$BACKUP_FILE"

    # Compress backup
    echo "Compressing backup..."
    gzip "$BACKUP_DIR/$BACKUP_FILE"
    print_success "Backup compressed: $BACKUP_DIR/${BACKUP_FILE}.gz"

    # Optional: Encrypt backup (requires openssl)
    if command -v openssl &> /dev/null; then
        read -p "Do you want to encrypt the backup? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Enter encryption password:"
            read -s ENCRYPTION_PASSWORD
            openssl enc -aes-256-cbc -salt -in "$BACKUP_DIR/${BACKUP_FILE}.gz" -out "$BACKUP_DIR/${ENCRYPTED_BACKUP_FILE}" -k "$ENCRYPTION_PASSWORD"
            print_success "Backup encrypted: $BACKUP_DIR/${ENCRYPTED_BACKUP_FILE}"

            # Remove unencrypted backup
            rm "$BACKUP_DIR/${BACKUP_FILE}.gz"
            print_warning "Unencrypted backup removed for security"
        fi
    fi

    # Clean up old backups (keep last 7 days)
    echo "Cleaning up old backups..."
    find "$BACKUP_DIR" -name "acunexus_backup_*.sql*" -mtime +7 -delete
    print_success "Old backups cleaned up (keeping last 7 days)"

    echo
    print_success "Backup completed successfully!"
else
    print_error "Backup failed!"
    exit 1
fi