"""
Performance benchmark tests for tree-sitter parsers.
"""

import time
import unittest
from langchain.docstore.document import Document
from src.processors.chunking.csharp_chunker import CSharpChunker
from src.processors.chunking.javascript_chunker import JavaScriptChunker
from src.processors.chunking.typescript_chunker import TypeScriptChunker


class TestParserPerformance(unittest.TestCase):
    """Performance benchmark tests for tree-sitter parsers."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_sizes = [
            ("small", 500),   # ~500 chars
            ("medium", 2000), # ~2KB
            ("large", 10000)  # ~10KB
        ]
    
    def _generate_csharp_code(self, size_chars: int) -> str:
        """Generate C# code of approximately the specified size."""
        base_code = '''
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace TestNamespace
{
    /// <summary>
    /// Test class for performance benchmarking
    /// </summary>
    public class TestClass
    {
        private readonly string _name;
        
        /// <summary>
        /// Constructor
        /// </summary>
        public TestClass(string name)
        {
            _name = name;
        }
        
        /// <summary>
        /// Test method
        /// </summary>
        public async Task<string> ProcessAsync(string input)
        {
            await Task.Delay(10);
            return $"Processed: {input}";
        }
        
        public string GetName() => _name;
    }
}
'''
        
        # Repeat the class definition to reach desired size
        repetitions = max(1, size_chars // len(base_code))
        code = ""
        for i in range(repetitions):
            code += base_code.replace("TestClass", f"TestClass{i}")
        
        return code[:size_chars] if len(code) > size_chars else code
    
    def _generate_javascript_code(self, size_chars: int) -> str:
        """Generate JavaScript code of approximately the specified size."""
        base_code = '''
import React, { useState, useEffect } from 'react';

/**
 * Test component for performance benchmarking
 */
export default function TestComponent() {
    const [count, setCount] = useState(0);
    const [data, setData] = useState(null);
    
    useEffect(() => {
        fetchData();
    }, []);
    
    /**
     * Fetch data from API
     */
    const fetchData = async () => {
        try {
            const response = await fetch('/api/data');
            const result = await response.json();
            setData(result);
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    };
    
    const handleIncrement = () => {
        setCount(prevCount => prevCount + 1);
    };
    
    return (
        <div>
            <h1>Count: {count}</h1>
            <button onClick={handleIncrement}>Increment</button>
            {data && <pre>{JSON.stringify(data, null, 2)}</pre>}
        </div>
    );
}
'''
        
        # Repeat to reach desired size
        repetitions = max(1, size_chars // len(base_code))
        code = ""
        for i in range(repetitions):
            code += base_code.replace("TestComponent", f"TestComponent{i}")
        
        return code[:size_chars] if len(code) > size_chars else code
    
    def _generate_typescript_code(self, size_chars: int) -> str:
        """Generate TypeScript code of approximately the specified size."""
        base_code = '''
interface User {
    id: number;
    name: string;
    email?: string;
}

interface ApiResponse<T> {
    data: T;
    success: boolean;
    message?: string;
}

/**
 * Generic service class for API operations
 */
export class ApiService<T> {
    private baseUrl: string;
    
    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }
    
    /**
     * Fetch data from the API
     */
    async get<U = T>(endpoint: string): Promise<ApiResponse<U>> {
        try {
            const response = await fetch(`${this.baseUrl}/${endpoint}`);
            const data = await response.json();
            return { data, success: true };
        } catch (error) {
            return { 
                data: null as any, 
                success: false, 
                message: error.message 
            };
        }
    }
    
    /**
     * Post data to the API
     */
    async post<U = T>(endpoint: string, payload: Partial<T>): Promise<ApiResponse<U>> {
        try {
            const response = await fetch(`${this.baseUrl}/${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            return { data, success: true };
        } catch (error) {
            return { 
                data: null as any, 
                success: false, 
                message: error.message 
            };
        }
    }
}

export enum ResponseStatus {
    SUCCESS = 'success',
    ERROR = 'error',
    PENDING = 'pending'
}
'''
        
        # Repeat to reach desired size
        repetitions = max(1, size_chars // len(base_code))
        code = ""
        for i in range(repetitions):
            code += base_code.replace("ApiService", f"ApiService{i}")
        
        return code[:size_chars] if len(code) > size_chars else code
    
    def test_csharp_parser_performance(self):
        """Benchmark C# parser performance."""
        chunker = CSharpChunker(use_advanced_parsing=True)
        
        print(f"\n=== C# Parser Performance ===")
        
        for size_name, size_chars in self.sample_sizes:
            code = self._generate_csharp_code(size_chars)
            doc = Document(
                page_content=code,
                metadata={"file_path": f"test_{size_name}.cs", "file_type": ".cs", "source": "benchmark"}
            )
            
            # Warm up
            chunker.chunk_document(doc)
            
            # Benchmark
            start_time = time.time()
            chunks = chunker.chunk_document(doc)
            end_time = time.time()
            
            parse_time_ms = (end_time - start_time) * 1000
            
            print(f"  {size_name.capitalize()} ({size_chars:,} chars): {parse_time_ms:.2f}ms, {len(chunks)} chunks")
            
            # Performance assertions
            self.assertLess(parse_time_ms, 200, f"C# parsing too slow for {size_name} file")
            self.assertGreater(len(chunks), 0, f"No chunks produced for {size_name} file")
    
    def test_javascript_parser_performance(self):
        """Benchmark JavaScript parser performance."""
        chunker = JavaScriptChunker(use_advanced_parsing=True)
        
        print(f"\n=== JavaScript Parser Performance ===")
        
        for size_name, size_chars in self.sample_sizes:
            code = self._generate_javascript_code(size_chars)
            doc = Document(
                page_content=code,
                metadata={"file_path": f"test_{size_name}.js", "file_type": ".js", "source": "benchmark"}
            )
            
            # Warm up
            chunker.chunk_document(doc)
            
            # Benchmark
            start_time = time.time()
            chunks = chunker.chunk_document(doc)
            end_time = time.time()
            
            parse_time_ms = (end_time - start_time) * 1000
            
            print(f"  {size_name.capitalize()} ({size_chars:,} chars): {parse_time_ms:.2f}ms, {len(chunks)} chunks")
            
            # Performance assertions
            self.assertLess(parse_time_ms, 200, f"JavaScript parsing too slow for {size_name} file")
            self.assertGreater(len(chunks), 0, f"No chunks produced for {size_name} file")
    
    def test_typescript_parser_performance(self):
        """Benchmark TypeScript parser performance."""
        chunker = TypeScriptChunker(use_advanced_parsing=True)
        
        print(f"\n=== TypeScript Parser Performance ===")
        
        for size_name, size_chars in self.sample_sizes:
            code = self._generate_typescript_code(size_chars)
            doc = Document(
                page_content=code,
                metadata={"file_path": f"test_{size_name}.ts", "file_type": ".ts", "source": "benchmark"}
            )
            
            # Warm up
            chunker.chunk_document(doc)
            
            # Benchmark
            start_time = time.time()
            chunks = chunker.chunk_document(doc)
            end_time = time.time()
            
            parse_time_ms = (end_time - start_time) * 1000
            
            print(f"  {size_name.capitalize()} ({size_chars:,} chars): {parse_time_ms:.2f}ms, {len(chunks)} chunks")
            
            # Performance assertions
            self.assertLess(parse_time_ms, 200, f"TypeScript parsing too slow for {size_name} file")
            self.assertGreater(len(chunks), 0, f"No chunks produced for {size_name} file")
    
    def test_memory_usage_reasonable(self):
        """Test that memory usage is reasonable for large files."""
        import psutil
        import os
        
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Parse a large file
        chunker = TypeScriptChunker(use_advanced_parsing=True)
        large_code = self._generate_typescript_code(50000)  # ~50KB
        doc = Document(
            page_content=large_code,
            metadata={"file_path": "large_test.ts", "file_type": ".ts", "source": "benchmark"}
        )
        
        chunks = chunker.chunk_document(doc)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"\n=== Memory Usage Test ===")
        print(f"  Initial memory: {initial_memory:.1f} MB")
        print(f"  Final memory: {final_memory:.1f} MB")
        print(f"  Memory increase: {memory_increase:.1f} MB")
        print(f"  Chunks produced: {len(chunks)}")
        
        # Memory should not increase by more than 50MB for a 50KB file
        self.assertLess(memory_increase, 50, "Memory usage too high")
        self.assertGreater(len(chunks), 0, "No chunks produced")


if __name__ == '__main__':
    # Run with verbose output to see performance numbers
    unittest.main(verbosity=2)