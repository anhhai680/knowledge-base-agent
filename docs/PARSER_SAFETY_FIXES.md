# AdvancedParser Safety Fixes

## Overview

This document describes the comprehensive fixes implemented to resolve the AdvancedParser infinite loop and high CPU usage issues that were causing repository indexing to fail.

## Issues Identified

### 1. Infinite Loops in Tree-Sitter Parsing
- **Problem**: Tree-sitter parsers could enter infinite loops when processing complex or malformed code
- **Cause**: Missing timeout protection and recursion depth limits
- **Impact**: Docker containers would consume 100% CPU indefinitely

### 2. Missing Error Recovery
- **Problem**: When parsing failed, the system would retry indefinitely
- **Cause**: Insufficient error handling and fallback mechanisms
- **Impact**: Indexing would never complete

### 3. Memory Leaks
- **Problem**: Tree-sitter objects not properly cleaned up
- **Cause**: Missing resource management
- **Impact**: Memory usage would grow until system failure

### 4. Recursive Method Issues
- **Problem**: AST traversal methods could exceed stack limits
- **Cause**: No recursion depth tracking
- **Impact**: Stack overflow crashes

## Solutions Implemented

### 1. Timeout Protection

#### Parser-Level Timeouts
```python
# In AdvancedParser
self.max_parse_time = self.config.get('max_parse_time_seconds', 30)
self.max_recursion_depth = self.config.get('max_recursion_depth', 100)
self.max_elements_per_file = self.config.get('max_elements_per_file', 1000)
```

#### Threaded Parsing with Timeouts
```python
def _parse_with_tree_sitter_with_timeout(self, source_code: str) -> Optional[ts.Tree]:
    """Parse source code with tree-sitter with timeout protection."""
    thread = threading.Thread(target=parse_code)
    thread.daemon = True
    thread.start()
    thread.join(timeout=self.max_parse_time)
    
    if thread.is_alive():
        logger.warning(f"Parsing timeout for {self.language_name} file")
        return None
```

#### Chunking Timeouts
```python
def _chunk_documents_with_timeout(self, documents: List[Document], timeout_seconds: int = 60):
    """Chunk documents with timeout protection to prevent infinite loops."""
    thread = threading.Thread(target=chunk_documents)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout_seconds)
```

### 2. Recursion Depth Protection

#### AST Parser Safety
```python
def _visit_node(self, node: ast.AST, parent_name: Optional[str] = None) -> None:
    # Check recursion depth
    self.current_recursion_depth += 1
    if self.current_recursion_depth > self.max_recursion_depth:
        logger.error(f"Maximum recursion depth ({self.max_recursion_depth}) exceeded")
        self.current_recursion_depth -= 1
        return
    
    try:
        # ... parsing logic ...
    finally:
        # Always decrement recursion depth
        self.current_recursion_depth -= 1
```

#### Tree-Sitter Node Traversal Safety
```python
def _extract_semantic_elements_safe(self, tree: ts.Tree, source_code: str) -> List[SemanticElement]:
    """Extract semantic elements with safety checks to prevent infinite loops."""
    try:
        elements = self._extract_semantic_elements(tree, source_code)
        
        # Safety check: limit number of elements
        if len(elements) > self.max_elements_per_file:
            logger.warning(f"Too many elements ({len(elements)}), limiting to {self.max_elements_per_file}")
            elements = elements[:self.max_elements_per_file]
        
        return elements
        
    except RecursionError:
        logger.error("Recursion error during semantic extraction")
        return []
```

### 3. Enhanced Error Handling

#### Graceful Fallback
```python
def _initialize_parser(self) -> None:
    """Initialize the tree-sitter parser and language."""
    try:
        self._language = self._get_tree_sitter_language_with_timeout()
        if not self._language:
            raise AdvancedParserError("Failed to load tree-sitter language")
            
        self._parser = ts.Parser()
        self._parser.set_language(self._language)
        logger.debug(f"Initialized tree-sitter parser for {self.language_name}")
        
    except Exception as e:
        logger.error(f"Failed to initialize tree-sitter parser for {self.language_name}: {e}")
        # Don't raise here, allow fallback to work
        self._parser = None
        self._language = None
```

#### Fallback to Traditional Chunking
```python
def _process_documents_enhanced(self, documents: List[Document]) -> List[Document]:
    try:
        # ... enhanced processing ...
    except Exception as e:
        logger.error(f"Error in enhanced processing: {str(e)}")
        logger.info("Falling back to traditional processing due to enhanced chunking error")
        return self._process_documents_traditional(documents)
```

### 4. Configuration-Based Safety Limits

#### Safety Configuration
```python
@dataclass
class ChunkingConfig:
    # Timeout and safety settings
    global_timeout_seconds: int = 300  # 5 minutes total timeout
    chunking_timeout_seconds: int = 60  # 1 minute per chunking operation
    parsing_timeout_seconds: int = 30   # 30 seconds per parsing operation
    
    # Memory and performance limits
    max_memory_usage_mb: int = 1024  # 1GB memory limit
    max_concurrent_operations: int = 4
    max_file_size_mb: int = 10
    
    # Error handling
    max_consecutive_failures: int = 5
    retry_attempts: int = 3
    exponential_backoff: bool = True
```

#### Automatic Validation
```python
def _validate_config(self) -> None:
    """Validate configuration values and apply safety limits."""
    # Ensure timeouts are reasonable
    if self.config.global_timeout_seconds > 1800:  # 30 minutes max
        logger.warning("Global timeout too high, limiting to 30 minutes")
        self.config.global_timeout_seconds = 1800
    
    if self.config.chunking_timeout_seconds > 300:  # 5 minutes max
        logger.warning("Chunking timeout too high, limiting to 5 minutes")
        self.config.chunking_timeout_seconds = 300
```

