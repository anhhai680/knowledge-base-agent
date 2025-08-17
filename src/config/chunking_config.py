"""
Configuration management for enhanced chunking strategies.

This module provides configuration management for different chunking strategies,
including language-specific settings, timeout configurations, and safety limits.
"""

import os
import yaml
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path

from ..utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ChunkingStrategyConfig:
    """Configuration for a specific chunking strategy."""
    
    # Basic chunking parameters
    max_chunk_size: int = 1500
    chunk_overlap: int = 100
    
    # Safety and timeout parameters
    max_parse_time_seconds: int = 30
    max_recursion_depth: int = 100
    max_elements_per_file: int = 1000
    max_documents_per_batch: int = 1000
    
    # Chunking behavior
    preserve_imports: bool = True
    preserve_docstrings: bool = True
    preserve_class_methods: bool = True
    group_related_functions: bool = True
    
    # Language-specific features
    extract_types: bool = True
    extract_decorators: bool = True
    extract_comments: bool = False
    handle_jsx: bool = True
    
    # Performance tuning
    enable_caching: bool = True
    max_cache_size: int = 1000
    cleanup_interval: int = 300  # seconds


@dataclass
class ChunkingConfig:
    """Main configuration for the chunking system."""
    
    # Global settings
    default_strategy: str = "fallback"
    enable_enhanced_chunking: bool = True
    fallback_to_traditional: bool = True
    
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
    
    # Strategies configuration
    strategies: Dict[str, ChunkingStrategyConfig] = field(default_factory=dict)
    
    # Fallback configuration
    fallback: ChunkingStrategyConfig = field(default_factory=lambda: ChunkingStrategyConfig())


