#!/bin/bash

# Radio Russell - Production Deployment Script
# This script deploys the application with PostgreSQL and nginx

set -e  # Exit on any error

echo "🚀 Starting Radio Russell Production Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    error "Docker is not installed. Please install Docker first."
fi

if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose is not installed. Please install Docker Compose first."
fi

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

log "Project root: $PROJECT_ROOT"

# Stop any running containers
log "Stopping existing containers..."
docker-compose --profile prod down --remove-orphans || true

# Remove old images (optional - uncomment if you want to rebuild from scratch)
# log "Removing old images..."
# docker-compose --profile prod down --rmi all || true

# Build the application
log "Building application images..."
docker-compose --profile prod build --no-cache

# Start PostgreSQL first and wait for it to be ready
log "Starting PostgreSQL database..."
docker-compose --profile prod up -d postgres

# Wait for PostgreSQL to be ready
log "Waiting for PostgreSQL to be ready..."
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
    if docker-compose --profile prod exec -T postgres pg_isready -U radio_user -d radio_db; then
        log "PostgreSQL is ready!"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        error "PostgreSQL failed to start within timeout"
    fi
    
    echo "Attempt $attempt/$max_attempts: PostgreSQL not ready yet, waiting..."
    sleep 2
    ((attempt++))
done

# Start the application
log "Starting Radio Russell application..."
docker-compose --profile prod up -d radio-russell-prod

# Wait for the application to be ready
log "Waiting for application to be ready..."
max_attempts=30
attempt=1
while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:8000/health &> /dev/null; then
        log "Application is ready!"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        # Show logs for debugging
        log "Application health check failed. Showing recent logs:"
        docker logs radio-russell-prod --tail=20
        error "Application failed to start within timeout"
    fi
    
    echo "Attempt $attempt/$max_attempts: Application not ready yet, waiting..."
    sleep 3
    ((attempt++))
done

# Start nginx
log "Starting nginx reverse proxy..."
docker-compose --profile prod up -d nginx

# Wait for nginx to be ready
log "Waiting for nginx to be ready..."
max_attempts=15
attempt=1
while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost/health &> /dev/null; then
        log "Nginx is ready!"
        break
    fi
    
    if [ $attempt -eq $max_attempts ]; then
        error "Nginx failed to start within timeout"
    fi
    
    echo "Attempt $attempt/$max_attempts: Nginx not ready yet, waiting..."
    sleep 2
    ((attempt++))
done

# Show running containers
log "Checking running containers..."
docker-compose --profile prod ps

# Show logs
log "Recent logs from all services:"
docker-compose --profile prod logs --tail=20

echo ""
log "🎉 Production deployment completed successfully!"
echo ""
echo -e "${BLUE}Services are running:${NC}"
echo -e "${BLUE}• Application: http://localhost (via nginx)${NC}"
echo -e "${BLUE}• Direct access: http://localhost:8000${NC}"
echo -e "${BLUE}• Health check: http://localhost/health${NC}"
echo -e "${BLUE}• Database: PostgreSQL running on internal network${NC}"
echo ""
echo -e "${YELLOW}To view logs: docker-compose --profile prod logs -f${NC}"
echo -e "${YELLOW}To stop: docker-compose --profile prod down${NC}"
echo -e "${YELLOW}To restart: $0${NC}"
echo ""

# Optional: Run basic health checks
log "Running basic health checks..."

if curl -s http://localhost/health | jq -r '.status' | grep -q "healthy"; then
    log "✅ Health check passed"
else
    warn "⚠️  Health check returned unexpected result"
fi

if curl -s http://localhost/api/users | jq -r '.users' &> /dev/null; then
    log "✅ API endpoints accessible"
else
    warn "⚠️  API endpoints may not be working correctly"
fi

log "Deployment script completed!"
