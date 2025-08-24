# TreeSitter Chunker Integration Guide

## Overview

This document describes the integration of the provided `CodeParser.py` and `Chunker.py` files into the Knowledge Base Agent's enhanced chunking system. The integration provides improved semantic chunking capabilities using Tree-sitter for accurate multi-language code analysis.

## Architecture Summary

### Current System Before Integration
The Knowledge Base Agent used a sophisticated chunking system with:
- `ChunkingFactory`: Factory pattern for managing different chunkers
- `BaseChunker`: Abstract base class defining chunking interface  
- Language-specific chunkers: `PythonChunker`, `JavaScriptChunker`, etc.
- AST-based parsing for semantic understanding

### Enhanced System After Integration
The new implementation adds:
- `TreeSitterParser`: Multi-language parser using Tree-sitter grammars
- `TreeSitterChunker`: Enhanced chunker using Tree-sitter for semantic boundaries
- Fallback mechanisms for unsupported languages
- Improved semantic metadata extraction

## Implementation Details

### 1. TreeSitterParser (`src/processors/chunking/parsers/tree_sitter_parser.py`)

**Based on:** Provided `CodeParser.py`  
**Enhancements:**
- Integrated with existing logging system
- Added comprehensive error handling
- Enhanced symbol information extraction
- Support for semantic boundary detection
- Caching and performance optimizations

**Key Features:**
```python
# Initialize parser for specific languages
parser = TreeSitterParser(['py', 'js', 'ts'])

# Parse code and get semantic boundaries
boundaries = parser.get_semantic_boundaries(code, 'py')

# Extract symbol information  
symbols = parser.get_symbol_information(code, 'py')

# Check parser status
status = parser.get_language_status()
```

### 2. TreeSitterChunker (`src/processors/chunking/tree_sitter_chunker.py`)

**Based on:** Provided `Chunker.py` concepts  
**Enhancements:**
- Implements `BaseChunker` interface for seamless integration
- Token-aware chunking with configurable limits
- Enhanced metadata generation
- Graceful fallback to line-based chunking
- Support for overlap and size configuration

**Key Features:**
```python
# Initialize chunker
chunker = TreeSitterChunker(max_chunk_size=1500, chunk_overlap=100)

# Check supported extensions
extensions = chunker.get_supported_extensions()

# Chunk a document
chunks = chunker.chunk_document(document)

# Get parser status
status = chunker.get_parser_status()
```

### 3. Integration with TextProcessor

The `TextProcessor` class has been enhanced to register the `TreeSitterChunker`:

```python
# TreeSitter chunker is registered with highest priority
tree_sitter_chunker = TreeSitterChunker(
    max_chunk_size=self.chunk_size,
    chunk_overlap=self.chunk_overlap
)
self.chunking_factory.register_chunker(tree_sitter_chunker)
```

## Language Support

### Supported Languages (via Tree-sitter)
- **Python** (`.py`): Classes, functions, imports, docstrings
- **JavaScript** (`.js`, `.jsx`): Functions, classes, imports, exports
- **TypeScript** (`.ts`, `.tsx`): Interfaces, types, enums + JavaScript features
- **CSS** (`.css`): Rules, at-rules, media queries
- **PHP** (`.php`): Classes, methods, functions, namespaces
- **C#** (`.cs`): Classes, methods, properties, namespaces

### Tree-sitter Grammar Installation
Grammars are automatically downloaded and compiled:
```bash
# Automatic installation to ~/.code_parser_cache/
git clone https://github.com/tree-sitter/tree-sitter-python
git clone https://github.com/tree-sitter/tree-sitter-javascript
# ... other languages
```

## Usage Examples

### Basic Document Chunking
```python
from langchain.docstore.document import Document
from src.processors.chunking import TreeSitterChunker

# Create chunker
chunker = TreeSitterChunker(max_chunk_size=1000)

# Create document
doc = Document(
    page_content=python_code,
    metadata={'file_path': 'example.py', 'source': 'github'}
)

# Chunk document
chunks = chunker.chunk_document(doc)

# Analyze results
for chunk in chunks:
    print(f"Chunk: {len(chunk.page_content)} chars")
    print(f"Type: {chunk.metadata['chunk_type']}")
    print(f"Symbol: {chunk.metadata.get('symbol_name', 'N/A')}")
    print(f"Method: {chunk.metadata['chunking_method']}")
```

### Using with ChunkingFactory
```python
from src.processors.chunking import ChunkingFactory, TreeSitterChunker

# Initialize factory and register chunker
factory = ChunkingFactory()
tree_sitter_chunker = TreeSitterChunker()
factory.register_chunker(tree_sitter_chunker)

# Process multiple documents
documents = [doc1, doc2, doc3]  # List of Document objects
chunked_docs = factory.chunk_documents(documents)
```

### Enhanced TextProcessor Integration
```python
from src.processors.text_processor import TextProcessor

# TextProcessor automatically uses TreeSitterChunker when available
processor = TextProcessor(use_enhanced_chunking=True)
chunked_docs = processor.process_documents(documents)

# Get chunking statistics
stats = processor.get_chunk_stats(chunked_docs)
print(f"Chunking method: {stats.get('enhanced_chunking')}")
```

## Configuration

### Chunker Configuration
```python
# Basic configuration
chunker = TreeSitterChunker(
    max_chunk_size=1500,    # Maximum chunk size in characters
    chunk_overlap=100       # Overlap between chunks
)

# Advanced configuration
config = {
    'max_chunk_size': 2000,
    'chunk_overlap': 150,
    'encoding_name': 'gpt-4',
    'reinitialize_parser': True
}
chunker.configure(config)
```

