#!/bin/bash
set -e

echo "🚀 Starting Knowledge Base Agent..."
echo "Working directory: $(pwd)"
echo "Python version: $(python --version)"

# Run startup verification
echo "📋 Running startup verification..."
python verify_startup.py
VERIFY_EXIT_CODE=$?

if [ $VERIFY_EXIT_CODE -eq 0 ]; then
    echo "✅ Verification passed, starting application..."
    exec python main.py
else
    echo "❌ Verification failed with exit code $VERIFY_EXIT_CODE"
    echo "Please check the logs above for details."
    exit 1
fi
