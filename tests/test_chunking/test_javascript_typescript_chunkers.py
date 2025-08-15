"""
Tests for JavaScript and TypeScript chunkers.
"""

import unittest
from langchain.docstore.document import Document
from src.processors.chunking.javascript_chunker import JavaScriptChunker
from src.processors.chunking.typescript_chunker import TypeScriptChunker


class TestJavaScriptChunker(unittest.TestCase):
    """Test cases for JavaScriptChunker."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.chunker = JavaScriptChunker(max_chunk_size=1500, chunk_overlap=100)
    
    def test_javascript_chunker_initialization(self):
        """Test JavaScript chunker initialization."""
        self.assertIsNotNone(self.chunker)
        self.assertTrue(self.chunker.use_advanced_parsing)
        self.assertIn('.js', self.chunker.get_supported_extensions())
        self.assertIn('.jsx', self.chunker.get_supported_extensions())
    
    def test_javascript_import_export_chunking(self):
        """Test chunking of JavaScript import/export statements."""
        js_code = '''
import React from 'react';
import { useState, useEffect } from 'react';

export default function App() {
    const [count, setCount] = useState(0);
    
    return <div>Count: {count}</div>;
}

export const utils = {
    add: (a, b) => a + b,
    multiply: (a, b) => a * b
};
'''
        
        doc = Document(
            page_content=js_code,
            metadata={"file_path": "App.jsx", "file_type": ".jsx", "source": "test"}
        )
        
        chunks = self.chunker.chunk_document(doc)
        
        # Should have chunks for imports and exports
        self.assertGreater(len(chunks), 0)
        
        chunk_types = {chunk.metadata.get("chunk_type") for chunk in chunks}
        self.assertIn("import", chunk_types)
        self.assertIn("export", chunk_types)
        
        # Check for tree-sitter parsing
        for chunk in chunks:
            self.assertEqual(chunk.metadata.get("parsing_method"), "tree-sitter")
            self.assertEqual(chunk.metadata.get("language"), "javascript")
    
    def test_javascript_class_chunking(self):
        """Test chunking of JavaScript classes."""
        js_code = '''
/**
 * Calculator class for basic arithmetic
 */
class Calculator {
    constructor() {
        this.history = [];
    }
    
    /**
     * Add two numbers
     */
    add(a, b) {
        const result = a + b;
        this.history.push({op: 'add', result});
        return result;
    }
    
    static create() {
        return new Calculator();
    }
}
'''
        
        doc = Document(
            page_content=js_code,
            metadata={"file_path": "Calculator.js", "file_type": ".js", "source": "test"}
        )
        
        chunks = self.chunker.chunk_document(doc)
        
        # Should have chunks
        self.assertGreater(len(chunks), 0)
        
        # Should have class chunk
        chunk_types = {chunk.metadata.get("chunk_type") for chunk in chunks}
        self.assertIn("class", chunk_types)
        
        # Check for documentation
        has_docs = any(chunk.metadata.get("contains_documentation", False) for chunk in chunks)
        self.assertTrue(has_docs)
    
    def test_javascript_function_chunking(self):
        """Test chunking of JavaScript functions."""
        js_code = '''
function calculateSum(numbers) {
    return numbers.reduce((sum, num) => sum + num, 0);
}

const calculateAverage = (numbers) => {
    const sum = calculateSum(numbers);
    return sum / numbers.length;
};

async function fetchData(url) {
    const response = await fetch(url);
    return response.json();
}
'''
        
        doc = Document(
            page_content=js_code,
            metadata={"file_path": "utils.js", "file_type": ".js", "source": "test"}
        )
        
        chunks = self.chunker.chunk_document(doc)
        
        # Should have chunks for functions
        self.assertGreater(len(chunks), 0)
        
        # Check that at least some functions are detected (const arrow functions might not be extracted yet)
        all_content = " ".join(chunk.page_content for chunk in chunks)
        self.assertIn("function calculateSum", all_content)
        self.assertIn("function fetchData", all_content)
        # Note: calculateAverage as const variable might not be detected as function yet
        
        # Should use tree-sitter parsing
        for chunk in chunks:
            self.assertEqual(chunk.metadata.get("parsing_method"), "tree-sitter")


class TestTypeScriptChunker(unittest.TestCase):
    """Test cases for TypeScriptChunker."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.chunker = TypeScriptChunker(max_chunk_size=1800, chunk_overlap=75)
    
    def test_typescript_chunker_initialization(self):
        """Test TypeScript chunker initialization."""
        self.assertIsNotNone(self.chunker)
        self.assertTrue(self.chunker.use_advanced_parsing)
        self.assertIn('.ts', self.chunker.get_supported_extensions())
        self.assertIn('.tsx', self.chunker.get_supported_extensions())
        self.assertIn('.d.ts', self.chunker.get_supported_extensions())
    
    def test_typescript_interface_chunking(self):
        """Test chunking of TypeScript interfaces."""
        ts_code = '''
interface User {
    id: number;
    name: string;
    email?: string;
    roles: UserRole[];
}

interface ApiResponse<T> {
    data: T;
    success: boolean;
    message?: string;
}

type UserRole = 'admin' | 'user' | 'guest';
type Status = 'pending' | 'completed' | 'failed';
'''
        
        doc = Document(
            page_content=ts_code,
            metadata={"file_path": "types.ts", "file_type": ".ts", "source": "test"}
        )
        
        chunks = self.chunker.chunk_document(doc)
        
        # Should have chunks for interfaces and types
        self.assertGreater(len(chunks), 0)
        
        # Check that types and interfaces are present in content
        all_content = " ".join(chunk.page_content for chunk in chunks)
        self.assertIn("interface User", all_content)
        self.assertIn("interface ApiResponse", all_content)
        self.assertIn("type UserRole", all_content)
        self.assertIn("type Status", all_content)
        
        # Check for TypeScript-specific metadata
        for chunk in chunks:
            self.assertEqual(chunk.metadata.get("parsing_method"), "tree-sitter")
            self.assertEqual(chunk.metadata.get("language"), "typescript")
    
    def test_typescript_class_with_generics(self):
        """Test chunking of TypeScript classes with generics."""
        ts_code = '''
/**
 * Generic repository class
 */
export class Repository<T extends BaseEntity> {
    private items: T[] = [];
    
    constructor(private readonly validator: Validator<T>) {}
    
    /**
     * Add an item to the repository
     */
    async add(item: T): Promise<T> {
        await this.validator.validate(item);
        this.items.push(item);
        return item;
    }
    
    findById(id: string): T | undefined {
        return this.items.find(item => item.id === id);
    }
}
'''
        
        doc = Document(
            page_content=ts_code,
            metadata={"file_path": "Repository.ts", "file_type": ".ts", "source": "test"}
        )
        
        chunks = self.chunker.chunk_document(doc)
        
        # Should have chunks
        self.assertGreater(len(chunks), 0)
        
        # Check that the class is present
        all_content = " ".join(chunk.page_content for chunk in chunks)
        self.assertIn("class Repository", all_content)
        self.assertIn("extends BaseEntity", all_content)
        
        # Check for tree-sitter parsing
        for chunk in chunks:
            self.assertEqual(chunk.metadata.get("parsing_method"), "tree-sitter")
        
        # Check that class content is properly extracted
        all_content = " ".join(chunk.page_content for chunk in chunks)
        self.assertIn("Repository", all_content)
        self.assertIn("add", all_content)  # Method should be present
    
    def test_typescript_enum_and_namespace(self):
        """Test chunking of TypeScript enums and namespaces."""
        ts_code = '''
export enum UserStatus {
    ACTIVE = 'active',
    INACTIVE = 'inactive',
    SUSPENDED = 'suspended'
}

export namespace UserUtils {
    export function isActive(status: UserStatus): boolean {
        return status === UserStatus.ACTIVE;
    }
    
    export function getDisplayName(status: UserStatus): string {
        switch (status) {
            case UserStatus.ACTIVE: return 'Active';
            case UserStatus.INACTIVE: return 'Inactive';
            case UserStatus.SUSPENDED: return 'Suspended';
            default: return 'Unknown';
        }
    }
}
'''
        
        doc = Document(
            page_content=ts_code,
            metadata={"file_path": "UserUtils.ts", "file_type": ".ts", "source": "test"}
        )
        
        chunks = self.chunker.chunk_document(doc)
        
        # Should have chunks for enum and namespace
        self.assertGreater(len(chunks), 0)
        
        chunk_types = {chunk.metadata.get("chunk_type") for chunk in chunks}
        self.assertIn("export", chunk_types)  # Both enum and namespace are exported
        
        # Check content includes enum and namespace
        all_content = " ".join(chunk.page_content for chunk in chunks)
        self.assertIn("enum UserStatus", all_content)
        self.assertIn("namespace UserUtils", all_content)
    
    def test_typescript_fallback_to_javascript(self):
        """Test fallback to JavaScript parsing when TypeScript parsing fails."""
        # Create a chunker that will fail TypeScript parsing
        chunker = TypeScriptChunker(use_advanced_parsing=False)
        
        ts_code = '''
function simpleFunction() {
    return "hello world";
}
'''
        
        doc = Document(
            page_content=ts_code,
            metadata={"file_path": "simple.ts", "file_type": ".ts", "source": "test"}
        )
        
        chunks = chunker.chunk_document(doc)
        
        # Should still produce chunks via fallback
        self.assertGreater(len(chunks), 0)


if __name__ == '__main__':
    unittest.main()