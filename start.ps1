# Multimodal RAG System Launcher - Windows PowerShell Version
# Usage: .\start.ps1 [command]

param(
    [Parameter(Position=0)]
    [string]$Command = "help"
)

Write-Host "Multimodal RAG System Launcher" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if Docker is running
function Test-DockerRunning {
    try {
        $null = docker info 2>&1
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

# Function to check if Python is available
function Test-PythonInstalled {
    try {
        $null = python --version 2>&1
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

# Function to start with Docker
function Start-DockerMode {
    Write-Host "[Docker] Starting with Docker..." -ForegroundColor Green
    
    if (-not (Test-DockerRunning)) {
        Write-Host "[ERROR] Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
        exit 1
    }
    
    # Check if .env file exists
    if (-not (Test-Path .env)) {
        Write-Host "[WARNING] .env file not found. Creating from template..." -ForegroundColor Yellow
        if (Test-Path .env.example) {
            Copy-Item .env.example .env
            Write-Host "[SUCCESS] Created .env file. Please edit it with your API keys!" -ForegroundColor Green
        }
        else {
            Write-Host "[WARNING] Please create .env file with your API keys" -ForegroundColor Yellow
        }
    }
    
    Write-Host "[INFO] Building and starting containers..." -ForegroundColor Cyan
    docker-compose up --build -d
    
    Write-Host "[INFO] Waiting for services to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    Write-Host "[INFO] Checking service health..." -ForegroundColor Cyan
    docker-compose ps
    
    Write-Host ""
    Write-Host "[SUCCESS] System started successfully!" -ForegroundColor Green
    Write-Host "[INFO] Access the application at: http://localhost" -ForegroundColor Cyan
    Write-Host "[INFO] View logs with: docker-compose logs -f" -ForegroundColor Yellow
    Write-Host "[INFO] Stop with: docker-compose down" -ForegroundColor Yellow
}

# Function to start with Docker including monitoring
function Start-DockerMonitoringMode {
    Write-Host "[Docker+Monitoring] Starting with Docker + Monitoring..." -ForegroundColor Green
    
    if (-not (Test-DockerRunning)) {
        Write-Host "[ERROR] Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
        exit 1
    }
    
    if (-not (Test-Path .env)) {
        Write-Host "[WARNING] .env file not found. Creating from template..." -ForegroundColor Yellow
        if (Test-Path .env.example) {
            Copy-Item .env.example .env
            Write-Host "[SUCCESS] Created .env file. Please edit it with your API keys!" -ForegroundColor Green
        }
    }
    
    Write-Host "[INFO] Building and starting containers with monitoring..." -ForegroundColor Cyan
    docker-compose --profile monitoring up --build -d
    
    Write-Host "[INFO] Waiting for services to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    Write-Host "[INFO] Checking service health..." -ForegroundColor Cyan
    docker-compose ps
    
    Write-Host ""
    Write-Host "[SUCCESS] System started successfully!" -ForegroundColor Green
    Write-Host "[INFO] Main app: http://localhost" -ForegroundColor Cyan
    Write-Host "[INFO] Grafana: http://localhost:3000 (admin/admin)" -ForegroundColor Cyan
    Write-Host "[INFO] Prometheus: http://localhost:9090" -ForegroundColor Cyan
    Write-Host "[INFO] View logs: docker-compose logs -f" -ForegroundColor Yellow
    Write-Host "[INFO] Stop: docker-compose --profile monitoring down" -ForegroundColor Yellow
}

# Function to start locally
function Start-LocalMode {
    Write-Host "[Local] Starting locally with Python..." -ForegroundColor Green
    
    if (-not (Test-PythonInstalled)) {
        Write-Host "[ERROR] Python is not installed. Please install Python 3.11+." -ForegroundColor Red
        exit 1
    }
    
    # Check if virtual environment exists
    if (-not (Test-Path venv)) {
        Write-Host "[INFO] Creating virtual environment..." -ForegroundColor Cyan
        python -m venv venv
    }
    
    Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Cyan
    & .\venv\Scripts\Activate.ps1
    
    Write-Host "[INFO] Installing dependencies..." -ForegroundColor Cyan
    pip install -r requirements.txt
    
    # Check if .env file exists
    if (-not (Test-Path .env)) {
        Write-Host "[WARNING] .env file not found. Creating from template..." -ForegroundColor Yellow
        if (Test-Path .env.example) {
            Copy-Item .env.example .env
            Write-Host "[SUCCESS] Created .env file. Please edit it with your API keys!" -ForegroundColor Green
        }
    }
    
    Write-Host "[INFO] Starting the application..." -ForegroundColor Green
    python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
}

# Function to run tests
function Start-TestMode {
    Write-Host "[Test] Running system tests..." -ForegroundColor Green
    
    Write-Host "[INFO] Waiting for system to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    python test_system.py
}

# Function to stop services
function Stop-AllServices {
    Write-Host "[Stop] Stopping services..." -ForegroundColor Yellow
    
    if (Test-DockerRunning) {
        Write-Host "[INFO] Stopping Docker containers..." -ForegroundColor Cyan
        docker-compose down --remove-orphans 2>$null
        docker-compose --profile monitoring down --remove-orphans 2>$null
    }
    else {
        Write-Host "[INFO] No Docker containers to stop" -ForegroundColor Gray
    }
    
    # Kill any local Python processes
    Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "*python*" -and $_.CommandLine -like "*uvicorn*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Host "[SUCCESS] Services stopped." -ForegroundColor Green
}

# Function to show status
function Show-SystemStatus {
    Write-Host "System Status" -ForegroundColor Cyan
    Write-Host "===============" -ForegroundColor Cyan
    Write-Host ""
    
    if (Test-DockerRunning) {
        Write-Host "[Docker] Docker containers:" -ForegroundColor Cyan
        docker-compose ps 2>$null
    }
    else {
        Write-Host "[INFO] Docker is not running" -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "[Testing] Checking endpoints..." -ForegroundColor Cyan
    
    # Test main application
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        Write-Host "[SUCCESS] Main application: http://localhost:8000" -ForegroundColor Green
    }
    catch {
        Write-Host "[ERROR] Main application: Not running" -ForegroundColor Red
    }
    
    # Test if port 80 is running (nginx)
    try {
        $response = Invoke-WebRequest -Uri "http://localhost/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        Write-Host "[SUCCESS] Nginx proxy: http://localhost" -ForegroundColor Green
    }
    catch {
        Write-Host "[ERROR] Nginx proxy: Not running" -ForegroundColor Red
    }
}

# Function to show help
function Show-HelpMessage {
    Write-Host "Usage: .\start.ps1 [COMMAND]" -ForegroundColor White
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Yellow
    Write-Host "  docker          Start with Docker (recommended)" -ForegroundColor White
    Write-Host "  docker-monitor  Start with Docker + monitoring" -ForegroundColor White
    Write-Host "  local           Start locally with Python" -ForegroundColor White
    Write-Host "  test            Run system tests" -ForegroundColor White
    Write-Host "  stop            Stop all services" -ForegroundColor White
    Write-Host "  status          Show system status" -ForegroundColor White
    Write-Host "  help            Show this help message" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\start.ps1 docker          # Start with Docker" -ForegroundColor Gray
    Write-Host "  .\start.ps1 local           # Start locally" -ForegroundColor Gray
    Write-Host "  .\start.ps1 test            # Run tests" -ForegroundColor Gray
    Write-Host "  .\start.ps1 stop            # Stop everything" -ForegroundColor Gray
}

# Main logic
switch ($Command.ToLower()) {
    "docker" {
        Start-DockerMode
    }
    "docker-monitor" {
        Start-DockerMonitoringMode
    }
    "local" {
        Start-LocalMode
    }
    "test" {
        Start-TestMode
    }
    "stop" {
        Stop-AllServices
    }
    "status" {
        Show-SystemStatus
    }
    default {
        Show-HelpMessage
    }
}
