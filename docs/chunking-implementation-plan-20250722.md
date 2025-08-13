# Implementation Plan: File Extension-Based Chunking

## Overview

Transform the current length-based document chunking strategy to an intelligent file extension-based approach that preserves semantic structure of different programming languages and file types. This enhancement will improve the quality of retrieved context for AI Agent responses by maintaining logical code boundaries (classes, methods, namespaces) rather than arbitrary character limits.

## Requirements

### Functional Requirements
1. **Language-Aware Chunking**: Implement chunking strategies specific to programming languages based on file extensions
2. **Semantic Preservation**: Maintain logical code boundaries (classes, methods, functions, namespaces)
3. **Fallback Mechanism**: Use current length-based chunking for unsupported file types
4. **Metadata Enhancement**: Include structural information (method names, class names) in chunk metadata
5. **Configuration Support**: Allow customization of chunking rules per file type
6. **Backward Compatibility**: Ensure existing functionality remains intact during migration

### Non-Functional Requirements
1. **Performance**: Maintain or improve current processing speeds
2. **Scalability**: Support large codebases without significant memory overhead
3. **Extensibility**: Easy addition of new language parsers
4. **Maintainability**: Clear separation of concerns with modular design
5. **Error Handling**: Graceful degradation for malformed or unparseable files

### Supported Languages (Phase 1)
- **C#** (.cs): Namespaces, classes, methods, properties
- **Python** (.py): Classes, functions, imports, docstrings
- **JavaScript/TypeScript** (.js, .ts, .jsx, .tsx): Functions, classes, exports
- **Java** (.java): Packages, classes, methods, interfaces
- **C/C++** (.c, .cpp, .h): Headers, functions, structs, classes
- **Markdown** (.md): Headers, code blocks, sections
- **YAML/JSON** (.yml, .yaml, .json): Top-level keys, nested structures

## Implementation Steps

### Step 1: Create Chunking Strategy Framework
**Files to Create/Modify:**
- `src/processors/chunking/` (new directory)
- `src/processors/chunking/__init__.py`
- `src/processors/chunking/base_chunker.py`
- `src/processors/chunking/chunking_factory.py`

**Tasks:**
1. Create abstract base class `BaseChunker` with interface for file-specific chunking
2. Implement `ChunkingFactory` to select appropriate chunker based on file extension
3. Define common chunk metadata structure with semantic information
4. Create configuration system for chunking parameters per file type

### Step 2: Implement Language-Specific Chunkers
**Files to Create:**
- `src/processors/chunking/csharp_chunker.py`
- `src/processors/chunking/python_chunker.py`
- `src/processors/chunking/javascript_chunker.py`
- `src/processors/chunking/markdown_chunker.py`
- `src/processors/chunking/fallback_chunker.py`

**Implementation Details:**

#### C# Chunker (`csharp_chunker.py`)
```python
# Extract chunks in this order:
# 1. Using statements and namespaces
# 2. Class declarations with attributes
# 3. Individual methods/properties
# 4. Remaining code blocks
```

#### Python Chunker (`python_chunker.py`)
```python
# Extract chunks in this order:
# 1. Import statements and module docstring
# 2. Class definitions with docstrings
# 3. Individual functions with docstrings
# 4. Module-level code
```

#### JavaScript/TypeScript Chunker (`javascript_chunker.py`)
```python
# Extract chunks in this order:
# 1. Import/require statements
# 2. Interface/type definitions (TS)
# 3. Function declarations and classes
# 4. Export statements
```

#### Markdown Chunker (`markdown_chunker.py`)
```python
# Extract chunks in this order:
# 1. Document title (# header)
# 2. Major sections (## headers)
# 3. Subsections (### headers and content)
# 4. Code blocks as separate chunks
```

### Step 3: AST Parser Integration
**Files to Create/Modify:**
- `src/processors/chunking/parsers/` (new directory)
- `src/processors/chunking/parsers/ast_parser.py`
- `src/processors/chunking/parsers/tree_sitter_parser.py` (optional)

**Tasks:**
1. Implement AST-based parsing for supported languages using Python's `ast` module
2. Create language-specific parsers that can identify:
   - Function/method boundaries
   - Class definitions
   - Import/namespace declarations
   - Documentation strings
3. Extract line numbers and character positions for precise chunking
4. Handle syntax errors gracefully with fallback to regex-based parsing

### Step 4: Configuration System Enhancement
**Files to Modify:**
- `src/config/settings.py`
- `src/config/chunking_config.py` (new)

**Configuration Structure:**
```yaml
chunking:
  strategies:
    '.cs':
      max_chunk_size: 2000
      preserve_methods: true
      include_imports: true
      chunk_overlap: 50
    '.py':
      max_chunk_size: 1500
      preserve_functions: true
      include_docstrings: true
      chunk_overlap: 100
  fallback:
    chunk_size: 1000
    chunk_overlap: 200
```

### Step 5: Update Text Processor
**Files to Modify:**
- `src/processors/text_processor.py`

