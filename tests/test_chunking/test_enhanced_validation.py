"""
Comprehensive validation tests for the enhanced chunking system.
"""

import unittest
from unittest.mock import patch, MagicMock
from langchain.docstore.document import Document

# Import from the source
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.processors.text_processor import TextProcessor
from src.processors.chunking import PythonChunker, CSharpChunker, FallbackChunker


class TestEnhancedChunkingValidation(unittest.TestCase):
    """Comprehensive validation tests for enhanced chunking."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.enhanced_processor = TextProcessor(
            chunk_size=1000,
            chunk_overlap=100,
            use_enhanced_chunking=True
        )
        
        self.traditional_processor = TextProcessor(
            chunk_size=1000,
            chunk_overlap=100,
            use_enhanced_chunking=False
        )
    
    def test_python_chunking_with_complex_code(self):
        """Test Python chunking with complex code structures."""
        complex_python_code = '''
"""Complex Python module for testing."""

import asyncio
import typing
from dataclasses import dataclass
from typing import Dict, List, Optional, Union
import contextlib

@dataclass
class UserData:
    """User data model."""
    name: str
    email: str
    age: Optional[int] = None
    
    def validate(self) -> bool:
        """Validate user data."""
        return bool(self.name and self.email)

class DatabaseManager:
    """Database management class."""
    
    def __init__(self, connection_string: str):
        """Initialize database manager."""
        self.connection_string = connection_string
        self._connection = None
    
    async def connect(self) -> None:
        """Establish database connection."""
        if not self._connection:
            self._connection = await self._create_connection()
    
    async def _create_connection(self):
        """Create database connection."""
        await asyncio.sleep(0.1)  # Simulate connection time
        return MagicMock()
    
    @contextlib.asynccontextmanager
    async def transaction(self):
        """Database transaction context manager."""
        try:
            await self.connect()
            yield self._connection
        except Exception as e:
            await self._rollback()
            raise
        else:
            await self._commit()
    
    async def _commit(self):
        """Commit transaction."""
        pass
    
    async def _rollback(self):
        """Rollback transaction.""" 
        pass

def utility_function(data: List[Dict]) -> Dict[str, int]:
    """Utility function for data processing."""
    result = {}
    for item in data:
        key = item.get("key", "unknown")
        value = item.get("value", 0)
        result[key] = result.get(key, 0) + value
    return result

# Global constants
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
'''
        
        doc = Document(
            page_content=complex_python_code,
            metadata={"file_path": "complex_example.py", "file_type": ".py", "source": "test"}
        )
        
        # Test enhanced chunking
        enhanced_chunks = self.enhanced_processor.process_documents([doc])
        
        # Validate results
        self.assertGreater(len(enhanced_chunks), 0)
        
        # Check that we have different chunk types
        chunk_types = {chunk.metadata.get("chunk_type") for chunk in enhanced_chunks}
        self.assertIn("import", chunk_types)
        self.assertIn("class", chunk_types)
        
        # Verify metadata completeness
        for chunk in enhanced_chunks:
            self.assertIn("language", chunk.metadata)
            self.assertEqual(chunk.metadata["language"], "python")
            self.assertIn("chunk_type", chunk.metadata)
            self.assertIn("contains_documentation", chunk.metadata)
    
    def test_csharp_chunking_with_complex_code(self):
        """Test C# chunking with complex code structures."""
        complex_csharp_code = '''
using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.DependencyInjection;

namespace ComplexExample.Services
{
    /// <summary>
    /// Service for managing complex business operations.
    /// Implements multiple interfaces and design patterns.
    /// </summary>
    public class ComplexBusinessService : IBusinessService, IDisposable
    {
        private readonly ILogger<ComplexBusinessService> _logger;
        private readonly IRepository<BusinessEntity> _repository;
        private readonly IEventPublisher _eventPublisher;
        private bool _disposed = false;
        
        /// <summary>
        /// Initializes a new instance of the ComplexBusinessService.
        /// </summary>
        /// <param name="logger">Logger instance</param>
        /// <param name="repository">Repository for business entities</param>
        /// <param name="eventPublisher">Event publisher for domain events</param>
        public ComplexBusinessService(
            ILogger<ComplexBusinessService> logger,
            IRepository<BusinessEntity> repository,
            IEventPublisher eventPublisher)
        {
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            _repository = repository ?? throw new ArgumentNullException(nameof(repository));
            _eventPublisher = eventPublisher ?? throw new ArgumentNullException(nameof(eventPublisher));
        }
        
        /// <summary>
        /// Processes a business operation asynchronously.
        /// </summary>
        /// <param name="request">The business operation request</param>
        /// <returns>The result of the operation</returns>
        /// <exception cref="BusinessException">Thrown when business rules are violated</exception>
        public async Task<BusinessResult> ProcessOperationAsync(BusinessRequest request)
        {
            ValidateRequest(request);
            
            try
            {
                _logger.LogInformation("Processing business operation for {EntityId}", request.EntityId);
                
                var entity = await _repository.GetByIdAsync(request.EntityId);
                if (entity == null)
                {
                    throw new BusinessException($"Entity {request.EntityId} not found");
                }
                
                var result = await ProcessEntityAsync(entity, request);
                
                await _eventPublisher.PublishAsync(new BusinessOperationCompletedEvent
                {
                    EntityId = entity.Id,
                    OperationType = request.OperationType,
                    Timestamp = DateTime.UtcNow
                });
                
                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error processing business operation for {EntityId}", request.EntityId);
                throw;
            }
        }
        
        /// <summary>
        /// Validates the business request.
        /// </summary>
        /// <param name="request">Request to validate</param>
        private void ValidateRequest(BusinessRequest request)
        {
            if (request == null)
                throw new ArgumentNullException(nameof(request));
            
            if (request.EntityId <= 0)
                throw new ArgumentException("EntityId must be positive", nameof(request));
        }
        
        /// <summary>
        /// Processes a business entity.
        /// </summary>
        /// <param name="entity">Entity to process</param>
        /// <param name="request">Processing request</param>
        /// <returns>Processing result</returns>
        private async Task<BusinessResult> ProcessEntityAsync(BusinessEntity entity, BusinessRequest request)
        {
            // Complex business logic implementation
            await Task.Delay(100); // Simulate processing time
            return new BusinessResult { Success = true, EntityId = entity.Id };
        }
        
        /// <summary>
        /// Disposes resources used by the service.
        /// </summary>
        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }
        
        /// <summary>
        /// Disposes resources used by the service.
        /// </summary>
        /// <param name="disposing">True if disposing managed resources</param>
        protected virtual void Dispose(bool disposing)
        {
            if (!_disposed && disposing)
            {
                // Dispose managed resources
                _disposed = true;
            }
        }
    }
    
    /// <summary>
    /// Business entity model.
    /// </summary>
    public class BusinessEntity
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public DateTime CreatedAt { get; set; }
    }
}
'''
        
        doc = Document(
            page_content=complex_csharp_code,
            metadata={"file_path": "ComplexBusinessService.cs", "file_type": ".cs", "source": "test"}
        )
        
        # Test enhanced chunking
        enhanced_chunks = self.enhanced_processor.process_documents([doc])
        
        # Validate results
        self.assertGreater(len(enhanced_chunks), 0)
        
        # Check that we have different chunk types
        chunk_types = {chunk.metadata.get("chunk_type") for chunk in enhanced_chunks}
        self.assertIn("using", chunk_types)
        self.assertIn("class", chunk_types)
        
        # Verify metadata completeness
        for chunk in enhanced_chunks:
            self.assertIn("language", chunk.metadata)
            self.assertEqual(chunk.metadata["language"], "csharp")
            self.assertIn("chunk_type", chunk.metadata)
            self.assertIn("contains_documentation", chunk.metadata)
    
    def test_empty_document_handling(self):
        """Test handling of empty documents."""
        empty_doc = Document(
            page_content="",
            metadata={"file_path": "empty.py", "file_type": ".py", "source": "test"}
        )
        
        # Should handle gracefully
        chunks = self.enhanced_processor.process_documents([empty_doc])
        self.assertEqual(len(chunks), 0)
    
    def test_malformed_code_fallback(self):
        """Test fallback behavior with malformed code."""
        malformed_python = '''
def incomplete_function(
    # Missing closing parenthesis and function body
    
class IncompleteClass
    # Missing colon and body
    
# This should fall back to traditional chunking
some_content = "This is still processable content"
more_content = "Even with syntax errors above"
'''
        
        doc = Document(
            page_content=malformed_python,
            metadata={"file_path": "malformed.py", "file_type": ".py", "source": "test"}
        )
        
        # Should still produce chunks via fallback
        chunks = self.enhanced_processor.process_documents([doc])
        self.assertGreater(len(chunks), 0)
        
        # Should have some content
        total_content = "".join(chunk.page_content for chunk in chunks)
        self.assertIn("some_content", total_content)
    
    def test_unsupported_file_type_fallback(self):
        """Test fallback to traditional chunking for unsupported file types."""
        go_code = '''
// Go code - not supported by enhanced chunking
package main

import "fmt"

func calculateSum(a, b int) int {
    return a + b
}

type Calculator struct {
    history []string
}

func (c *Calculator) Add(a, b int) int {
    result := a + b
    c.history = append(c.history, fmt.Sprintf("add: %d + %d = %d", a, b, result))
    return result
}

func main() {
    calc := &Calculator{}
    fmt.Println(calc.Add(5, 3))
}
'''
        
        doc = Document(
            page_content=go_code,
            metadata={"file_path": "script.go", "file_type": ".go", "source": "test"}
        )
        
        # Should use fallback chunker
        chunks = self.enhanced_processor.process_documents([doc])
        self.assertGreater(len(chunks), 0)
        
        # Should have traditional chunking metadata
        for chunk in chunks:
            # Should not have enhanced semantic metadata
            self.assertNotIn("symbol_name", chunk.metadata)
            # But should have basic metadata
            self.assertIn("chunk_index", chunk.metadata)
            self.assertIn("chunk_size", chunk.metadata)
    
    def test_chunking_mode_switching(self):
        """Test switching between enhanced and traditional chunking modes."""
        python_code = '''
def test_function():
    """A test function."""
    return "test"

class TestClass:
    def method(self):
        return "method"
'''
        
        doc = Document(
            page_content=python_code,
            metadata={"file_path": "test.py", "file_type": ".py", "source": "test"}
        )
        
        # Test enhanced chunking
        enhanced_chunks = self.enhanced_processor.process_documents([doc])
        enhanced_count = len(enhanced_chunks)
        
        # Switch to traditional chunking
        self.enhanced_processor.switch_chunking_mode(False)
        traditional_chunks = self.enhanced_processor.process_documents([doc])
        traditional_count = len(traditional_chunks)
        
        # Switch back to enhanced
        self.enhanced_processor.switch_chunking_mode(True)
        enhanced_again_chunks = self.enhanced_processor.process_documents([doc])
        enhanced_again_count = len(enhanced_again_chunks)
        
        # Verify that switching works
        self.assertNotEqual(enhanced_count, traditional_count)
        self.assertEqual(enhanced_count, enhanced_again_count)
    
    def test_chunk_statistics(self):
        """Test chunk statistics functionality."""
        python_code = '''
"""Module docstring."""

import os
import sys

def function1():
    """Function 1."""
    pass

def function2():
    """Function 2."""
    pass

class MyClass:
    """A test class."""
    
    def method1(self):
        """Method 1."""
        pass
    
    def method2(self):
        """Method 2."""
        pass
'''
        
        doc = Document(
            page_content=python_code,
            metadata={"file_path": "stats_test.py", "file_type": ".py", "source": "test"}
        )
        
        chunks = self.enhanced_processor.process_documents([doc])
        stats = self.enhanced_processor.get_chunk_stats(chunks)
        
        # Validate statistics
        self.assertIn("total_chunks", stats)
        self.assertIn("chunk_types", stats)
        self.assertIn("languages", stats)
        self.assertIn("has_documentation", stats)
        self.assertIn("symbol_count", stats)
        
        # Should have detected Python
        self.assertIn("python", stats["languages"])
        
        # Should have different chunk types
        self.assertGreater(len(stats["chunk_types"]), 1)
        
        # Should have detected documentation
        self.assertGreater(stats["has_documentation"], 0)
    
    def test_configuration_info(self):
        """Test chunking configuration information retrieval."""
        info = self.enhanced_processor.get_chunking_info()
        
        # Should have basic configuration
        self.assertIn("enhanced_chunking", info)
        self.assertIn("chunk_size", info)
        self.assertIn("chunk_overlap", info)
        
        # Should have enhanced chunking info
        if info["enhanced_chunking"]:
            self.assertIn("supported_extensions", info)
            self.assertIn("chunker_info", info)
            
            # Should support Python and C#
            self.assertIn(".py", info["supported_extensions"])
            self.assertIn(".cs", info["supported_extensions"])
    
    def test_large_file_chunking(self):
        """Test chunking of larger files."""
        # Create a larger Python file
        large_python_code = '''
"""Large Python module for testing."""

import os
import sys
import json
import asyncio
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

''' + '''
class TestClass{i}:
    """Test class {i}."""
    
    def __init__(self, value: int = {i}):
        """Initialize with value."""
        self.value = value
    
    def get_value(self) -> int:
        """Get the value."""
        return self.value
    
    def set_value(self, value: int) -> None:
        """Set the value."""
        self.value = value
    
    def calculate(self, other: int) -> int:
        """Calculate something."""
        return self.value + other

def utility_function_{i}(data: List[Dict]) -> Dict:
    """Utility function {i}."""
    result = {{}}
    for item in data:
        key = f"key_{i}_{{item.get('id', 0)}}"
        result[key] = item.get('value', 0) * {i}
    return result

'''.format(i=1) * 10  # Create 10 similar classes and functions
        
        doc = Document(
            page_content=large_python_code,
            metadata={"file_path": "large_test.py", "file_type": ".py", "source": "test"}
        )
        
        chunks = self.enhanced_processor.process_documents([doc])
        
        # Should create multiple chunks
        self.assertGreater(len(chunks), 5)
        
        # All chunks should have proper metadata
        for chunk in chunks:
            self.assertIn("language", chunk.metadata)
            self.assertIn("chunk_type", chunk.metadata)
            
        # Total content should be preserved
        total_original = len(doc.page_content.replace(" ", "").replace("\n", ""))
        total_chunked = len("".join(chunk.page_content for chunk in chunks).replace(" ", "").replace("\n", ""))
        
        # Should preserve most content (allowing for some formatting differences)
        self.assertGreater(total_chunked, total_original * 0.9)


if __name__ == '__main__':
    unittest.main()
