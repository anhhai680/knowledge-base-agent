"""
Factory for selecting appropriate chunking strategy based on file extension.
"""

from typing import Dict, List, Any
from langchain.docstore.document import Document

from ...config import settings

from .base_chunker import BaseChunker
from .fallback_chunker import FallbackChunker
from ...utils.logging import get_logger

logger = get_logger(__name__)


class ChunkingFactory:
    """
    Factory class that selects the appropriate chunking strategy based on file extension.
    
    Manages registration of chunkers and provides fallback mechanism for unsupported types.
    """
    
    def __init__(self):
        """Initialize the chunking factory."""
        self._chunkers: Dict[str, BaseChunker] = {}
        self._fallback_chunker = FallbackChunker()
        self._default_config = {
            'max_chunk_size': settings.settings.chunk_size,
            'chunk_overlap': settings.settings.chunk_overlap
        }

    def register_chunker(self, chunker: BaseChunker) -> None:
        """
        Register a chunker for specific file extensions.
        
        Args:
            chunker: Chunker instance to register
        """
        for extension in chunker.get_supported_extensions():
            self._chunkers[extension.lower()] = chunker
            logger.debug(f"Registered chunker {chunker.__class__.__name__} for extension {extension}")
    
    def get_chunker(self, file_path: str) -> BaseChunker:
        """
        Get appropriate chunker for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Appropriate chunker instance
        """
        # Extract file extension
        if '.' in file_path:
            extension = '.' + file_path.split('.')[-1].lower()
        else:
            extension = ''
        
        # Find registered chunker
        chunker = self._chunkers.get(extension)
        
        if chunker:
            logger.debug(f"Using {chunker.__class__.__name__} for file {file_path}")
            return chunker
        else:
            logger.debug(f"Using fallback chunker for file {file_path} (extension: {extension})")
            return self._fallback_chunker

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Chunk multiple documents using appropriate chunkers.
        
        Args:
            documents: List of documents to chunk
            
        Returns:
            List of chunked documents
        """
        if not documents:
            logger.debug("No documents to chunk")
            return []
        
        chunked_docs = []
        failed_docs = []
        
        for doc in documents:
            try:
                # Get appropriate chunker for this document
                file_path = doc.metadata.get('file_path', 'unknown')
                chunker = self.get_chunker(file_path)
                
                # Configure chunker with default settings
                chunker.configure(self._default_config)
                
                # Chunk the document
                chunks = chunker.chunk_document(doc)
                chunked_docs.extend(chunks)
                
                logger.debug(f"Successfully chunked document {file_path} into {len(chunks)} chunks")
                
            except Exception as e:
                logger.warning(f"Failed to chunk document {doc.metadata.get('file_path', 'unknown')}: {e}")
                failed_docs.append(doc)
                # Continue with other documents
        
        if failed_docs:
            logger.warning(f"Failed to chunk {len(failed_docs)} out of {len(documents)} documents")
        
        logger.info(f"Chunking complete: {len(chunked_docs)} chunks from {len(documents)} documents")
        return chunked_docs

    def get_supported_extensions(self) -> List[str]:
        """
        Get all supported file extensions from registered chunkers.
        
        Returns:
            List of supported file extensions
        """
        extensions = set()
        for chunker in self._chunkers.values():
            extensions.update(chunker.get_supported_extensions())
        return list(extensions)

    def get_chunker_info(self) -> Dict[str, List[str]]:
        """
        Get information about registered chunkers and their supported extensions.
        
        Returns:
            Dictionary mapping chunker class names to their supported extensions
        """
        info = {}
        
        # Add registered chunkers
        for chunker in self._chunkers.values():
            chunker_name = chunker.__class__.__name__
            if chunker_name not in info:
                info[chunker_name] = []
            info[chunker_name].extend(chunker.get_supported_extensions())
        
        # Add fallback chunker
        info["FallbackChunker"] = self._fallback_chunker.get_supported_extensions()
        
        return info

    def configure_chunking(self, config: Dict[str, Any]) -> None:
        """
        Configure the chunking factory with the provided configuration.
        
        Args:
            config: Configuration dictionary containing chunking settings
        """
        try:
            # Update default configuration if provided
            if 'fallback' in config:
                fallback_config = config['fallback']
                self._default_config.update({
                    'max_chunk_size': fallback_config.get('max_chunk_size', self._default_config['max_chunk_size']),
                    'chunk_overlap': fallback_config.get('chunk_overlap', self._default_config['chunk_overlap'])
                })
            
            # Update global settings
            if 'global_timeout_seconds' in config:
                self._default_config['global_timeout'] = config['global_timeout_seconds']
            
            if 'chunking_timeout_seconds' in config:
                self._default_config['chunking_timeout'] = config['chunking_timeout_seconds']
            
            if 'parsing_timeout_seconds' in config:
                self._default_config['parsing_timeout'] = config['parsing_timeout_seconds']
            
            # Update fallback chunker configuration
            if 'fallback' in config:
                fallback_config = config['fallback']
                self._fallback_chunker.configure(fallback_config)
            
            logger.debug("Chunking factory configured successfully")
            
        except Exception as e:
            logger.warning(f"Failed to configure chunking factory: {e}")
            # Continue with default configuration
