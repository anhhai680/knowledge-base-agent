#!/bin/bash

# Script to set up proper Chroma data persistence
# This ensures that Chroma data is properly persisted across container restarts

set -e

echo "Setting up Chroma persistence..."

# Create necessary directories
mkdir -p ./chroma_db
mkdir -p ./logs

# Set proper permissions (Docker typically runs as root, but we want to be safe)
echo "Setting proper permissions..."
chmod 755 ./chroma_db
chmod 755 ./logs

# Create a .gitkeep file to ensure directories are tracked but not their contents
echo "Creating .gitkeep files..."
touch ./chroma_db/.gitkeep
touch ./logs/.gitkeep

echo "✅ Chroma persistence setup complete!"
echo ""
echo "📋 Directory structure:"
echo "  - ./chroma_db/   - Chroma database storage (shared between HTTP service and persistent client)"
echo "  - ./logs/        - Application logs"
echo ""
echo "🔧 To start the services:"
if command -v docker-compose > /dev/null 2>&1; then
    echo "  docker-compose up -d"
elif command -v docker > /dev/null 2>&1 && docker compose version > /dev/null 2>&1; then
    echo "  docker compose up -d"
else
    echo "  Install Docker Compose first"
fi
echo ""
echo "🧹 To clean up data (⚠️  WARNING: This will delete all data!):"
if command -v docker-compose > /dev/null 2>&1; then
    echo "  docker-compose down -v"
elif command -v docker > /dev/null 2>&1 && docker compose version > /dev/null 2>&1; then
    echo "  docker compose down -v"
else
    echo "  Install Docker Compose first"
fi
echo "  rm -rf ./chroma_db/* ./logs/*"
