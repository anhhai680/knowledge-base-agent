"""
RAG Enhancement Configuration

Configuration settings for advanced RAG capabilities including Chain-of-Thought reasoning,
context refinement, and response quality enhancement.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field

class RAGEnhancementConfig(BaseModel):
    """Configuration for RAG enhancement features"""
    
    # Chain-of-Thought settings
    max_reasoning_steps: int = Field(default=5, description="Maximum reasoning steps for complex queries")
    reasoning_transparency: bool = Field(default=True, description="Show reasoning steps to users")
    
    # Context refinement settings
    max_refinement_iterations: int = Field(default=3, description="Maximum context refinement iterations")
    quality_threshold: float = Field(default=0.8, description="Context quality threshold (0.0-1.0)")
    context_optimization: bool = Field(default=True, description="Enable context optimization")
    
    # Response quality settings
    max_enhancement_iterations: int = Field(default=2, description="Maximum response enhancement iterations")
    quality_validation: bool = Field(default=True, description="Enable response quality validation")
    response_improvement: bool = Field(default=True, description="Enable response improvement")
    
    # Query analysis settings
    intent_classification: bool = Field(default=True, description="Enable query intent classification")
    query_optimization: bool = Field(default=True, description="Enable query optimization")
    dynamic_retrieval: bool = Field(default=True, description="Enable dynamic retrieval strategies")
    
    # Performance settings
    enable_caching: bool = Field(default=True, description="Enable response caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    
    # Debug settings
    verbose_logging: bool = Field(default=False, description="Enable verbose logging for debugging")
    log_reasoning_steps: bool = Field(default=True, description="Log reasoning steps for analysis")

# Default configuration
DEFAULT_RAG_ENHANCEMENT_CONFIG = RAGEnhancementConfig()

# Configuration presets
RAG_ENHANCEMENT_PRESETS = {
    "basic": RAGEnhancementConfig(
        max_reasoning_steps=3,
        reasoning_transparency=False,
        max_refinement_iterations=1,
        quality_threshold=0.6,
        max_enhancement_iterations=1
    ),
    "standard": RAGEnhancementConfig(),  # Default settings
    "advanced": RAGEnhancementConfig(
        max_reasoning_steps=8,
        reasoning_transparency=True,
        max_refinement_iterations=5,
        quality_threshold=0.9,
        max_enhancement_iterations=3,
        verbose_logging=True
    ),
    "performance": RAGEnhancementConfig(
        max_reasoning_steps=3,
        reasoning_transparency=False,
        max_refinement_iterations=2,
        quality_threshold=0.7,
        max_enhancement_iterations=1,
        enable_caching=True,
        cache_ttl=7200
    )
}

def get_enhancement_config(preset: str = "standard") -> RAGEnhancementConfig:
    """Get enhancement configuration by preset name"""
    if preset not in RAG_ENHANCEMENT_PRESETS:
        raise ValueError(f"Invalid preset: {preset}. Valid presets: {list(RAG_ENHANCEMENT_PRESETS.keys())}")
    
    return RAG_ENHANCEMENT_PRESETS[preset]

def get_enhancement_config_dict(preset: str = "standard") -> Dict[str, Any]:
    """Get enhancement configuration as dictionary by preset name"""
    config = get_enhancement_config(preset)
    return config.dict()

def validate_enhancement_config(config_dict: Dict[str, Any]) -> RAGEnhancementConfig:
    """Validate and create enhancement configuration from dictionary"""
    try:
        return RAGEnhancementConfig(**config_dict)
    except Exception as e:
        raise ValueError(f"Invalid enhancement configuration: {str(e)}")