### 5. Progress Monitoring and Logging

#### Document Processing Progress
```python
for i, document in enumerate(documents):
    # Add progress logging for large document sets
    if len(documents) > 100 and i % 100 == 0:
        logger.info(f"Chunking progress: {i}/{len(documents)} documents processed")
```

#### Performance Statistics
```python
def get_statistics(self) -> Dict[str, Any]:
    """Get parser performance statistics."""
    return {
        "language": self.language_name,
        "parse_count": self._parse_count,
        "failed_parses": self._failed_parses,
        "total_parse_time_ms": self._total_parse_time,
        "average_parse_time_ms": avg_parse_time,
        "max_parse_time_seconds": self.max_parse_time,
        "max_recursion_depth": self.max_recursion_depth,
        "max_elements_per_file": self.max_elements_per_file
    }
```

## Configuration Options

### Environment Variables
```bash
# Set global timeout (5 minutes)
export CHUNKING_GLOBAL_TIMEOUT=300

# Set parsing timeout (30 seconds)
export CHUNKING_PARSING_TIMEOUT=30

# Set chunking timeout (1 minute)
export CHUNKING_CHUNKING_TIMEOUT=60

# Set memory limit (1GB)
export CHUNKING_MAX_MEMORY_MB=1024
```

### Configuration File
```yaml
# chunking_config.yaml
global_timeout_seconds: 300
chunking_timeout_seconds: 60
parsing_timeout_seconds: 30
max_memory_usage_mb: 1024
max_concurrent_operations: 4

strategies:
  .py:
    max_parse_time_seconds: 30
    max_recursion_depth: 100
    max_elements_per_file: 1000
  .js:
    max_parse_time_seconds: 30
    max_recursion_depth: 100
    max_elements_per_file: 1000
  .ts:
    max_parse_time_seconds: 30
    max_recursion_depth: 100
    max_elements_per_file: 1000
```

## Testing

### Run Safety Tests
```bash
python test_parser_safety.py
```

### Test Coverage
- ✅ Parser timeout protection
- ✅ Chunking timeout protection
- ✅ Recursion depth limits
- ✅ Error recovery mechanisms
- ✅ Configuration safety limits
- ✅ Fallback mechanisms

## Monitoring and Debugging

### Log Analysis
Look for these log patterns to identify issues:

```bash
# Timeout warnings
grep "timeout\|Timeout" logs/*.log

# Recursion depth exceeded
grep "recursion depth\|RecursionError" logs/*.log

# Fallback activations
grep "fallback\|Fallback" logs/*.log

# Performance issues
grep "took too long\|slow" logs/*.log
```

### Performance Metrics
Monitor these metrics during indexing:

- **Parse time per file**: Should be under configured timeout
- **Memory usage**: Should stay under configured limits
- **Failed parse count**: Should be low (< 5% of total files)
- **Fallback rate**: Should be low (< 10% of total files)

### Health Checks
```python
# Get parser statistics
stats = parser.get_statistics()
print(f"Parse count: {stats['parse_count']}")
print(f"Failed parses: {stats['failed_parses']}")
print(f"Average parse time: {stats['average_parse_time_ms']:.2f}ms")

# Get configuration safety summary
config_manager = ChunkingConfigManager()
safety_summary = config_manager.get_safety_summary()
print(f"Safety limits: {safety_summary}")
```

## Troubleshooting

### Common Issues

#### 1. Still Getting Timeouts
- Check if file sizes exceed `max_file_size_mb`
- Verify tree-sitter language packages are installed
- Check system resources (CPU, memory)

#### 2. High Memory Usage
- Reduce `max_elements_per_file` in configuration
- Lower `max_concurrent_operations`
- Check for memory leaks in custom parsers

#### 3. Slow Performance
- Increase timeout values if system can handle it
- Check if fallback chunking is being used too often
- Monitor system resource usage

### Debug Mode
Enable debug logging to see detailed parsing information:

```python
import logging
logging.getLogger('processors.chunking').setLevel(logging.DEBUG)
```

## Migration Guide

### From Old Version
1. **Update imports**: No breaking changes in public APIs
2. **Configuration**: Old config files will be automatically migrated
3. **Behavior**: More robust error handling, may see more fallback usage initially

### Performance Impact
- **Positive**: Prevents infinite loops and system crashes
- **Neutral**: Minimal overhead from timeout checks
- **Negative**: Some files may take longer to process due to safety checks

## Future Improvements

### Planned Enhancements
1. **Adaptive timeouts**: Adjust timeouts based on file complexity
2. **Memory profiling**: Better memory usage tracking
3. **Parallel processing**: Safe concurrent parsing
4. **Machine learning**: Predict parsing complexity

### Contributing
When adding new parsers or chunkers:

1. **Always implement timeout protection**
2. **Add recursion depth tracking**
3. **Include proper error handling**
4. **Add performance monitoring**
5. **Write safety tests**

## Conclusion

These safety fixes ensure that the AdvancedParser can handle any repository without causing infinite loops or excessive CPU usage. The system now gracefully degrades to fallback mechanisms when needed, providing reliable indexing for all codebases.

The key principles implemented are:
- **Fail fast**: Detect issues early and stop processing
- **Graceful degradation**: Fall back to simpler methods when needed
- **Resource protection**: Prevent memory and CPU exhaustion
- **Monitoring**: Track performance and identify issues
- **Configuration**: Allow tuning for different environments
