#!/bin/bash
# Test Docker build and run locally before Azure deployment

set -e

print_status() {
    echo -e "\033[0;32m[$(date +'%Y-%m-%d %H:%M:%S')]\033[0m $1"
}

print_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

cd "$(dirname "$0")/.."

# Check if .env exists
if [ ! -f .env ]; then
    print_error ".env file not found. Please create it from .env.example"
    exit 1
fi

print_status "Building Docker image..."
docker build -t stratos-fastapi:test .

print_status "Running container locally..."
docker run -d \
    --name stratos-test \
    -p 8000:8000 \
    --env-file .env \
    stratos-fastapi:test

print_status "Waiting for container to start..."
sleep 10

print_status "Testing health endpoint..."
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    print_status "Health check passed!"
    echo ""
    echo "API is running at:"
    echo "  - Health: http://localhost:8000/health"
    echo "  - Docs: http://localhost:8000/docs"
    echo "  - Agents: http://localhost:8000/api/v1/agents"
    echo ""
    echo "To view logs: docker logs stratos-test"
    echo "To stop: docker stop stratos-test && docker rm stratos-test"
else
    print_error "Health check failed!"
    echo "Container logs:"
    docker logs stratos-test
    docker stop stratos-test && docker rm stratos-test
    exit 1
fi