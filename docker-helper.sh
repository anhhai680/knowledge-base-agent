#!/bin/bash

# Docker Deployment Helper Script
# This script helps diagnose and fix common Docker deployment issues

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  Knowledge Base Agent - Docker Helper${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_section() {
    echo -e "\n${YELLOW}$1${NC}"
    echo "----------------------------------------"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

check_prerequisites() {
    print_section "Checking Prerequisites"
    
    # Check Docker
    if command -v docker &> /dev/null; then
        print_success "Docker is installed"
        docker --version
    else
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose is installed"
        docker-compose --version
    else
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if docker info &> /dev/null; then
        print_success "Docker daemon is running"
    else
        print_error "Docker daemon is not running"
        exit 1
    fi
}

check_environment() {
    print_section "Checking Environment"
    
    # Check for .env file
    if [ -f .env ]; then
        print_success ".env file exists"
    else
        print_warning ".env file not found"
        if [ -f .env.sample ]; then
            print_warning "Creating .env from .env.sample"
            cp .env.sample .env
            print_success ".env file created from sample"
        else
            print_error "No .env.sample file found"
        fi
    fi
    
    # Check key environment variables
    source .env 2>/dev/null || true
    
    if [ -n "$LLM_PROVIDER" ]; then
        print_success "LLM_PROVIDER is set to: $LLM_PROVIDER"
    else
        print_warning "LLM_PROVIDER not set, using default: ollama"
    fi
    
    if [ -n "$LLM_MODEL" ]; then
        print_success "LLM_MODEL is set to: $LLM_MODEL"
    else
        print_warning "LLM_MODEL not set, using default: llama3.1:8b"
    fi
    
    if [ -n "$EMBEDDING_MODEL" ]; then
        print_success "EMBEDDING_MODEL is set to: $EMBEDDING_MODEL"
    else
        print_warning "EMBEDDING_MODEL not set, using default: nomic-embed-text"
    fi
}

check_ports() {
    print_section "Checking Port Availability"
    
    ports=(8000 8001 11434)
    port_names=("Main App" "Chroma" "Ollama")
    
    for i in "${!ports[@]}"; do
        port=${ports[$i]}
        name=${port_names[$i]}
        
        if lsof -i :$port &> /dev/null; then
            print_warning "Port $port ($name) is already in use"
            echo "Process using port $port:"
            lsof -i :$port
        else
            print_success "Port $port ($name) is available"
        fi
    done
}

clean_environment() {
    print_section "Cleaning Environment"
    
    echo "Stopping all containers..."
    docker-compose down -v 2>/dev/null || true
    
    echo "Removing orphaned containers..."
    docker system prune -f
    
    echo "Removing unused volumes..."
    docker volume prune -f
    
    print_success "Environment cleaned"
}

start_services() {
    print_section "Starting Services"
    
    echo "Starting Chroma database..."
    docker-compose up -d chroma
    
    echo "Starting Ollama service..."  
    docker-compose up -d ollama
    
    echo "Waiting for services to initialize..."
    sleep 20
    
    # Check if services are responding (don't fail if they're not ready yet)
    echo "Checking service readiness..."
    
    # Check Chroma
    for i in {1..6}; do
        if curl -s http://localhost:8001/api/v1/heartbeat &>/dev/null || \
           curl -s http://localhost:8001/api/v1/version &>/dev/null || \
           curl -s http://localhost:8001/ &>/dev/null; then
            print_success "Chroma is responding"
            break
        else
            echo "Waiting for Chroma... ($i/6)"
            sleep 10
        fi
    done
    
    # Check Ollama
    for i in {1..6}; do
        if curl -s http://localhost:11434/api/version &>/dev/null || \
           curl -s http://localhost:11434/api/tags &>/dev/null; then
            print_success "Ollama is responding"
            break
        else
            echo "Waiting for Ollama... ($i/6)"
            sleep 10
        fi
    done
    
    echo "Starting main application..."
    docker-compose up -d knowledge-base-agent
    
    echo "Waiting for application to start..."
    sleep 30
    
    # Give it more time to fully initialize
    echo "Allowing time for full initialization..."
    sleep 30
}

check_service_health() {
    print_section "Checking Service Health"
    
    # Check Chroma with multiple attempts
    echo "Checking Chroma service..."
    chroma_ready=false
    for i in {1..10}; do
        if curl -s -f http://localhost:8001/api/v1/heartbeat &>/dev/null; then
            print_success "Chroma service is healthy"
            chroma_ready=true
            break
        elif curl -s -f http://localhost:8001/api/v1/version &>/dev/null; then
            print_success "Chroma service is responding (version endpoint)"
            chroma_ready=true
            break
        elif curl -s -f http://localhost:8001/ &>/dev/null; then
            print_success "Chroma service is responding (root endpoint)"
            chroma_ready=true
            break
        else
            echo "Attempt $i/10: Chroma not ready yet..."
            sleep 5
        fi
    done
    
    if [ "$chroma_ready" = false ]; then
        print_error "Chroma service is not responding after 50 seconds"
        echo "Chroma logs:"
        docker-compose logs --tail=20 chroma
        echo "Chroma container status:"
        docker-compose ps chroma
    fi
    
    # Check Ollama
    echo "Checking Ollama service..."
    ollama_ready=false
    for i in {1..6}; do
        if curl -s -f http://localhost:11434/api/version &>/dev/null; then
            print_success "Ollama service is healthy"
            ollama_ready=true
            break
        elif curl -s -f http://localhost:11434/api/tags &>/dev/null; then
            print_success "Ollama service is responding (tags endpoint)"
            ollama_ready=true
            break
        else
            echo "Attempt $i/6: Ollama not ready yet..."
            sleep 5
        fi
    done
    
    if [ "$ollama_ready" = false ]; then
        print_error "Ollama service is not responding after 30 seconds"
        echo "Ollama logs:"
        docker-compose logs --tail=20 ollama
        echo "Ollama container status:"
        docker-compose ps ollama
    fi
    
    # Check main app
    echo "Checking main application..."
    app_ready=false
    for i in {1..12}; do
        if curl -s -f http://localhost:8000/health &>/dev/null; then
            print_success "Main application is healthy"
            app_ready=true
            break
        elif curl -s -f http://localhost:8000/ &>/dev/null; then
            print_success "Main application is responding"
            app_ready=true
            break
        else
            echo "Attempt $i/12: Application not ready yet..."
            sleep 10
        fi
    done
    
    if [ "$app_ready" = false ]; then
        print_warning "Main application is not responding after 2 minutes"
        echo "Application logs:"
        docker-compose logs --tail=30 knowledge-base-agent
        echo "Application container status:"
        docker-compose ps knowledge-base-agent
    fi
}

check_models() {
    print_section "Checking Ollama Models"
    
    # Check if required models are available
    if docker-compose exec -T ollama ollama list | grep -q "llama3.1:8b"; then
        print_success "llama3.1:8b model is available"
    else
        print_warning "llama3.1:8b model not found, pulling..."
        docker-compose exec -T ollama ollama pull llama3.1:8b
    fi
    
    if docker-compose exec -T ollama ollama list | grep -q "nomic-embed-text"; then
        print_success "nomic-embed-text model is available"
    else
        print_warning "nomic-embed-text model not found, pulling..."
        docker-compose exec -T ollama ollama pull nomic-embed-text
    fi
}

show_status() {
    print_section "Container Status"
    docker-compose ps
    
    print_section "Service URLs"
    echo "Main Application: http://localhost:8000"
    echo "API Documentation: http://localhost:8000/docs"
    echo "Health Check: http://localhost:8000/health"
    echo "Configuration: http://localhost:8000/config"
    echo "Chroma: http://localhost:8001"
    echo "Ollama: http://localhost:11434"
}

show_logs() {
    print_section "Recent Logs"
    
    echo "Knowledge Base Agent logs:"
    docker-compose logs --tail=50 knowledge-base-agent
    
    echo -e "\nTo follow logs in real-time:"
    echo "docker-compose logs -f knowledge-base-agent"
}

usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     - Start all services (default)"
    echo "  stop      - Stop all services"
    echo "  restart   - Restart all services"
    echo "  clean     - Clean environment and restart"
    echo "  status    - Show service status"
    echo "  logs      - Show recent logs"
    echo "  health    - Check service health"
    echo "  models    - Check and pull required models"
    echo "  debug     - Start in debug mode"
    echo "  help      - Show this help"
}

main() {
    print_header
    
    case "${1:-start}" in
        "start")
            check_prerequisites
            check_environment
            check_ports
            start_services
            show_status
            ;;
        "stop")
            print_section "Stopping Services"
            docker-compose down
            ;;
        "restart")
            print_section "Restarting Services"
            docker-compose down
            start_services
            show_status
            ;;
        "clean")
            check_prerequisites
            clean_environment
            check_environment
            start_services
            show_status
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "health")
            check_service_health
            ;;
        "models")
            check_models
            ;;
        "debug")
            print_section "Starting in Debug Mode"
            docker-compose up knowledge-base-agent
            ;;
        "help")
            usage
            ;;
        *)
            echo "Unknown command: $1"
            usage
            exit 1
            ;;
    esac
}

main "$@"