class ChunkingConfigManager:
    """Manages chunking configuration with safety defaults."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> ChunkingConfig:
        """Load configuration from file or use defaults."""
        if not self.config_path or not os.path.exists(self.config_path):
            logger.info("No configuration file found, using default safety settings")
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Convert to ChunkingConfig object
            config = ChunkingConfig(**config_data)
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
            
        except Exception as e:
            logger.warning(f"Failed to load configuration from {self.config_path}: {e}")
            logger.info("Using default safety settings")
            return self._get_default_config()
    
    def _get_default_config(self) -> ChunkingConfig:
        """Get default configuration with safety settings."""
        config = ChunkingConfig()
        
        # Configure strategies with safety defaults
        config.strategies = {
            '.py': ChunkingStrategyConfig(
                max_chunk_size=1500,
                chunk_overlap=100,
                max_parse_time_seconds=30,
                max_recursion_depth=100,
                max_elements_per_file=1000
            ),
            '.js': ChunkingStrategyConfig(
                max_chunk_size=1500,
                chunk_overlap=100,
                max_parse_time_seconds=30,
                max_recursion_depth=100,
                max_elements_per_file=1000,
                handle_jsx=True
            ),
            '.ts': ChunkingStrategyConfig(
                max_chunk_size=1500,
                chunk_overlap=100,
                max_parse_time_seconds=30,
                max_recursion_depth=100,
                max_elements_per_file=1000,
                extract_types=True,
                handle_jsx=True
            ),
            '.cs': ChunkingStrategyConfig(
                max_chunk_size=1500,
                chunk_overlap=100,
                max_parse_time_seconds=30,
                max_recursion_depth=100,
                max_elements_per_file=1000
            ),
            '.md': ChunkingStrategyConfig(
                max_chunk_size=1500,
                chunk_overlap=100,
                max_parse_time_seconds=15,
                max_recursion_depth=50,
                max_elements_per_file=500
            )
        }
        
        return config
    
    def _validate_config(self) -> None:
        """Validate configuration values and apply safety limits."""
        # Ensure timeouts are reasonable
        if self.config.global_timeout_seconds > 1800:  # 30 minutes max
            logger.warning("Global timeout too high, limiting to 30 minutes")
            self.config.global_timeout_seconds = 1800
        
        if self.config.chunking_timeout_seconds > 300:  # 5 minutes max
            logger.warning("Chunking timeout too high, limiting to 5 minutes")
            self.config.chunking_timeout_seconds = 300
        
        if self.config.parsing_timeout_seconds > 120:  # 2 minutes max
            logger.warning("Parsing timeout too high, limiting to 2 minutes")
            self.config.parsing_timeout_seconds = 120
        
        # Ensure memory limits are reasonable
        if self.config.max_memory_usage_mb > 4096:  # 4GB max
            logger.warning("Memory limit too high, limiting to 4GB")
            self.config.max_memory_usage_mb = 4096
        
        # Validate strategy configurations
        for ext, strategy in self.config.strategies.items():
            if strategy.max_parse_time_seconds > self.config.parsing_timeout_seconds:
                logger.warning(f"Strategy {ext} parse timeout too high, limiting to {self.config.parsing_timeout_seconds}s")
                strategy.max_parse_time_seconds = self.config.parsing_timeout_seconds
            
            if strategy.max_recursion_depth > 200:
                logger.warning(f"Strategy {ext} recursion depth too high, limiting to 200")
                strategy.max_recursion_depth = 200
            
            if strategy.max_elements_per_file > 2000:
                logger.warning(f"Strategy {ext} max elements too high, limiting to 2000")
                strategy.max_elements_per_file = 2000
    
    def get_config(self) -> ChunkingConfig:
        """Get the current configuration."""
        return self.config
    
    def get_strategy_config(self, file_extension: str) -> Optional[ChunkingStrategyConfig]:
        """Get configuration for a specific file extension."""
        return self.config.strategies.get(file_extension)
    
    def get_global_timeout(self) -> int:
        """Get the global timeout setting."""
        return self.config.global_timeout_seconds
    
    def get_chunking_timeout(self) -> int:
        """Get the chunking timeout setting."""
        return self.config.chunking_timeout_seconds
    
    def get_parsing_timeout(self) -> int:
        """Get the parsing timeout setting."""
        return self.config.parsing_timeout_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "default_strategy": self.config.default_strategy,
            "enable_enhanced_chunking": self.config.enable_enhanced_chunking,
            "fallback_to_traditional": self.config.fallback_to_traditional,
            "global_timeout_seconds": self.config.global_timeout_seconds,
            "chunking_timeout_seconds": self.config.chunking_timeout_seconds,
            "parsing_timeout_seconds": self.config.parsing_timeout_seconds,
            "max_memory_usage_mb": self.config.max_memory_usage_mb,
            "max_concurrent_operations": self.config.max_concurrent_operations,
            "max_file_size_mb": self.config.max_file_size_mb,
            "max_consecutive_failures": self.config.max_consecutive_failures,
            "retry_attempts": self.config.retry_attempts,
            "exponential_backoff": self.config.exponential_backoff,
            "strategies": {
                ext: {
                    "max_chunk_size": strategy.max_chunk_size,
                    "chunk_overlap": strategy.chunk_overlap,
                    "max_parse_time_seconds": strategy.max_parse_time_seconds,
                    "max_recursion_depth": strategy.max_recursion_depth,
                    "max_elements_per_file": strategy.max_elements_per_file,
                    "preserve_imports": strategy.preserve_imports,
                    "preserve_docstrings": strategy.preserve_docstrings,
                    "preserve_class_methods": strategy.preserve_class_methods,
                    "group_related_functions": strategy.group_related_functions,
                    "extract_types": strategy.extract_types,
                    "extract_decorators": strategy.extract_decorators,
                    "extract_comments": strategy.extract_comments,
                    "handle_jsx": strategy.handle_jsx
                }
                for ext, strategy in self.config.strategies.items()
            },
            "fallback": {
                "max_chunk_size": self.config.fallback.max_chunk_size,
                "chunk_overlap": self.config.fallback.chunk_overlap,
                "max_parse_time_seconds": self.config.fallback.max_parse_time_seconds,
                "max_recursion_depth": self.config.fallback.max_recursion_depth,
                "max_elements_per_file": self.config.fallback.max_elements_per_file
            }
        }
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        try:
            # Update main config
            for key, value in new_config.items():
                if hasattr(self.config, key) and key != 'strategies':
                    setattr(self.config, key, value)
            
            # Update strategies
            if 'strategies' in new_config:
                for ext, strategy_config in new_config['strategies'].items():
                    if ext in self.config.strategies:
                        for key, value in strategy_config.items():
                            if hasattr(self.config.strategies[ext], key):
                                setattr(self.config.strategies[ext], key, value)
            
            # Validate updated config
            self._validate_config()
            
            logger.info("Configuration updated successfully")
            
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
    
    def save_config(self, output_path: Optional[str] = None) -> None:
        """Save current configuration to file."""
        try:
            save_path = output_path or self.config_path
            if not save_path:
                logger.warning("No output path specified for configuration save")
                return
            
            # Ensure directory exists
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'w') as f:
                yaml.dump(self.to_dict(), f, default_flow_style=False, indent=2)
            
            logger.info(f"Configuration saved to {save_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def get_safety_summary(self) -> Dict[str, Any]:
        """Get a summary of safety settings."""
        return {
            "timeouts": {
                "global": f"{self.config.global_timeout_seconds}s",
                "chunking": f"{self.config.chunking_timeout_seconds}s",
                "parsing": f"{self.config.parsing_timeout_seconds}s"
            },
            "limits": {
                "memory_mb": self.config.max_memory_usage_mb,
                "concurrent_ops": self.config.max_concurrent_operations,
                "file_size_mb": self.config.max_file_size_mb,
                "consecutive_failures": self.config.max_consecutive_failures
            },
            "strategies": {
                ext: {
                    "parse_timeout": f"{strategy.max_parse_time_seconds}s",
                    "recursion_depth": strategy.max_recursion_depth,
                    "max_elements": strategy.max_elements_per_file
                }
                for ext, strategy in self.config.strategies.items()
            }
        }
