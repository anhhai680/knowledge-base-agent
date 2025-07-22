# Enhanced Chunking System

This directory contains the enhanced semantic chunking system that replaces traditional length-based document chunking with intelligent, language-aware strategies.

## Overview

The enhanced chunking system processes source code files according to their programming language, preserving semantic boundaries like classes, methods, and functions rather than splitting at arbitrary character limits.

## Benefits

- **Better Code Understanding**: Chunks respect logical code boundaries
- **Enhanced Metadata**: Includes symbol names, types, documentation flags
- **Improved Retrieval**: More relevant code snippets in search results  
- **Language Awareness**: Different strategies for Python, C#, etc.
- **Backward Compatible**: Falls back to traditional chunking when needed

## Architecture

```
chunking/
├── __init__.py                 # Package exports
├── base_chunker.py            # Abstract base class and metadata
├── chunking_factory.py        # Factory for chunker selection
├── fallback_chunker.py        # Traditional chunking fallback
├── python_chunker.py          # Python-specific semantic chunking
├── csharp_chunker.py          # C# semantic chunking
└── parsers/
    ├── __init__.py
    └── ast_parser.py          # AST parsing utilities
```

## Usage

### Basic Usage

```python
from src.processors.text_processor import TextProcessor

# Enable enhanced chunking
processor = TextProcessor(
    chunk_size=1000,
    chunk_overlap=100,
    use_enhanced_chunking=True
)

# Process documents
documents = [...]  # Your documents
chunks = processor.process_documents(documents)

# Get enhanced statistics
stats = processor.get_chunk_stats(chunks)
print(f"Created {stats['total_chunks']} semantic chunks")
```

### Configuration

Create a YAML configuration file:

```yaml
chunking:
  enabled: true
  strategies:
    '.py':
      max_chunk_size: 1500
      chunk_overlap: 100
      preserve_methods: true
      include_docstrings: true
    '.cs':
      max_chunk_size: 2000
      chunk_overlap: 50
      preserve_classes: true
  fallback:
    chunk_size: 1000
    chunk_overlap: 200
```

### Enhanced Metadata

Chunks now include semantic metadata:

```python
chunk.metadata = {
    # Traditional metadata
    "file_path": "src/utils/helper.py",
    "source": "github",
    
    # Enhanced semantic metadata
    "chunk_type": "method",           # class, method, function, import
    "symbol_name": "calculate_score", # Function/class name
    "parent_symbol": "Calculator",    # Containing class
    "language": "python",
    "contains_documentation": True,
    "line_start": 45,
    "line_end": 67,
    "symbols": ["calculate_score"]    # All symbols in chunk
}
```

## Supported Languages

### Python (.py, .pyx, .pyi)
- **Chunking Strategy**: AST-based parsing
- **Semantic Elements**: 
  - Import statements (grouped)
  - Module docstrings
  - Class definitions with methods
  - Standalone functions
  - Module-level code
- **Special Features**: Docstring preservation, decorator handling

### C# (.cs)
- **Chunking Strategy**: Regex-based parsing
- **Semantic Elements**:
  - Using statements (grouped)
  - Namespace declarations
  - Class/interface/struct definitions
  - Methods and properties
  - XML documentation comments
- **Special Features**: Access modifier detection, XML docs recognition

### Fallback (All Other Types)
- **Chunking Strategy**: Traditional recursive character splitting
- **Files**: Any file type not specifically supported
- **Behavior**: Identical to the original chunking system

## Extending with New Languages

To add support for a new programming language:

1. **Create a new chunker class**:
```python
from .base_chunker import BaseChunker, ChunkMetadata

class JavaScriptChunker(BaseChunker):
    def get_supported_extensions(self):
        return ['.js', '.jsx', '.ts', '.tsx']
    
    def chunk_document(self, document):
        # Implement language-specific chunking logic
        pass
```

2. **Register with the factory**:
```python
factory = ChunkingFactory()
factory.register_chunker(JavaScriptChunker())
```

3. **Add configuration** (optional):
```yaml
chunking:
  strategies:
    '.js':
      max_chunk_size: 1200
      preserve_functions: true
```

## Testing

Run the demonstration script to see the enhanced chunking in action:

```bash
python demo_enhanced_chunking.py
```

Run unit tests:

```bash
python -m pytest tests/test_chunking/
```

## Backward Compatibility

The enhanced chunking system is fully backward compatible:

- **Opt-in**: Enhanced chunking must be explicitly enabled
- **Fallback**: Automatically falls back to traditional chunking on errors
- **Settings**: Works with existing configuration when disabled
- **API**: No breaking changes to existing text processor interface

## Performance

The enhanced chunking system maintains comparable performance to traditional chunking while providing significantly better semantic understanding:

- **Python files**: ~10-20% slower due to AST parsing, but much better chunk quality
- **C# files**: Similar performance to traditional chunking
- **Other files**: Identical performance (uses same traditional chunking)
- **Memory usage**: Minimal increase due to enhanced metadata

## Configuration Reference

### ChunkingStrategyConfig

- `max_chunk_size`: Maximum characters per chunk (default: 1500)
- `chunk_overlap`: Character overlap between chunks (default: 100)  
- `preserve_methods`: Keep method boundaries intact (default: true)
- `preserve_classes`: Keep class boundaries intact (default: true)
- `include_imports`: Include import statements (default: true)
- `include_docstrings`: Include documentation strings (default: true)
- `respect_indentation`: Maintain code indentation (default: true)

### FallbackConfig

- `chunk_size`: Traditional chunk size (default: 1000)
- `chunk_overlap`: Traditional overlap (default: 200)

### Global Settings

- `enabled`: Enable enhanced chunking system (default: true)
- `use_ast_parsing`: Use AST parsing when available (default: true)
- `max_file_size_mb`: Skip files larger than this (default: 10MB)
