# Run Multimodal RAG System Locally
# This script runs the app without full Docker rebuild

Write-Host "Starting Multimodal RAG System (Local Mode)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check if ChromaDB is running
Write-Host "[INFO] Checking ChromaDB..." -ForegroundColor Yellow
$chromaStatus = docker ps --filter "name=multimodal_rag_chromadb" --format "{{.Status}}"
if (-not $chromaStatus) {
    Write-Host "[INFO] Starting ChromaDB and Redis..." -ForegroundColor Yellow
    docker-compose -f docker-compose.simple.yml up -d
    Start-Sleep -Seconds 3
}
else {
    Write-Host "[SUCCESS] ChromaDB is running" -ForegroundColor Green
}

# Check Python
Write-Host "[INFO] Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "  Found: $pythonVersion" -ForegroundColor Gray

# Set environment
$env:PYTHONPATH = $PWD.Path
Write-Host "[INFO] PYTHONPATH set to: $env:PYTHONPATH" -ForegroundColor Gray

Write-Host ""
Write-Host "[SUCCESS] Starting FastAPI application..." -ForegroundColor Green
Write-Host "  URL: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Run the application
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
