#!/usr/bin/env python3
"""
Startup verification script for Knowledge Base Agent
"""

import sys
import os
sys.path.insert(0, '/app' if '/app' in sys.path else '.')

def verify_environment():
    """Verify environment and dependencies"""
    print("🔍 Verifying environment...")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check working directory
    print(f"Working directory: {os.getcwd()}")
    
    # Check if required directories exist
    required_dirs = ['src', 'src/config', 'src/api', 'src/utils', 'src/llm', 'src/vectorstores', 'src/loaders', 'src/processors', 'src/agents']
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✓ Directory exists: {dir_path}")
        else:
            print(f"✗ Directory missing: {dir_path}")
    
def verify_dependencies():
    """Verify critical dependencies"""
    print("\n📦 Verifying dependencies...")
    
    dependencies = [
        'pydantic',
        'pydantic_settings',
        'fastapi',
        'uvicorn',
        'langchain',
        'chromadb'
    ]
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✓ {dep} available")
        except ImportError as e:
            print(f"✗ {dep} missing: {e}")

def verify_imports():
    """Verify application imports"""
    print("\n🔧 Verifying application imports...")
    
    try:
        print("Testing pydantic_settings...")
        from pydantic_settings import BaseSettings
        print("✓ pydantic_settings imported successfully")
        
        print("Testing settings module...")
        from src.config.settings import settings
        print("✓ settings module imported successfully")
        print(f"  - Environment: {settings.app_env}")
        print(f"  - API Host: {settings.api_host}:{settings.api_port}")
        
        print("Testing API models...")
        from src.api.models import QueryRequest, QueryResponse, HealthResponse
        print("✓ API models imported successfully")
        
        print("Testing logging utilities...")
        from src.utils.logging import setup_logging, get_logger
        print("✓ logging utilities imported successfully")
        
        print("Testing API routes...")
        from src.api.routes import app
        print("✓ API routes imported successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main verification function"""
    print("🚀 Knowledge Base Agent - Startup Verification")
    print("=" * 50)
    
    verify_environment()
    verify_dependencies()
    
    if verify_imports():
        print("\n✅ All verifications passed! Application should start successfully.")
        return 0
    else:
        print("\n❌ Verification failed! Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
