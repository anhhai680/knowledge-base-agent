#!/usr/bin/env python3
"""
Test script to validate the indexing fixes
"""

import sys
import asyncio
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.api.models import IndexRequest, IndexResponse, RepositoryInfo
from src.loaders.github_loader import GitHubLoader
from src.processors.text_processor import TextProcessor

def test_models():
    """Test that the models are properly defined"""
    print("Testing model definitions...")
    
    # Test IndexRequest
    request = IndexRequest(
        repository_urls=["https://github.com/test/repo"],
        branch="main",
        file_patterns=["*.py", "*.md"]
    )
    print(f"✓ IndexRequest created: {request}")
    
    # Test IndexResponse
    response = IndexResponse(
        message="Test message",
        status="indexing_started",
        repositories_processed=0,
        documents_indexed=0,
        task_id="test-123"
    )
    print(f"✓ IndexResponse created: {response}")
    
    # Test RepositoryInfo
    repo_info = RepositoryInfo(
        id="test-repo",
        url="https://github.com/test/repo",
        name="test-repo",
        description="Test repository",
        branch="main",
        status="indexed",
        documents_count=10,
        last_indexed="2025-01-01T00:00:00Z"
    )
    print(f"✓ RepositoryInfo created: {repo_info}")

def test_github_loader():
    """Test that GitHubLoader supports file_patterns"""
    print("\nTesting GitHubLoader...")
    
    loader = GitHubLoader()
    
    # Check if the method signature is correct
    import inspect
    sig = inspect.signature(loader.load_repository)
    params = list(sig.parameters.keys())
    
    expected_params = ["repo_url", "branch", "file_patterns"]
    for param in expected_params:
        if param in params:
            print(f"✓ GitHubLoader.load_repository has parameter: {param}")
        else:
            print(f"✗ GitHubLoader.load_repository missing parameter: {param}")
            return False
    
    return True

def test_text_processor():
    """Test that TextProcessor has the correct methods"""
    print("\nTesting TextProcessor...")
    
    processor = TextProcessor()
    
    # Check if process_documents method exists
    if hasattr(processor, 'process_documents'):
        print("✓ TextProcessor has process_documents method")
    else:
        print("✗ TextProcessor missing process_documents method")
        return False
    
    return True

def main():
    """Run all tests"""
    print("=" * 50)
    print("Testing indexing fixes...")
    print("=" * 50)
    
    try:
        test_models()
        
        if test_github_loader():
            print("\n✓ GitHubLoader tests passed")
        else:
            print("\n✗ GitHubLoader tests failed")
            return False
            
        if test_text_processor():
            print("✓ TextProcessor tests passed")
        else:
            print("✗ TextProcessor tests failed")
            return False
        
        print("\n" + "=" * 50)
        print("✓ All tests passed! The indexing fixes look good.")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n✗ Tests failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
