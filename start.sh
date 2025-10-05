
#!/bin/bash

# Multimodal RAG System Launcher
# This script helps you start the system in different modes

set -e

echo "🤖 Multimodal RAG System Launcher"
echo "=================================="

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Function to check if Python is available
check_python() {
    if ! command -v python3 > /dev/null 2>&1; then
        echo "❌ Python 3 is not installed. Please install Python 3.11+."
        exit 1
    fi
}

# Function to start with Docker
start_docker() {
    echo "🐳 Starting with Docker..."
    check_docker
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        echo "⚠️  .env file not found. Creating from template..."
        cp .env.example .env || echo "Please create .env file with your API keys"
    fi
    
    echo "📦 Building and starting containers..."
    docker-compose up --build -d
    
    echo "⏳ Waiting for services to start..."
    sleep 10
    
    echo "🔍 Checking service health..."
    docker-compose ps
    
    echo ""
    echo "✅ System started successfully!"
    echo "🌐 Access the application at: http://localhost"
    echo "📊 View logs with: docker-compose logs -f"
    echo "🛑 Stop with: docker-compose down"
}

# Function to start with Docker including monitoring
start_docker_monitoring() {
    echo "🐳📊 Starting with Docker + Monitoring..."
    check_docker
    
    if [ ! -f .env ]; then
        echo "⚠️  .env file not found. Creating from template..."
        cp .env.example .env || echo "Please create .env file with your API keys"
    fi
    
    echo "📦 Building and starting containers with monitoring..."
    docker-compose --profile monitoring up --build -d
    
    echo "⏳ Waiting for services to start..."
    sleep 15
    
    echo "🔍 Checking service health..."
    docker-compose ps
    
    echo ""
    echo "✅ System started successfully!"
    echo "🌐 Main app: http://localhost"
    echo "📊 Grafana: http://localhost:3000 (admin/admin)"
    echo "🔍 Prometheus: http://localhost:9090"
    echo "📋 View logs: docker-compose logs -f"
    echo "🛑 Stop: docker-compose --profile monitoring down"
}

# Function to start locally
start_local() {
    echo "🐍 Starting locally with Python..."
    check_python
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "📦 Creating virtual environment..."
        python3 -m venv venv
    fi
    
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate || source venv/Scripts/activate
    
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        echo "⚠️  .env file not found. Creating from template..."
        cp .env.example .env || echo "Please create .env file with your API keys"
    fi
    
    echo "🚀 Starting the application..."
    python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
}

# Function to run tests
run_tests() {
    echo "🧪 Running system tests..."
    
    echo "⏳ Waiting for system to be ready..."
    sleep 5
    
    if command -v python3 > /dev/null 2>&1; then
        python3 test_system.py
    else
        python test_system.py
    fi
}

# Function to stop services
stop_services() {
    echo "🛑 Stopping services..."
    
    if docker info > /dev/null 2>&1; then
        echo "🐳 Stopping Docker containers..."
        docker-compose down --remove-orphans
        docker-compose --profile monitoring down --remove-orphans 2>/dev/null || true
    fi
    
    # Kill any local Python processes
    pkill -f "uvicorn src.api.main:app" 2>/dev/null || true
    
    echo "✅ Services stopped."
}

# Function to show status
show_status() {
    echo "📊 System Status"
    echo "==============="
    
    if docker info > /dev/null 2>&1; then
        echo "🐳 Docker containers:"
        docker-compose ps 2>/dev/null || echo "No Docker containers running"
    fi
    
    echo ""
    echo "🌐 Testing endpoints..."
    
    # Test main application
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Main application: http://localhost:8000"
    else
        echo "❌ Main application: Not running"
    fi
    
    # Test if port 80 is running (nginx)
    if curl -s http://localhost/health > /dev/null 2>&1; then
        echo "✅ Nginx proxy: http://localhost"
    else
        echo "❌ Nginx proxy: Not running"
    fi
}

# Function to show help
show_help() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  docker          Start with Docker (recommended)"
    echo "  docker-monitor  Start with Docker + monitoring"
    echo "  local           Start locally with Python"
    echo "  test            Run system tests"
    echo "  stop            Stop all services"
    echo "  status          Show system status"
    echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 docker          # Start with Docker"
    echo "  $0 local           # Start locally"
    echo "  $0 test            # Run tests"
    echo "  $0 stop            # Stop everything"
}

# Main logic
case "${1:-help}" in
    "docker")
        start_docker
        ;;
    "docker-monitor")
        start_docker_monitoring
        ;;
    "local")
        start_local
        ;;
    "test")
        run_tests
        ;;
    "stop")
        stop_services
        ;;
    "status")
        show_status
        ;;
    "help"|*)
        show_help
        ;;
esac