**Changes:**
1. Replace `RecursiveCharacterTextSplitter` initialization with `ChunkingFactory`
2. Modify `process_documents()` to use file extension-based chunking
3. Add semantic metadata extraction and enhancement
4. Maintain backward compatibility with existing chunk statistics

### Step 6: Enhanced Metadata System
**Files to Modify:**
- `src/processors/text_processor.py`
- `src/loaders/github_loader.py`

**Metadata Enhancements:**
```python
# Enhanced chunk metadata structure
{
    # Existing metadata
    "source": "github",
    "repository": "owner/repo",
    "file_path": "src/utils/helper.cs",
    "file_type": ".cs",
    
    # New semantic metadata
    "chunk_type": "method",  # method, class, namespace, import, etc.
    "symbol_name": "CalculateScore",  # function/class/method name
    "parent_symbol": "UserService",  # containing class/namespace
    "line_start": 45,
    "line_end": 67,
    "language": "csharp",
    "contains_documentation": true
}
```

### Step 7: Testing Implementation
**Files to Create:**
- `tests/test_chunking/` (new directory)
- `tests/test_chunking/test_base_chunker.py`
- `tests/test_chunking/test_csharp_chunker.py`
- `tests/test_chunking/test_python_chunker.py`
- `tests/test_chunking/test_chunking_factory.py`
- `tests/test_text_processor_enhanced.py`

**Test Cases:**
1. **Unit Tests**: Each chunker with sample code files
2. **Integration Tests**: End-to-end processing with real repository files
3. **Performance Tests**: Compare processing speed with current implementation
4. **Edge Cases**: Malformed code, empty files, very large files
5. **Metadata Validation**: Ensure all semantic metadata is correctly extracted

### Step 8: Migration and Deployment
**Files to Modify:**
- `requirements.txt` (add AST parsing dependencies if needed)
- `docker-compose.yml` (environment variables for chunking config)
- `docs/` (update documentation)

**Migration Strategy:**
1. Implement feature flag for new chunking system
2. Run parallel processing to compare results
3. Gradual rollout with monitoring
4. Full migration after validation

## Testing Strategy

### Unit Testing
- **Chunker Classes**: Test each language-specific chunker with representative code samples
- **AST Parser**: Validate parsing accuracy for different language constructs
- **Factory Pattern**: Ensure correct chunker selection based on file extensions
- **Configuration**: Test various configuration combinations

### Integration Testing
- **End-to-End Processing**: Test complete pipeline from GitHub loading to vector storage
- **Performance Comparison**: Benchmark against current implementation
- **Memory Usage**: Monitor memory consumption with large repositories
- **Error Handling**: Test with malformed and edge-case files

### Quality Assurance
- **Semantic Preservation**: Validate that logical code boundaries are maintained
- **Retrieval Quality**: Test RAG performance with semantically chunked documents
- **Metadata Accuracy**: Ensure all extracted metadata is correct and useful
- **Backward Compatibility**: Verify existing functionality remains intact

### Test Data
- **Sample Repositories**: Create test repositories with various programming languages
- **Edge Cases**: Collect examples of complex code structures, deeply nested classes, etc.
- **Real-World Validation**: Test with actual open-source repositories of different sizes

## Success Criteria

1. **Improved Retrieval Quality**: AI Agent provides more accurate and contextually relevant answers
2. **Semantic Coherence**: Retrieved chunks contain complete logical units (full methods, classes)
3. **Performance Maintained**: Processing time remains within 20% of current implementation
4. **Extensibility**: New language support can be added with minimal effort
5. **User Experience**: Users notice improved answer quality and relevance
6. **System Stability**: No degradation in system reliability or error rates

## Implementation Timeline

### Phase 1: Foundation (Week 1-2)
- Create chunking framework and base classes
- Implement configuration system
- Set up testing infrastructure

### Phase 2: Core Language Support (Week 3-4)
- Implement C#, Python, and JavaScript chunkers
- Integrate AST parsers
- Update text processor integration

### Phase 3: Testing & Validation (Week 5-6)
- Comprehensive unit and integration testing
- Performance benchmarking
- Real-world validation with sample repositories

### Phase 4: Migration & Deployment (Week 7-8)
- Feature flag implementation
- Gradual rollout and monitoring
- Documentation updates
- Production deployment

## Risk Mitigation

### Technical Risks
1. **Performance Degradation**: Extensive benchmarking and optimization
2. **AST Parsing Failures**: Robust fallback mechanisms
3. **Memory Usage**: Streaming processing for large files
4. **Complex Code Structures**: Comprehensive test coverage

### Operational Risks
1. **Migration Issues**: Feature flags and parallel processing
2. **User Impact**: Gradual rollout with monitoring
3. **Data Integrity**: Backup and rollback procedures
4. **Team Knowledge**: Documentation and knowledge transfer

This implementation plan provides a comprehensive roadmap for transitioning from length-based to semantic file extension-based chunking, ensuring improved AI Agent performance while maintaining system reliability and extensibility.