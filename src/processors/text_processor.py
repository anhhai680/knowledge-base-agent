from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from typing import List
from ..utils.logging import get_logger

logger = get_logger(__name__)

class TextProcessor:
    """Text processing and chunking"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def process_documents(self, documents: List[Document]) -> List[Document]:
        """Process and chunk documents"""
        logger.info(f"Processing {len(documents)} documents")
        
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
                        "chunk_size": len(chunk.page_content)
                    })
                
                processed_docs.extend(chunks)
                
            except Exception as e:
                logger.warning(f"Failed to process document: {str(e)}")
                continue
        
        logger.info(f"Generated {len(processed_docs)} chunks from {len(documents)} documents")
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
        
        return {
            "total_chunks": len(documents),
            "avg_chunk_size": round(avg_chunk_size, 2),
            "total_chars": total_chars,
            "min_chunk_size": min(len(doc.page_content) for doc in documents),
            "max_chunk_size": max(len(doc.page_content) for doc in documents)
        }
