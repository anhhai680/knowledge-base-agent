from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from typing import List, Optional

from src.config import settings
from ..utils.logging import get_logger
from .chunking import ChunkingFactory, PythonChunker, CSharpChunker
from ..config.chunking_config import ChunkingConfigManager

logger = get_logger(__name__)

class TextProcessor:
    """Text processing and chunking with enhanced semantic support"""
    
    def __init__(
        self, 
        chunk_size: int = settings.settings.chunk_size, 
        chunk_overlap: int = settings.settings.chunk_overlap,
        use_enhanced_chunking: bool = True,
        chunking_config_path: Optional[str] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.use_enhanced_chunking = use_enhanced_chunking
        
        # Initialize traditional text splitter (for fallback)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Initialize enhanced chunking system
        if use_enhanced_chunking:
            self._setup_enhanced_chunking(chunking_config_path)
        else:
            self.chunking_factory = None
    
    def _setup_enhanced_chunking(self, config_path: Optional[str] = None) -> None:
        """Setup the enhanced chunking system with language-specific chunkers."""
        try:
            # Initialize configuration manager
            self.config_manager = ChunkingConfigManager(config_path)
            
            # Initialize chunking factory
            self.chunking_factory = ChunkingFactory()
            
            # Register language-specific chunkers
            self._register_chunkers()
            
            # Configure chunking factory with settings
            config = self.config_manager.to_dict()
            self.chunking_factory.configure_chunking(config)
            
            logger.info("Enhanced chunking system initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to initialize enhanced chunking: {str(e)}")
            logger.info("Falling back to traditional chunking")
            self.chunking_factory = None
            self.use_enhanced_chunking = False
    
    def _register_chunkers(self) -> None:
        """Register language-specific chunkers with the factory."""
        try:
            # Ensure chunking factory is available
            if not self.chunking_factory:
                return
            
            # Get configuration for chunkers
            config = self.config_manager.get_config()
            
            # Register Python chunker
            python_config = self.config_manager.get_strategy_config('.py')
            if python_config:
                python_chunker = PythonChunker(
                    max_chunk_size=python_config.max_chunk_size,
                    chunk_overlap=python_config.chunk_overlap
                )
            else:
                python_chunker = PythonChunker()
            
            self.chunking_factory.register_chunker(python_chunker)
            
            # Register C# chunker
            csharp_config = self.config_manager.get_strategy_config('.cs')
            if csharp_config:
                csharp_chunker = CSharpChunker(
                    max_chunk_size=csharp_config.max_chunk_size,
                    chunk_overlap=csharp_config.chunk_overlap
                )
            else:
                csharp_chunker = CSharpChunker()
            
            self.chunking_factory.register_chunker(csharp_chunker)
            
            logger.info("Registered chunkers: Python, C#")
            
        except Exception as e:
            logger.error(f"Error registering chunkers: {str(e)}")
            raise
    
    def process_documents(self, documents: List[Document]) -> List[Document]:
        """Process and chunk documents using enhanced or traditional chunking"""
        logger.info(f"Processing {len(documents)} documents (enhanced_chunking: {self.use_enhanced_chunking})")
        
        # Use enhanced chunking if available
        if self.use_enhanced_chunking and self.chunking_factory:
            return self._process_documents_enhanced(documents)
        else:
            return self._process_documents_traditional(documents)
    
    def _process_documents_enhanced(self, documents: List[Document]) -> List[Document]:
        """Process documents using enhanced semantic chunking."""
        try:
            # Ensure chunking factory is available
            if not self.chunking_factory:
                logger.warning("Chunking factory not available, falling back to traditional processing")
                return self._process_documents_traditional(documents)
            
            processed_docs = []
            
            # Preprocess documents
            cleaned_documents = []
            skipped_empty = 0
            
            for doc in documents:
                try:
                    # Clean text
                    cleaned_text = self._clean_text(doc.page_content)
                    
                    # Skip empty documents but log them
                    if not cleaned_text.strip():
                        skipped_empty += 1
                        logger.debug(f"Skipping empty document: {doc.metadata.get('file_path', 'unknown')}")
                        continue
                    
                    # Update document with cleaned content
                    doc.page_content = cleaned_text
                    cleaned_documents.append(doc)
                    
                except Exception as e:
                    logger.warning(f"Failed to clean document {doc.metadata.get('file_path', 'unknown')}: {str(e)}")
                    continue
            
            if skipped_empty > 0:
                logger.info(f"Skipped {skipped_empty} empty documents during enhanced processing")
            
            # Use chunking factory to process documents
            if cleaned_documents:
                logger.debug(f"Processing {len(cleaned_documents)} cleaned documents with enhanced chunking")
                chunked_docs = self.chunking_factory.chunk_documents(cleaned_documents)
                processed_docs.extend(chunked_docs)
                
                # Log the chunking ratio for monitoring
                avg_chunks_per_doc = len(chunked_docs) / len(cleaned_documents) if cleaned_documents else 0
                logger.info(f"Enhanced chunking: Generated {len(processed_docs)} chunks from {len(cleaned_documents)} cleaned documents (avg: {avg_chunks_per_doc:.2f} chunks/doc)")
            else:
                logger.warning("No cleaned documents available for enhanced chunking")
            
            return processed_docs
            
        except Exception as e:
            logger.error(f"Error in enhanced processing: {str(e)}")
            logger.info("Falling back to traditional processing due to enhanced chunking error")
            return self._process_documents_traditional(documents)
    
    def _process_documents_traditional(self, documents: List[Document]) -> List[Document]:
        """Process documents using traditional recursive character splitting."""
        processed_docs = []
        
        for doc in documents:
            try:
                # Clean text
                cleaned_text = self._clean_text(doc.page_content)
                doc.page_content = cleaned_text
                
                # Skip empty documents
                if not cleaned_text.strip():
                    continue
                
                # Split into chunks
                chunks = self.text_splitter.split_documents([doc])
                
                # Add chunk metadata
                for i, chunk in enumerate(chunks):
                    chunk.metadata.update({
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "chunk_size": len(chunk.page_content),
                        "chunking_method": "traditional"
                    })
                
                processed_docs.extend(chunks)
                
            except Exception as e:
                logger.warning(f"Failed to process document: {str(e)}")
                continue
        
        logger.info(f"Traditional chunking: Generated {len(processed_docs)} chunks from {len(documents)} documents")
        return processed_docs
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove null bytes and other problematic characters
        text = text.replace('\x00', '')
        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')
        
        # Remove excessive whitespace while preserving structure
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove trailing whitespace but keep leading whitespace for code structure
            cleaned_line = line.rstrip()
            cleaned_lines.append(cleaned_line)
        
        # Join lines and remove excessive blank lines
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Remove more than 3 consecutive newlines
        import re
        cleaned_text = re.sub(r'\n{4,}', '\n\n\n', cleaned_text)
        
        return cleaned_text.strip()
    
    def get_chunk_stats(self, documents: List[Document]) -> dict:
        """Get statistics about chunked documents"""
        if not documents:
            return {"total_chunks": 0, "avg_chunk_size": 0, "total_chars": 0}
        
        total_chars = sum(len(doc.page_content) for doc in documents)
        avg_chunk_size = total_chars / len(documents) if documents else 0
        
        # Enhanced statistics if using semantic chunking
        stats = {
            "total_chunks": len(documents),
            "avg_chunk_size": round(avg_chunk_size, 2),
            "total_chars": total_chars,
            "min_chunk_size": min(len(doc.page_content) for doc in documents),
            "max_chunk_size": max(len(doc.page_content) for doc in documents),
            "enhanced_chunking": self.use_enhanced_chunking
        }
        
        # Add semantic chunking statistics if available
        if self.use_enhanced_chunking:
            stats.update(self._get_semantic_stats(documents))
        
        return stats
    
    def _get_semantic_stats(self, documents: List[Document]) -> dict:
        """Get statistics specific to semantic chunking."""
        semantic_stats = {
            "chunk_types": {},
            "languages": {},
            "has_documentation": 0,
            "symbol_count": 0
        }
        
        for doc in documents:
            metadata = doc.metadata
            
            # Count chunk types
            chunk_type = metadata.get("chunk_type", "unknown")
            semantic_stats["chunk_types"][chunk_type] = semantic_stats["chunk_types"].get(chunk_type, 0) + 1
            
            # Count languages
            language = metadata.get("language", "unknown")
            semantic_stats["languages"][language] = semantic_stats["languages"].get(language, 0) + 1
            
            # Count documentation
            if metadata.get("contains_documentation", False):
                semantic_stats["has_documentation"] += 1
            
            # Count symbols
            symbols = metadata.get("symbols", [])
            if isinstance(symbols, list):
                semantic_stats["symbol_count"] += len(symbols)
        
        return semantic_stats
    
    def get_chunking_info(self) -> dict:
        """Get information about the current chunking configuration."""
        info = {
            "enhanced_chunking": self.use_enhanced_chunking,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap
        }
        
        if self.use_enhanced_chunking and self.chunking_factory:
            info.update({
                "supported_extensions": self.chunking_factory.get_supported_extensions(),
                "chunker_info": self.chunking_factory.get_chunker_info()
            })
        
        return info
    
    def switch_chunking_mode(self, use_enhanced: bool) -> None:
        """Switch between enhanced and traditional chunking modes."""
        if use_enhanced and not self.chunking_factory:
            # Try to setup enhanced chunking
            self._setup_enhanced_chunking()
        
        self.use_enhanced_chunking = use_enhanced and self.chunking_factory is not None
        logger.info(f"Switched to {'enhanced' if self.use_enhanced_chunking else 'traditional'} chunking mode")
