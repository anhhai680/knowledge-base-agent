"""
Tree-sitter based chunker that provides enhanced semantic chunking across multiple languages.
Based on the provided Chunker.py with integration into the existing chunking system.
"""

from typing import List, Dict, Any, Optional
from langchain.docstore.document import Document

from .base_chunker import BaseChunker, ChunkMetadata
from .parsers.tree_sitter_parser import TreeSitterParser
from ...utils.chunk_utils import count_tokens
from ...utils.logging import get_logger

logger = get_logger(__name__)


class TreeSitterChunker(BaseChunker):
    """
    Enhanced chunker using tree-sitter for semantic boundary detection.
    
    This chunker provides semantic chunking for multiple programming languages
    using tree-sitter parsers for accurate syntax analysis.
    """
    
    def __init__(self, max_chunk_size: int = 1500, chunk_overlap: int = 100):
        """
        Initialize tree-sitter chunker.
        
        Args:
            max_chunk_size: Maximum size for chunks in tokens/characters
            chunk_overlap: Number of characters to overlap between chunks
        """
        super().__init__(max_chunk_size, chunk_overlap)
        
        # Supported file extensions - will be populated after parser initialization
        self._supported_extensions = []
        
        # Initialize tree-sitter parser with error handling
        self.parser = None
        self.encoding_name = "gpt-4"
        self._initialize_parser()
    
    def _initialize_parser(self) -> None:
        """Initialize the tree-sitter parser with error handling."""
        try:
            # Initialize parser for all supported languages
            self.parser = TreeSitterParser()
            
            # Get supported extensions from the parser
            if self.parser:
                status = self.parser.get_language_status()
                self._supported_extensions = [
                    f".{ext}" for ext, loaded in status.items() if loaded
                ]
                logger.info(f"TreeSitterChunker initialized with support for: {self._supported_extensions}")
            else:
                logger.warning("TreeSitterParser initialization failed")
                
        except Exception as e:
            logger.error(f"Failed to initialize TreeSitterParser: {str(e)}")
            logger.info("TreeSitterChunker will operate in fallback mode")
            self.parser = None
    
    def get_supported_extensions(self) -> List[str]:
        """Return list of file extensions this chunker supports."""
        if self._supported_extensions:
            return self._supported_extensions
        else:
            # Fallback to basic extensions if parser failed to initialize
            return ['.py', '.js', '.jsx', '.ts', '.tsx', '.css', '.php', '.cs']
    
    def chunk_document(self, document: Document) -> List[Document]:
        """
        Chunk a document using tree-sitter semantic analysis.
        
        Args:
            document: The document to chunk
            
        Returns:
            List of chunked documents with enhanced metadata
        """
        try:
            content = self._clean_content(document.page_content)
            if not content.strip():
                logger.warning("Empty document content, skipping")
                return []
            
            file_path = document.metadata.get('file_path', '')
            file_extension = self._extract_file_extension(file_path)
            
            # Use tree-sitter chunking if parser is available and supports the language
            if self.parser and self._can_use_tree_sitter(file_extension):
                return self._chunk_with_tree_sitter(document, content, file_extension)
            else:
                # Fall back to simple chunking
                logger.debug(f"Using fallback chunking for {file_path}")
                return self._chunk_with_fallback(document, content, file_extension)
                
        except Exception as e:
            logger.error(f"Error chunking document {document.metadata.get('file_path', 'unknown')}: {str(e)}")
            # Return the original document as a single chunk in case of error
            return [document]
    
    def _extract_file_extension(self, file_path: str) -> str:
        """Extract file extension from file path."""
        if '.' in file_path:
            return file_path.split('.')[-1].lower()
        return ''
    
    def _can_use_tree_sitter(self, file_extension: str) -> bool:
        """Check if tree-sitter can be used for this file extension."""
        return (self.parser is not None and 
                self.parser.is_language_supported(file_extension) and
                self.parser.is_language_loaded(file_extension))
    
    def _chunk_with_tree_sitter(self, document: Document, content: str, file_extension: str) -> List[Document]:
        """
        Perform semantic chunking using tree-sitter analysis.
        
        Args:
            document: Original document
            content: Cleaned content
            file_extension: File extension for language detection
            
        Returns:
            List of semantically chunked documents
        """
        try:
            # Get semantic boundaries from tree-sitter
            boundaries = self.parser.get_semantic_boundaries(content, file_extension)
            
            # Get symbol information for enhanced metadata
            symbols = self.parser.get_symbol_information(content, file_extension)
            
            # Perform chunking with semantic boundaries
            chunks = self._create_semantic_chunks(content, boundaries, symbols, file_extension)
            
            # Convert chunks to Document objects
            chunked_documents = []
            for i, chunk_data in enumerate(chunks):
                chunk_metadata = ChunkMetadata(
                    source=document.metadata.get('source', ''),
                    file_path=document.metadata.get('file_path', ''),
                    file_type=file_extension,
                    chunk_type=chunk_data.get('type', 'content'),
                    symbol_name=chunk_data.get('symbol_name'),
                    line_start=chunk_data.get('line_start'),
                    line_end=chunk_data.get('line_end'),
                    language=self.parser.language_extension_map.get(file_extension),
                    contains_documentation=chunk_data.get('has_documentation', False)
                )
                
                chunk_doc = self._create_chunk_document(
                    chunk_data['content'],
                    document.metadata,
                    chunk_metadata,
                    i,
                    len(chunks)
                )
                
                # Add tree-sitter specific metadata
                chunk_doc.metadata.update({
                    'chunking_method': 'tree_sitter',
                    'semantic_boundaries': len(boundaries),
                    'symbols_count': len([s for s in symbols if 
                                        s['line_start'] >= chunk_data.get('line_start', 0) and 
                                        s['line_end'] <= chunk_data.get('line_end', float('inf'))])
                })
                
                chunked_documents.append(chunk_doc)
            
            logger.debug(f"Tree-sitter chunking: {len(chunked_documents)} chunks from {len(boundaries)} boundaries")
            return chunked_documents
            
        except Exception as e:
            logger.error(f"Tree-sitter chunking failed: {str(e)}, falling back to simple chunking")
            return self._chunk_with_fallback(document, content, file_extension)
    
    def _create_semantic_chunks(self, content: str, boundaries: List[int], symbols: List[Dict], file_extension: str) -> List[Dict]:
        """
        Create chunks based on semantic boundaries while respecting size limits.
        
        Args:
            content: Source code content
            boundaries: List of line numbers representing semantic boundaries
            symbols: List of symbol information
            file_extension: File extension for token counting
            
        Returns:
            List of chunk data dictionaries
        """
        lines = content.split('\n')
        chunks = []
        current_chunk_lines = []
        current_start_line = 0
        
        # Add boundaries at start and end
        all_boundaries = [0] + sorted(set(boundaries)) + [len(lines)]
        
        for i in range(len(all_boundaries) - 1):
            start_boundary = all_boundaries[i]
            end_boundary = all_boundaries[i + 1]
            
            # Get lines for this semantic block
            block_lines = lines[start_boundary:end_boundary]
            block_content = '\n'.join(block_lines)
            
            # Check if adding this block would exceed the chunk size
            potential_chunk = '\n'.join(current_chunk_lines + block_lines)
            token_count = count_tokens(potential_chunk, self.encoding_name)
            
            if token_count > self.max_chunk_size and current_chunk_lines:
                # Create chunk from accumulated lines
                chunk_content = '\n'.join(current_chunk_lines)
                if chunk_content.strip():
                    chunk_info = self._analyze_chunk_content(
                        chunk_content, current_start_line, start_boundary - 1, symbols
                    )
                    chunks.append(chunk_info)
                
                # Start new chunk with current block
                current_chunk_lines = block_lines
                current_start_line = start_boundary
            else:
                # Add block to current chunk
                current_chunk_lines.extend(block_lines)
                if not current_chunk_lines or not any(line.strip() for line in current_chunk_lines):
                    current_start_line = start_boundary
        
        # Handle remaining lines
        if current_chunk_lines:
            chunk_content = '\n'.join(current_chunk_lines)
            if chunk_content.strip():
                chunk_info = self._analyze_chunk_content(
                    chunk_content, current_start_line, len(lines) - 1, symbols
                )
                chunks.append(chunk_info)
        
        return chunks
    
    def _analyze_chunk_content(self, content: str, start_line: int, end_line: int, symbols: List[Dict]) -> Dict:
        """
        Analyze chunk content to extract metadata.
        
        Args:
            content: Chunk content
            start_line: Starting line number
            end_line: Ending line number  
            symbols: List of all symbols in the file
            
        Returns:
            Dictionary with chunk information and metadata
        """
        # Find symbols that fall within this chunk
        chunk_symbols = [
            s for s in symbols 
            if s['line_start'] >= start_line and s['line_end'] <= end_line
        ]
        
        # Determine chunk type based on content
        chunk_type = 'content'
        symbol_name = None
        has_documentation = False
        
        if chunk_symbols:
            # Use the first/primary symbol for chunk identification
            primary_symbol = chunk_symbols[0]
            chunk_type = primary_symbol['type'].lower()
            symbol_name = primary_symbol['name']
        
        # Check for documentation patterns
        content_lower = content.lower()
        doc_indicators = ['"""', "'''", '/*', '//', '#', 'docstring', 'todo', 'fixme', 'note']
        has_documentation = any(indicator in content_lower for indicator in doc_indicators)
        
        return {
            'content': content,
            'type': chunk_type,
            'symbol_name': symbol_name,
            'line_start': start_line,
            'line_end': end_line,
            'has_documentation': has_documentation,
            'symbols': chunk_symbols
        }
    
    def _chunk_with_fallback(self, document: Document, content: str, file_extension: str) -> List[Document]:
        """
        Fallback chunking when tree-sitter is not available.
        
        Args:
            document: Original document
            content: Cleaned content
            file_extension: File extension
            
        Returns:
            List of chunked documents using simple line-based chunking
        """
        lines = content.split('\n')
        chunks = []
        current_chunk = ""
        current_lines = []
        chunk_start_line = 0
        
        for i, line in enumerate(lines):
            potential_chunk = current_chunk + ('\n' if current_chunk else '') + line
            token_count = count_tokens(potential_chunk, self.encoding_name)
            
            if token_count > self.max_chunk_size and current_chunk:
                # Create chunk from accumulated content
                if current_chunk.strip():
                    chunk_metadata = ChunkMetadata(
                        source=document.metadata.get('source', ''),
                        file_path=document.metadata.get('file_path', ''),
                        file_type=file_extension,
                        chunk_type='content',
                        line_start=chunk_start_line,
                        line_end=chunk_start_line + len(current_lines) - 1,
                        language=file_extension,
                        contains_documentation=self._has_documentation_patterns(current_chunk)
                    )
                    
                    chunk_doc = self._create_chunk_document(
                        current_chunk,
                        document.metadata,
                        chunk_metadata,
                        len(chunks),
                        0  # Will be updated later
                    )
                    
                    chunk_doc.metadata.update({
                        'chunking_method': 'fallback_line_based',
                        'token_count': count_tokens(current_chunk, self.encoding_name)
                    })
                    
                    chunks.append(chunk_doc)
                
                # Start new chunk with overlap
                overlap_lines = max(0, len(current_lines) - self.chunk_overlap // 50)  # Rough overlap conversion
                current_lines = current_lines[overlap_lines:] + [line]
                current_chunk = '\n'.join(current_lines)
                chunk_start_line = chunk_start_line + overlap_lines
            else:
                current_lines.append(line)
                current_chunk = potential_chunk
        
        # Handle remaining content
        if current_chunk.strip():
            chunk_metadata = ChunkMetadata(
                source=document.metadata.get('source', ''),
                file_path=document.metadata.get('file_path', ''),
                file_type=file_extension,
                chunk_type='content',
                line_start=chunk_start_line,
                line_end=chunk_start_line + len(current_lines) - 1,
                language=file_extension,
                contains_documentation=self._has_documentation_patterns(current_chunk)
            )
            
            chunk_doc = self._create_chunk_document(
                current_chunk,
                document.metadata,
                chunk_metadata,
                len(chunks),
                0
            )
            
            chunk_doc.metadata.update({
                'chunking_method': 'fallback_line_based',
                'token_count': count_tokens(current_chunk, self.encoding_name)
            })
            
            chunks.append(chunk_doc)
        
        # Update total_chunks for all chunks
        for chunk in chunks:
            chunk.metadata['total_chunks'] = len(chunks)
        
        logger.debug(f"Fallback chunking: {len(chunks)} chunks created")
        return chunks
    
    def _has_documentation_patterns(self, content: str) -> bool:
        """Check if content contains documentation patterns."""
        content_lower = content.lower()
        doc_patterns = [
            '"""', "'''",  # Python docstrings
            '/*', '//',    # C-style comments
            '#',           # Hash comments
            'todo', 'fixme', 'note', 'warning',  # Common doc keywords
            '@param', '@return', '@throws',       # JSDoc patterns
            '///', '<!--',  # XML/HTML comments
        ]
        return any(pattern in content_lower for pattern in doc_patterns)
    
    def get_parser_status(self) -> Dict[str, Any]:
        """Get detailed status information about the tree-sitter parser."""
        if not self.parser:
            return {
                "parser_initialized": False,
                "error": "TreeSitterParser initialization failed",
                "fallback_available": True
            }
        
        return {
            "parser_initialized": True,
            "loaded_languages": self.parser.get_loaded_languages(),
            "language_status": self.parser.get_language_status(),
            "supported_extensions": self.get_supported_extensions(),
            "cache_directory": self.parser.CACHE_DIR
        }
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the chunker with new settings.
        
        Args:
            config: Configuration dictionary
        """
        super().configure(config)
        
        # Handle tree-sitter specific configuration
        if 'encoding_name' in config:
            self.encoding_name = config['encoding_name']
        
        # Re-initialize parser if needed
        if 'reinitialize_parser' in config and config['reinitialize_parser']:
            self._initialize_parser()
