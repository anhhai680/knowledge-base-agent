#!/bin/bash

# Knowledge Base Agent Setup Script

echo "🚀 Setting up Knowledge Base Agent..."

# Check if Python 3.11+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if [[ "$(printf '%s\n' "3.11" "$python_version" | sort -V | head -n1)" != "3.11" ]]; then
    echo "⚠️  Python 3.11+ is recommended. Current version: $python_version"
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📄 Creating .env file from template..."
    cp .env.example .env
    echo "✏️  Please edit .env file with your API keys:"
    echo "   - OPENAI_API_KEY or GEMINI_API_KEY (at least one required)"
    echo "   - GITHUB_TOKEN (required for private repositories)"
fi

# Test API connections
echo "🧪 Testing API connections..."
python3 test_apis.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys if needed"
echo "2. Run: source venv/bin/activate"
echo "3. For Docker: docker-compose up --build"
echo "4. For local: python main.py"
echo ""
echo "Or use Docker:"
echo "1. Edit .env file with your API keys"
echo "2. Run: docker-compose up -d"
echo ""
echo "📚 Visit http://localhost:8000/docs for API documentation"
echo "🎨 Visit http://localhost:3000 for the web interface"
