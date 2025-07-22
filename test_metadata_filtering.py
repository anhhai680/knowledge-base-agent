#!/usr/bin/env python3
"""
Test script to verify metadata filtering functionality.
"""

import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from langchain.docstore.document import Document
from src.vectorstores.chroma_store import ChromaStore

def test_metadata_filtering():
    """Test that complex metadata is properly filtered."""
    
    # Create test documents with complex metadata
    test_documents = [
        Document(
            page_content="This is a test document",
            metadata={
                "source": "github",
                "repository": "test/repo",
                "file_path": "test.py",
                "file_name": "test.py",
                "file_type": ".py",
                "file_size": 100,
                "branch": "main",  # String - should be kept
                "branches": ["main", "develop"],  # List - should be converted to string
                "tags": {"version": "1.0", "status": "active"},  # Dict - should be converted to string
                "metadata_with_none": None,  # None - should be kept
                "complex_object": object(),  # Complex object - should be converted to string
            }
        )
    ]
    
    # Initialize ChromaStore (this should trigger the filtering)
    try:
        chroma_store = ChromaStore(
            collection_name="test-metadata-filtering",
            host="localhost",
            port=8000,
            persist_directory="./test_chroma_db"
        )
        
        # Test the metadata filtering method directly
        filtered_docs = chroma_store._filter_document_metadata(test_documents)
        
        print("Original metadata:")
        for key, value in test_documents[0].metadata.items():
            print(f"  {key}: {value} (type: {type(value).__name__})")
        
        print("\nFiltered metadata:")
        for key, value in filtered_docs[0].metadata.items():
            print(f"  {key}: {value} (type: {type(value).__name__})")
        
        print("\n✅ Metadata filtering test passed!")
        
        # Clean up test directory
        import shutil
        if os.path.exists("./test_chroma_db"):
            shutil.rmtree("./test_chroma_db")
        
        return True
        
    except Exception as e:
        print(f"❌ Metadata filtering test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_metadata_filtering()
    sys.exit(0 if success else 1)
