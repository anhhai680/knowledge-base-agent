"""
Configuration system for chunking strategies.

This module provides configuration management for different chunking strategies,
allowing customization of chunking parameters per file type.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import yaml
import os
import sys
import os.path

# Add the parent directory to the path to import from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logging import get_logger

logger = get_logger(__name__)


class ChunkingStrategyConfig(BaseModel):
    """Configuration for a specific chunking strategy."""
    
    max_chunk_size: int = Field(default=1000, ge=100, le=8000)  # Reduced max to prevent token overflow
    chunk_overlap: int = Field(default=100, ge=0, le=1000)
    preserve_methods: bool = Field(default=True)
    preserve_classes: bool = Field(default=True)
    include_imports: bool = Field(default=True)
    include_docstrings: bool = Field(default=True)
    respect_indentation: bool = Field(default=True)


class FallbackConfig(BaseModel):
    """Configuration for fallback chunking strategy."""
    
    chunk_size: int = Field(default=800, ge=100, le=8000)  # Reduced from 1000 to be more conservative
    chunk_overlap: int = Field(default=160, ge=0, le=1000)  # Adjusted proportionally


class ChunkingConfig(BaseModel):
    """Main configuration for chunking system."""
    
    strategies: Dict[str, ChunkingStrategyConfig] = Field(default_factory=dict)
    fallback: FallbackConfig = Field(default_factory=FallbackConfig)
    
    # Global settings
    enabled: bool = Field(default=True)
    use_ast_parsing: bool = Field(default=True)
    max_file_size_mb: int = Field(default=10)


class ChunkingConfigManager:
    """Manager for chunking configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self._config = self._load_default_config()
        
        # Load from file if provided
        if config_path and os.path.exists(config_path):
            self.load_from_file(config_path)
    
    def _load_default_config(self) -> ChunkingConfig:
        """Load default configuration."""
        default_strategies = {
            '.py': ChunkingStrategyConfig(
                max_chunk_size=1500,
                chunk_overlap=100,
                preserve_methods=True,
                preserve_classes=True,
                include_imports=True,
                include_docstrings=True
            ),
            '.cs': ChunkingStrategyConfig(
                max_chunk_size=2000,
                chunk_overlap=50,
                preserve_methods=True,
                preserve_classes=True,
                include_imports=True,
                include_docstrings=True
            ),
            '.js': ChunkingStrategyConfig(
                max_chunk_size=1500,
                chunk_overlap=75,
                preserve_methods=True,
                preserve_classes=True,
                include_imports=True,
                include_docstrings=False
            ),
            '.ts': ChunkingStrategyConfig(
                max_chunk_size=1500,
                chunk_overlap=75,
                preserve_methods=True,
                preserve_classes=True,
                include_imports=True,
                include_docstrings=True
            ),
            '.md': ChunkingStrategyConfig(
                max_chunk_size=6000,  # Increased from 4000 since MarkdownTextSplitter handles large chunks better
                chunk_overlap=400,     # Increased from 200 for better context preservation
                preserve_methods=False,
                preserve_classes=False,
                include_imports=False,
                include_docstrings=False
            ),
            '.java': ChunkingStrategyConfig(
                max_chunk_size=2000,
                chunk_overlap=75,
                preserve_methods=True,
                preserve_classes=True,
                include_imports=True,
                include_docstrings=True
            )
        }
        
        return ChunkingConfig(
            strategies=default_strategies,
            fallback=FallbackConfig()
        )
    
    def load_from_file(self, config_path: str) -> None:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to configuration file
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if 'chunking' in config_data:
                config_data = config_data['chunking']
            
            # Parse strategies
            strategies = {}
            if 'strategies' in config_data:
                for ext, strategy_data in config_data['strategies'].items():
                    strategies[ext] = ChunkingStrategyConfig(**strategy_data)
            
            # Parse fallback
            fallback = FallbackConfig()
            if 'fallback' in config_data:
                fallback = FallbackConfig(**config_data['fallback'])
            
            # Create new config
            self._config = ChunkingConfig(
                strategies=strategies,
                fallback=fallback,
                enabled=config_data.get('enabled', True),
                use_ast_parsing=config_data.get('use_ast_parsing', True),
                max_file_size_mb=config_data.get('max_file_size_mb', 10)
            )
            
            logger.info(f"Loaded chunking configuration from {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load chunking configuration from {config_path}: {str(e)}")
            logger.info("Using default configuration")
    
    def get_config(self) -> ChunkingConfig:
        """Get current configuration."""
        return self._config
    
    def get_strategy_config(self, file_extension: str) -> Optional[ChunkingStrategyConfig]:
        """
        Get configuration for specific file extension.
        
        Args:
            file_extension: File extension (e.g., '.py')
            
        Returns:
            Strategy configuration or None if not found
        """
        return self._config.strategies.get(file_extension.lower())
    
    def get_fallback_config(self) -> FallbackConfig:
        """Get fallback configuration."""
        return self._config.fallback
    
    def update_strategy(self, file_extension: str, config: ChunkingStrategyConfig) -> None:
        """
        Update strategy configuration for file extension.
        
        Args:
            file_extension: File extension
            config: New strategy configuration
        """
        self._config.strategies[file_extension.lower()] = config
        logger.debug(f"Updated chunking strategy for {file_extension}")
    
    def save_to_file(self, config_path: str) -> None:
        """
        Save current configuration to file.
        
        Args:
            config_path: Path to save configuration
        """
        try:
            config_dict = {
                'chunking': {
                    'enabled': self._config.enabled,
                    'use_ast_parsing': self._config.use_ast_parsing,
                    'max_file_size_mb': self._config.max_file_size_mb,
                    'strategies': {
                        ext: strategy.dict()
                        for ext, strategy in self._config.strategies.items()
                    },
                    'fallback': self._config.fallback.dict()
                }
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            
            logger.info(f"Saved chunking configuration to {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save chunking configuration to {config_path}: {str(e)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'enabled': self._config.enabled,
            'use_ast_parsing': self._config.use_ast_parsing,
            'max_file_size_mb': self._config.max_file_size_mb,
            'strategies': {
                ext: strategy.model_dump()
                for ext, strategy in self._config.strategies.items()
            },
            'fallback': self._config.fallback.model_dump()
        }
