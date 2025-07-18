#!/bin/bash

# Validation script for Chroma data persistence
# This script helps verify that the data persistence fix is working correctly

set -e

echo "🔍 Chroma Data Persistence Validation"
echo "====================================="

# Check if directories exist
echo "📁 Checking directories..."
if [ -d "./chroma_db" ]; then
    echo "✅ chroma_db directory exists"
else
    echo "❌ chroma_db directory missing"
    exit 1
fi

if [ -d "./logs" ]; then
    echo "✅ logs directory exists"
else
    echo "❌ logs directory missing"
    exit 1
fi

# Check directory permissions
echo ""
echo "🔒 Checking permissions..."
CHROMA_DB_PERM=$(stat -c "%a" ./chroma_db 2>/dev/null || stat -f "%A" ./chroma_db)
LOGS_PERM=$(stat -c "%a" ./logs 2>/dev/null || stat -f "%A" ./logs)

if [ "$CHROMA_DB_PERM" -ge "755" ]; then
    echo "✅ chroma_db permissions: $CHROMA_DB_PERM"
else
    echo "⚠️  chroma_db permissions: $CHROMA_DB_PERM (should be 755 or higher)"
fi

if [ "$LOGS_PERM" -ge "755" ]; then
    echo "✅ logs permissions: $LOGS_PERM"
else
    echo "⚠️  logs permissions: $LOGS_PERM (should be 755 or higher)"
fi

# Check Docker Compose configuration
echo ""
echo "🐳 Checking Docker Compose configuration..."
if command -v docker-compose > /dev/null 2>&1; then
    COMPOSE_CMD="docker-compose"
elif command -v docker > /dev/null 2>&1 && docker compose version > /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ Docker Compose not found"
    exit 1
fi

if $COMPOSE_CMD config &> /dev/null; then
    echo "✅ Docker Compose configuration is valid"
else
    echo "❌ Docker Compose configuration has errors"
    exit 1
fi

# Check if services are running
echo ""
echo "🚀 Checking running services..."
if $COMPOSE_CMD ps | grep -q "chroma.*Up" 2>/dev/null; then
    echo "✅ Chroma service is running"
else
    echo "⚠️  Chroma service is not running"
fi

if $COMPOSE_CMD ps | grep -q "knowledge-base-agent.*Up" 2>/dev/null; then
    echo "✅ Knowledge base agent service is running"
else
    echo "⚠️  Knowledge base agent service is not running"
fi

# Check if data is persisting (basic check)
echo ""
echo "💾 Checking data persistence..."
if [ -n "$(find ./chroma_db -name '*.sqlite' -o -name '*.db' -o -name '*.parquet' 2>/dev/null)" ]; then
    echo "✅ Chroma data files detected in chroma_db"
else
    echo "ℹ️  No data files found (this is normal for a fresh setup)"
fi

# Check API health
echo ""
echo "🏥 Checking API health..."
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is responding"
    # Try to get collection info
    if curl -s -f http://localhost:8000/collections > /dev/null 2>&1; then
        echo "✅ Collections endpoint is accessible"
    else
        echo "⚠️  Collections endpoint is not accessible"
    fi
else
    echo "⚠️  API is not responding (make sure services are running)"
fi

echo ""
echo "🎯 Summary:"
echo "- Run './setup_chroma_persistence.sh' if directories are missing"
echo "- Run '$COMPOSE_CMD up -d' to start services"
echo "- Check logs with '$COMPOSE_CMD logs chroma' or '$COMPOSE_CMD logs knowledge-base-agent'"
echo "- Data should persist across '$COMPOSE_CMD down' and '$COMPOSE_CMD up -d'"

echo ""
echo "✅ Validation complete!"
