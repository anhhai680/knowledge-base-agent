#!/bin/bash

# Fix dependencies script for Knowledge Base Agent
echo "🔧 Fixing LangChain dependencies and compatibility issues..."

# Stop existing containers
echo "📦 Stopping existing containers..."
docker-compose down

# Remove old images to force rebuild
echo "🗑️  Removing old images..."
docker rmi $(docker images -q knowledge-base-agent*) 2>/dev/null || true

# Rebuild containers with new dependencies
echo "🔨 Rebuilding containers..."
docker-compose build --no-cache

# Start containers
echo "🚀 Starting containers..."
docker-compose up -d

# Check status
echo "📊 Container status:"
docker-compose ps

echo "✅ Dependencies updated! Check the logs with: docker-compose logs -f knowledge-base-agent"