### TextProcessor Configuration
```python
processor = TextProcessor(
    chunk_size=1500,
    chunk_overlap=100,
    use_enhanced_chunking=True
)
```

## Error Handling and Fallbacks

### Parser Initialization Failures
- Tree-sitter compilation errors → Log warning, continue with other languages
- Network issues during grammar download → Retry mechanism, graceful degradation
- Missing system dependencies → Fallback to existing chunkers

### Runtime Fallbacks
```python
# TreeSitterChunker automatically falls back when:
# 1. Language not supported by tree-sitter
# 2. Parse errors occur
# 3. Tree-sitter parser not initialized

# Check parser availability
if chunker._can_use_tree_sitter('py'):
    # Use tree-sitter chunking
    pass
else:
    # Use fallback line-based chunking
    pass
```

### Graceful Degradation
- Unsupported file extensions → Use fallback chunker
- Parse failures → Use line-based chunking with overlap
- Token limit exceeded → Split at semantic boundaries when possible

## Testing

### Running Integration Tests
```bash
# Run the comprehensive test suite
python test_tree_sitter_integration.py

# Expected output:
# - TreeSitterParser functionality test
# - TreeSitterChunker functionality test  
# - ChunkingFactory integration test
# - Fallback behavior test
```

### Manual Testing
```python
# Test parser status
from src.processors.chunking.parsers.tree_sitter_parser import TreeSitterParser
parser = TreeSitterParser()
print(parser.get_language_status())

# Test chunker status
from src.processors.chunking import TreeSitterChunker
chunker = TreeSitterChunker()
print(chunker.get_parser_status())
```

## Performance Considerations

### Initialization Time
- Tree-sitter grammar compilation: 30-60 seconds (first time only)
- Grammar caching: Subsequent runs are fast (~1-2 seconds)
- Incremental language loading: Only requested languages are compiled

### Runtime Performance
- Tree-sitter parsing: Fast (~1ms per file)
- Semantic boundary detection: Minimal overhead
- Memory usage: Reasonable (grammars ~10MB each)

### Optimization Tips
```python
# Pre-initialize for better performance
chunker = TreeSitterChunker()  # Initialize once, reuse

# Use specific language extensions to reduce memory
parser = TreeSitterParser(['py', 'js'])  # Only Python and JavaScript

# Monitor parser status
status = chunker.get_parser_status()
if not status['parser_initialized']:
    # Handle initialization failure
    pass
```

## Troubleshooting

### Common Issues

1. **Tree-sitter compilation fails**
   ```
   Solution: Ensure git is installed and accessible
   Check network connectivity for grammar downloads
   Verify disk space in ~/.code_parser_cache/
   ```

2. **Parser not loading languages**
   ```
   Solution: Check logs for specific error messages
   Try manual grammar installation
   Verify file extension mapping
   ```

3. **Fallback chunking always used**
   ```
   Solution: Check parser initialization status
   Verify language support with get_language_status()
   Check file extension is in supported list
   ```

### Debug Information
```python
# Get detailed status information
chunker = TreeSitterChunker()
status = chunker.get_parser_status()

print(f"Parser initialized: {status['parser_initialized']}")
print(f"Loaded languages: {status.get('loaded_languages', [])}")
print(f"Cache directory: {status.get('cache_directory', 'unknown')}")
```

## Migration Guide

### For Existing Users
The integration is **backward compatible**:
- Existing chunkers continue to work unchanged
- TreeSitterChunker adds enhanced capabilities
- Fallback mechanisms ensure robustness
- No breaking changes to existing APIs

### Gradual Adoption
1. **Phase 1**: Deploy with TreeSitterChunker as optional enhancement
2. **Phase 2**: Monitor performance and accuracy improvements  
3. **Phase 3**: Consider making tree-sitter the default for supported languages

### Configuration Migration
```python
# Old configuration
processor = TextProcessor(chunk_size=1500, chunk_overlap=100)

# New configuration (enhanced)
processor = TextProcessor(
    chunk_size=1500, 
    chunk_overlap=100,
    use_enhanced_chunking=True  # Enable tree-sitter
)
```

## Benefits of Integration

### Improved Accuracy
- **Semantic boundaries**: Chunks respect code structure (classes, functions)
- **Symbol awareness**: Enhanced metadata for better retrieval
- **Language-specific parsing**: Proper handling of language constructs

### Better Performance
- **Efficient parsing**: Tree-sitter is faster than AST parsing
- **Reduced fragmentation**: Semantic chunking creates more coherent chunks
- **Enhanced retrieval**: Better metadata improves search accuracy

### Enhanced Metadata
```python
# Enhanced chunk metadata includes:
{
    'chunk_type': 'class',           # Type of code construct
    'symbol_name': 'UserService',    # Name of the symbol
    'line_start': 15,                # Starting line number
    'line_end': 45,                  # Ending line number
    'language': 'csharp',            # Programming language
    'contains_documentation': True,   # Has comments/docstrings
    'chunking_method': 'tree_sitter', # Method used for chunking
    'symbols_count': 3               # Number of symbols in chunk
}
```

## Future Enhancements

### Planned Improvements
- Additional language support (Rust, Go, Java)
- Smart chunk size adaptation based on code complexity
- Cross-reference detection and preservation
- Integration with code analysis tools

### Extensibility
```python
# Easy to add new languages
parser = TreeSitterParser(['py', 'js', 'new_language'])

# Custom node type definitions
custom_node_types = {
    'new_language': {
        'custom_construct': 'Custom Type'
    }
}
```

This integration provides a robust, scalable foundation for enhanced semantic chunking while maintaining compatibility with existing systems.
