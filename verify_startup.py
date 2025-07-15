#!/usr/bin/env python3
"""
Startup verification script for Knowledge Base Agent
"""

import sys
import os
import time
import traceback
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
    all_dirs_exist = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✓ Directory exists: {dir_path}")
        else:
            print(f"✗ Directory missing: {dir_path}")
            all_dirs_exist = False
    
    return all_dirs_exist

def verify_dependencies():
    """Verify critical dependencies"""
    print("\n📦 Verifying dependencies...")
    
    dependencies = [
        'pydantic',
        'pydantic_settings',
        'fastapi',
        'uvicorn',
        'langchain',
        'chromadb',
        'requests'
    ]
    
    missing_deps = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✓ {dep} available")
        except ImportError as e:
            print(f"✗ {dep} missing: {e}")
            missing_deps.append(dep)
    
    return len(missing_deps) == 0

def verify_configuration():
    """Verify configuration"""
    print("\n⚙️ Verifying configuration...")
    
    try:
        from src.config.settings import settings
        print("✓ Settings loaded successfully")
        
        print(f"  - Environment: {settings.app_env}")
        print(f"  - API Host: {settings.api_host}:{settings.api_port}")
        print(f"  - LLM Provider: {settings.llm_provider}")
        print(f"  - LLM Model: {settings.llm_model}")
        print(f"  - Embedding Model: {settings.embedding_model}")
        
        # Test configuration validation
        from src.config.model_config import ModelConfiguration
        config_summary = ModelConfiguration.get_configuration_summary()
        
        print(f"  - Overall Config Status: {config_summary['overall_status']}")
        print(f"  - LLM Config Valid: {config_summary['llm']['is_valid']}")
        print(f"  - Embedding Config Valid: {config_summary['embedding']['is_valid']}")
        
        if config_summary['llm']['error_message']:
            print(f"  - LLM Error: {config_summary['llm']['error_message']}")
        
        if config_summary['embedding']['error_message']:
            print(f"  - Embedding Error: {config_summary['embedding']['error_message']}")
        
        return config_summary['overall_status'] == 'ready'
        
    except Exception as e:
        print(f"✗ Configuration verification failed: {e}")
        traceback.print_exc()
        return False

def verify_external_services():
    """Verify external service connectivity"""
    print("\n🌐 Verifying external services...")
    
    try:
        import requests
        from src.config.settings import settings
        
        # Test Chroma connection
        try:
            chroma_url = f"http://{settings.chroma_host}:{settings.chroma_port}/api/v1/heartbeat"
            response = requests.get(chroma_url, timeout=5)
            if response.status_code == 200:
                print("✓ Chroma service is accessible")
            else:
                print(f"⚠ Chroma service returned status {response.status_code}")
        except Exception as e:
            print(f"⚠ Chroma service not accessible: {e}")
        
        # Test Ollama connection if using ollama
        if settings.llm_provider == "ollama" or (settings.llm_api_base_url and "ollama" in settings.llm_api_base_url):
            try:
                ollama_url = f"{settings.llm_api_base_url}/models"
                response = requests.get(ollama_url, timeout=5)
                if response.status_code == 200:
                    print("✓ Ollama service is accessible")
                else:
                    print(f"⚠ Ollama service returned status {response.status_code}")
            except Exception as e:
                print(f"⚠ Ollama service not accessible: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ External service verification failed: {e}")
        return False

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
        
        print("Testing API models...")
        from src.api.models import QueryRequest, QueryResponse, HealthResponse
        print("✓ API models imported successfully")
        
        print("Testing logging utilities...")
        from src.utils.logging import setup_logging, get_logger
        print("✓ logging utilities imported successfully")
        
        print("Testing LLM factory...")
        from src.llm.llm_factory import LLMFactory
        print("✓ LLM factory imported successfully")
        
        print("Testing embedding factory...")
        from src.llm.embedding_factory import EmbeddingFactory
        print("✓ embedding factory imported successfully")
        
        print("Testing vector store...")
        from src.vectorstores.chroma_store import ChromaStore
        print("✓ vector store imported successfully")
        
        print("Testing API routes...")
        from src.api.routes import app
        print("✓ API routes imported successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        traceback.print_exc()
        return False

def wait_for_services():
    """Wait for external services to be ready"""
    print("\n⏳ Waiting for external services...")
    
    max_wait = 60  # Maximum wait time in seconds
    check_interval = 2  # Check every 2 seconds
    waited = 0
    
    while waited < max_wait:
        try:
            import requests
            from src.config.settings import settings
            
            services_ready = True
            
            # Check Chroma
            try:
                chroma_url = f"http://{settings.chroma_host}:{settings.chroma_port}/api/v1/heartbeat"
                response = requests.get(chroma_url, timeout=2)
                if response.status_code != 200:
                    services_ready = False
            except requests.exceptions.RequestException:
                services_ready = False
            
            # Check Ollama if needed
            if settings.llm_provider == "ollama" or (settings.llm_api_base_url and "ollama" in settings.llm_api_base_url):
                try:
                    ollama_url = f"{settings.llm_api_base_url}/models"
                    response = requests.get(ollama_url, timeout=2)
                    if response.status_code != 200:
                        services_ready = False
                except:
                    services_ready = False
            
            if services_ready:
                print("✓ All external services are ready")
                return True
            
            print(f"⏳ Waiting for services... ({waited}s/{max_wait}s)")
            time.sleep(check_interval)
            waited += check_interval
            
        except Exception as e:
            print(f"⚠ Service check failed: {e}")
            time.sleep(check_interval)
            waited += check_interval
    
    print("⚠ Timed out waiting for services, continuing anyway...")
    return False

def main():
    """Main verification function"""
    print("🚀 Knowledge Base Agent - Startup Verification")
    print("=" * 60)
    
    try:
        # Basic environment verification
        if not verify_environment():
            print("\n❌ Environment verification failed!")
            return 1
        
        # Dependency verification
        if not verify_dependencies():
            print("\n❌ Dependency verification failed!")
            return 1
        
        # Configuration verification
        config_ok = verify_configuration()
        if not config_ok:
            print("\n⚠ Configuration issues detected, but continuing...")
        
        # Import verification
        if not verify_imports():
            print("\n❌ Import verification failed!")
            return 1
        
        # Wait for external services
        wait_for_services()
        
        # Final service verification
        verify_external_services()
        
        print("\n✅ Verification completed! Application should start.")
        print("Note: Some warnings are acceptable and won't prevent startup.")
        return 0
        
    except Exception as e:
        print(f"\n💥 Unexpected error during verification: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
