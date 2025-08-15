"""
Chunking strategies for different file types.

This package provides intelligent chunking based on file extensions and content type,
maintaining semantic boundaries for programming languages and other structured content.
"""

from .base_chunker import BaseChunker
from .chunking_factory import ChunkingFactory
from .python_chunker import PythonChunker
from .csharp_chunker import CSharpChunker
from .javascript_chunker import JavaScriptChunker
from .typescript_chunker import TypeScriptChunker
from .fallback_chunker import FallbackChunker
from .markdown_chunker import MarkdownChunker

__all__ = [
    'BaseChunker',
    'ChunkingFactory', 
    'PythonChunker',
    'CSharpChunker',
    'JavaScriptChunker',
    'TypeScriptChunker',
    'FallbackChunker',
    'MarkdownChunker'
]
