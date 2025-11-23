#!/bin/bash

# Orbu Database Restore Script

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }

echo "=========================================="
echo "     Orbu Database Restore"
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
if ! docker ps | grep -q orbu-postgres; then
    print_error "PostgreSQL container is not running."
    echo "Please start the services with: docker compose up -d"
    exit 1
fi

# List available backups
BACKUP_DIR="./backups"

if [ ! -d "$BACKUP_DIR" ]; then
    print_error "No backup directory found."
    exit 1
fi

echo "Available backups:"
echo
ls -lh "$BACKUP_DIR"/orbu_backup_*.sql* 2>/dev/null | awk '{print NR". "$9" ("$5")"}'

if [ $? -ne 0 ]; then
    print_error "No backups found in $BACKUP_DIR"
    exit 1
fi

echo
read -p "Enter the backup file path (or number from list): " BACKUP_CHOICE

# If user entered a number, get the actual filename
if [[ "$BACKUP_CHOICE" =~ ^[0-9]+$ ]]; then
    BACKUP_FILE=$(ls "$BACKUP_DIR"/orbu_backup_*.sql* 2>/dev/null | sed -n "${BACKUP_CHOICE}p")
else
    BACKUP_FILE="$BACKUP_CHOICE"
fi

if [ ! -f "$BACKUP_FILE" ]; then
    print_error "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Handle encrypted backups
if [[ "$BACKUP_FILE" == *.enc ]]; then
    echo "Encrypted backup detected. Enter decryption password:"
    read -s DECRYPTION_PASSWORD
    TEMP_FILE="/tmp/temp_backup.sql.gz"
    openssl enc -aes-256-cbc -d -in "$BACKUP_FILE" -out "$TEMP_FILE" -k "$DECRYPTION_PASSWORD"
    if [ $? -ne 0 ]; then
        print_error "Failed to decrypt backup"
        exit 1
    fi
    BACKUP_FILE="$TEMP_FILE"
fi

# Handle compressed backups
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "Decompressing backup..."
    TEMP_SQL="/tmp/temp_backup.sql"
    gunzip -c "$BACKUP_FILE" > "$TEMP_SQL"
    BACKUP_FILE="$TEMP_SQL"
fi

# Confirmation
print_warning "This will REPLACE ALL DATA in the database!"
read -p "Are you sure you want to restore from this backup? (yes/no) " -r
echo

if [ "$REPLY" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Stop backend to prevent connections during restore
echo "Stopping backend service..."
docker compose stop backend

# Drop and recreate database
echo "Preparing database for restore..."
docker exec orbu-postgres psql -U ${POSTGRES_USER:-orbu} -c "DROP DATABASE IF EXISTS ${POSTGRES_DB:-orbu};"
docker exec orbu-postgres psql -U ${POSTGRES_USER:-orbu} -c "CREATE DATABASE ${POSTGRES_DB:-orbu};"

# Restore backup
echo "Restoring database..."
docker exec -i orbu-postgres psql -U ${POSTGRES_USER:-orbu} ${POSTGRES_DB:-orbu} < "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    print_success "Database restored successfully!"

    # Restart backend
    echo "Restarting backend service..."
    docker compose start backend

    # Clean up temporary files
    rm -f /tmp/temp_backup.sql /tmp/temp_backup.sql.gz 2>/dev/null

    echo
    print_success "Restore completed successfully!"
    echo
    echo "Please wait a moment for services to restart."
else
    print_error "Restore failed!"
    echo "Attempting to restart backend service..."
    docker compose start backend
    exit 1
fi