# Orbu Setup Script (PowerShell)
# This script helps set up the Orbu Docker environment on Windows

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "     Orbu Docker Setup Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Function to print colored output
function Print-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Print-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Print-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Print-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

# Check if Docker is installed
function Check-Docker {
    try {
        docker --version | Out-Null
        Print-Success "Docker is installed"
    }
    catch {
        Print-Error "Docker is not installed. Please install Docker Desktop first."
        Write-Host "Visit: https://docs.docker.com/desktop/install/windows-install/"
        exit 1
    }
}

# Check if Docker Compose is installed
function Check-DockerCompose {
    try {
        docker compose version | Out-Null
        Print-Success "Docker Compose is installed"
    }
    catch {
        Print-Error "Docker Compose is not installed. Please install Docker Desktop first."
        Write-Host "Visit: https://docs.docker.com/desktop/install/windows-install/"
        exit 1
    }
}

# Create .env file if it doesn't exist
function Setup-Env {
    if (-not (Test-Path ".env")) {
        Print-Info "Creating .env file from template..."
        Copy-Item ".env.example" ".env"
        Print-Success ".env file created"

        # Use the dedicated key generation script
        Print-Info "Generating encryption and secret keys..."

        # Check if Python is available
        $pythonCmd = $null
        if (Get-Command python -ErrorAction SilentlyContinue) {
            $pythonCmd = "python"
        }
        elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
            $pythonCmd = "python3"
        }

        if ($pythonCmd) {
            # Install required package for key generation
            Print-Info "Installing required Python package (cryptography)..."
            & $pythonCmd -m pip install cryptography --quiet --disable-pip-version-check

            if ($LASTEXITCODE -eq 0) {
                & $pythonCmd scripts/generate_keys.py
                if ($LASTEXITCODE -eq 0) {
                    Print-Success "Keys generated and saved to .env file"
                }
                else {
                    Print-Error "Failed to generate keys"
                    Print-Info "Please run manually: python scripts/generate_keys.py"
                }
            }
            else {
                Print-Warning "Failed to install cryptography package"
                Print-Info "Please install manually: pip install cryptography"
                Print-Info "Then run: python scripts/generate_keys.py"
            }
        }
        else {
            Print-Warning "Python not found. Skipping key generation."
            Print-Info "Please run: python scripts/generate_keys.py"
        }

        Print-Warning "Please review and update the .env file with your specific settings"
        Print-Info "Especially update the database password!"
    }
    else {
        Print-Success ".env file already exists"
    }
}

# Create necessary directories
function Create-Directories {
    Print-Info "Creating necessary directories..."
    New-Item -ItemType Directory -Force -Path "backups" | Out-Null
    Print-Success "Directories created"
}

# Start Docker services
function Start-Services {
    Print-Info "Starting Docker services..."
    docker compose up -d
    Print-Success "Docker services started"
}

# Wait for services to be healthy
function Wait-ForServices {
    Print-Info "Waiting for services to be healthy..."

    # Wait for PostgreSQL
    Write-Host "Waiting for PostgreSQL..." -NoNewline
    for ($i = 1; $i -le 30; $i++) {
        try {
            docker exec orbu-postgres pg_isready -U orbu 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host " Ready!" -ForegroundColor Green
                break
            }
        }
        catch { }
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 2
    }

    # Wait for Backend
    Write-Host "Waiting for Backend API..." -NoNewline
    for ($i = 1; $i -le 30; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8080/api/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Host " Ready!" -ForegroundColor Green
                break
            }
        }
        catch { }
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 2
    }

    Print-Success "All services are healthy"
}

# Main setup flow
function Main {
    Write-Host "Starting Orbu setup..." -ForegroundColor Cyan
    Write-Host ""

    # Check prerequisites
    Check-Docker
    Check-DockerCompose

    # Setup environment
    Setup-Env

    # Create directories
    Create-Directories

    # Start services
    $response = Read-Host "Do you want to start the Docker services now? (y/n)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Start-Services
        Wait-ForServices

        Write-Host ""
        Print-Success "Setup completed successfully!"
        Write-Host ""
        Write-Host "==========================================" -ForegroundColor Cyan
        Write-Host "Orbu is now running!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Access the application at:"
        Write-Host "  -> http://localhost:8080" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "API endpoints:"
        Write-Host "  -> http://localhost:8080/api/health"
        Write-Host "  -> http://localhost:8080/api/v1/clients"
        Write-Host ""
        Write-Host "To stop services: docker compose down"
        Write-Host "To view logs: docker compose logs -f"
        Write-Host "==========================================" -ForegroundColor Cyan
    }
    else {
        Write-Host ""
        Print-Success "Setup completed!"
        Write-Host ""
        Write-Host "To start services manually, run:"
        Write-Host "  docker compose up -d"
    }
}

# Run main function
Main
