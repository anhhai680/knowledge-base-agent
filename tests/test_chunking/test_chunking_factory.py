"""
Tests for the chunking factory.
"""

import unittest
from unittest.mock import patch, MagicMock
from langchain.docstore.document import Document

# Import from the source
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.processors.chunking import ChunkingFactory, FallbackChunker, PythonChunker, CSharpChunker


class TestChunkingFactory(unittest.TestCase):
    """Tests for ChunkingFactory class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = ChunkingFactory()
    
    def test_factory_initialization(self):
        """Test that factory initializes correctly."""
        self.assertIsNotNone(self.factory)
        self.assertIsInstance(self.factory._fallback_chunker, FallbackChunker)
    
    def test_register_chunker(self):
        """Test registering a chunker."""
        python_chunker = PythonChunker()
        self.factory.register_chunker(python_chunker)
        
        # Check that Python extensions are registered
        supported_extensions = self.factory.get_supported_extensions()
        self.assertIn('.py', supported_extensions)
    
    def test_get_chunker_python(self):
        """Test getting Python chunker."""
        python_chunker = PythonChunker()
        self.factory.register_chunker(python_chunker)
        
        # Test Python file
        chunker = self.factory.get_chunker('test.py')
        self.assertIsInstance(chunker, PythonChunker)
    
    def test_get_chunker_csharp(self):
        """Test getting C# chunker."""
        csharp_chunker = CSharpChunker()
        self.factory.register_chunker(csharp_chunker)
        
        # Test C# file
        chunker = self.factory.get_chunker('test.cs')
        self.assertIsInstance(chunker, CSharpChunker)
    
    def test_get_chunker_fallback(self):
        """Test getting fallback chunker for unsupported extensions."""
        # Test unsupported file
        chunker = self.factory.get_chunker('test.unknown')
        self.assertIsInstance(chunker, FallbackChunker)
    
    def test_chunk_documents_empty(self):
        """Test chunking empty document list."""
        result = self.factory.chunk_documents([])
        self.assertEqual(result, [])
    
    def test_chunk_documents_with_python(self):
        """Test chunking Python documents."""
        python_chunker = PythonChunker()
        self.factory.register_chunker(python_chunker)
        
        # Create test document
        python_code = '''
def hello_world():
    """A simple hello world function."""
    print("Hello, world!")

class TestClass:
    """A test class."""
    
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        return self.value
'''
        
        doc = Document(
            page_content=python_code,
            metadata={"file_path": "test.py", "file_type": ".py", "source": "test"}
        )
        
        # Test chunking
        chunks = self.factory.chunk_documents([doc])
        
        # Should create multiple chunks for different elements
        self.assertGreater(len(chunks), 0)
        
        # Check that chunks have enhanced metadata
        for chunk in chunks:
            self.assertIn("chunk_type", chunk.metadata)
            self.assertIn("language", chunk.metadata)
            self.assertEqual(chunk.metadata["language"], "python")
    
    def test_get_chunker_info(self):
        """Test getting chunker information."""
        python_chunker = PythonChunker()
        csharp_chunker = CSharpChunker()
        
        self.factory.register_chunker(python_chunker)
        self.factory.register_chunker(csharp_chunker)
        
        info = self.factory.get_chunker_info()
        
        self.assertIn("PythonChunker", info)
        self.assertIn("CSharpChunker", info)
        self.assertIn("FallbackChunker", info)
        
        # Check that Python extensions are listed
        self.assertIn('.py', info["PythonChunker"])
        self.assertIn('.cs', info["CSharpChunker"])


if __name__ == '__main__':
    unittest.main()
