"""
Factory for selecting appropriate chunking strategy based on file extension.
"""

from typing import Dict, List
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
    
    def configure_chunking(self, chunking_config: Dict) -> None:
        """
        Configure chunking parameters.
        
        Args:
            chunking_config: Configuration dictionary with chunking parameters
        """
        # Update default config
        if 'fallback' in chunking_config:
            fallback_config = chunking_config['fallback']
            self._default_config.update(fallback_config)
            
            # Recreate fallback chunker with new config
            self._fallback_chunker = FallbackChunker(
                max_chunk_size=fallback_config.get('chunk_size', 1000),
                chunk_overlap=fallback_config.get('chunk_overlap', 200)
            )
        
        # Configure individual chunkers based on file type
        if 'strategies' in chunking_config:
            strategies = chunking_config['strategies']
            
            # This will be used when we implement language-specific chunkers
            for extension, config in strategies.items():
                if extension in self._chunkers:
                    chunker = self._chunkers[extension]
                    # Update chunker configuration if it supports it
                    if hasattr(chunker, 'configure'):
                        chunker.configure(config)
    
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
        Chunk a list of documents using appropriate strategies.
        
        Args:
            documents: List of documents to chunk
            
        Returns:
            List of chunked documents
        """
        if not documents:
            return []
        
        logger.info(f"Chunking {len(documents)} documents using extension-based strategies")
        
        chunked_documents = []
        chunker_stats = {}
        failed_documents = 0
        
        # Add safety check for document count
        if len(documents) > 1000:  # Prevent processing too many documents at once
            logger.warning(f"Too many documents ({len(documents)}), limiting to 1000")
            documents = documents[:1000]
        
        for i, document in enumerate(documents):
            try:
                # Add progress logging for large document sets
                if len(documents) > 100 and i % 100 == 0:
                    logger.info(f"Chunking progress: {i}/{len(documents)} documents processed")
                
                # Get file path from metadata
                file_path = document.metadata.get('file_path', '')
                
                # Get appropriate chunker
                chunker = self.get_chunker(file_path)
                chunker_name = chunker.__class__.__name__
                
                # Track chunker usage
                if chunker_name not in chunker_stats:
                    chunker_stats[chunker_name] = 0
                chunker_stats[chunker_name] += 1
                
                # Chunk the document with timeout protection
                chunks = self._chunk_document_with_timeout(chunker, document, chunker_name)
                
                if not chunks:
                    logger.warning(f"Chunker {chunker_name} produced no chunks for document: {file_path}")
                
                chunked_documents.extend(chunks)
                
            except Exception as e:
                failed_documents += 1
                logger.warning(f"Failed to chunk document {document.metadata.get('file_path', 'unknown')}: {str(e)}")
                # Log more details about the failure for debugging
                logger.debug(f"Document metadata: {document.metadata}")
                logger.debug(f"Document content length: {len(document.page_content)}")
                continue
        
        # Enhanced logging
        total_chunks = len(chunked_documents)
        logger.info(f"Created {total_chunks} chunks from {len(documents)} documents ({failed_documents} failed)")
        for chunker_name, count in chunker_stats.items():
            logger.info(f"  {chunker_name}: {count} documents")
        
        if failed_documents > 0:
            logger.warning(f"Enhanced chunking failed for {failed_documents} documents - check individual chunker implementations")
        
        # Validate chunk sizes to prevent embedding API token limit issues
        validated_documents = self._validate_chunk_sizes(chunked_documents)
        
        if len(validated_documents) != total_chunks:
            logger.info(f"Chunk validation resulted in {len(validated_documents)} final chunks (split {len(validated_documents) - total_chunks} oversized chunks)")
        
        return validated_documents
    
    def _chunk_document_with_timeout(self, chunker: BaseChunker, document: Document, chunker_name: str, timeout_seconds: int = 30) -> List[Document]:
        """
        Chunk a single document with timeout protection.
        
        Args:
            chunker: The chunker to use
            document: Document to chunk
            chunker_name: Name of the chunker for logging
            timeout_seconds: Maximum time to spend on chunking
            
        Returns:
            List of chunked documents
        """
        import threading
        
        result = [None]
        error = [None]
        
        def chunk_document():
            try:
                result[0] = chunker.chunk_document(document)
            except Exception as e:
                error[0] = e
        
        # Run chunking in a separate thread with timeout
        thread = threading.Thread(target=chunk_document)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout_seconds)
        
        if thread.is_alive():
            logger.warning(f"Chunking timeout for {chunker_name} on document {document.metadata.get('file_path', 'unknown')}")
            return []
        
        if error[0]:
            logger.error(f"Chunking error in {chunker_name}: {error[0]}")
            return []
            
        return result[0] or []
    
    def _validate_chunk_sizes(self, documents: List[Document]) -> List[Document]:
        """
        Validate and potentially split chunks that are too large for embedding APIs.
        
        Args:
            documents: List of chunked documents to validate
            
        Returns:
            List of validated documents with oversized chunks split
        """
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        validated_documents = []
        max_chunk_chars = 8000  # Conservative limit to avoid token issues
        oversized_count = 0
        
        for doc in documents:
            if len(doc.page_content) <= max_chunk_chars:
                validated_documents.append(doc)
            else:
                # Split oversized chunk
                oversized_count += 1
                logger.warning(f"Splitting oversized chunk ({len(doc.page_content)} chars) from {doc.metadata.get('file_path', 'unknown')}")
                
                # Create emergency text splitter for oversized chunks
                emergency_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=max_chunk_chars,
                    chunk_overlap=200,
                    length_function=len,
                    separators=["\n\n", "\n", " ", ""]
                )
                
                # Split the oversized document
                sub_chunks = emergency_splitter.split_documents([doc])
                
                # Update metadata for sub-chunks
                for i, sub_chunk in enumerate(sub_chunks):
                    sub_chunk.metadata.update({
                        "chunk_index": f"{doc.metadata.get('chunk_index', 0)}.{i}",
                        "emergency_split": True,
                        "original_chunk_size": len(doc.page_content)
                    })
                
                validated_documents.extend(sub_chunks)
        
        if oversized_count > 0:
            logger.info(f"Split {oversized_count} oversized chunks into smaller pieces for embedding compatibility")
        
        return validated_documents
    
    def get_supported_extensions(self) -> List[str]:
        """
        Get list of all supported file extensions.
        
        Returns:
            List of supported file extensions
        """
        return list(self._chunkers.keys())
    
    def get_chunker_info(self) -> Dict[str, List[str]]:
        """
        Get information about registered chunkers.
        
        Returns:
            Dictionary mapping chunker names to supported extensions
        """
        info = {}
        for extension, chunker in self._chunkers.items():
            chunker_name = chunker.__class__.__name__
            if chunker_name not in info:
                info[chunker_name] = []
            info[chunker_name].append(extension)
        
        # Add fallback chunker info
        info['FallbackChunker'] = ['*']
        
        return info
