"""
Query Optimization Configuration

Configuration settings for advanced query optimization capabilities including
semantic analysis, query rewriting, and multi-query strategies.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field

class QueryOptimizationConfig(BaseModel):
    """Configuration for query optimization features"""
    
    # Semantic analysis settings
    enable_semantic_analysis: bool = Field(default=True, description="Enable semantic query analysis")
    enable_intent_detection: bool = Field(default=True, description="Enable query intent detection")
    enable_domain_classification: bool = Field(default=True, description="Enable domain classification")
    enable_complexity_assessment: bool = Field(default=True, description="Enable complexity assessment")
    
    # Query expansion settings
    enable_query_expansion: bool = Field(default=True, description="Enable query expansion")
    enable_synonym_replacement: bool = Field(default=True, description="Enable synonym replacement")
    enable_context_enhancement: bool = Field(default=True, description="Enable context-based enhancement")
    max_expansion_queries: int = Field(default=3, description="Maximum number of expansion queries")
    
    # Query rewriting settings
    enable_query_rewriting: bool = Field(default=True, description="Enable query rewriting")
    enable_semantic_rewriting: bool = Field(default=True, description="Enable semantic rewriting")
    enable_pattern_rewriting: bool = Field(default=True, description="Enable pattern-based rewriting")
    enable_intent_based_rewriting: bool = Field(default=True, description="Enable intent-based rewriting")
    
    # Query decomposition settings
    enable_query_decomposition: bool = Field(default=True, description="Enable query decomposition")
    enable_complexity_based_decomposition: bool = Field(default=True, description="Enable complexity-based decomposition")
    enable_intent_based_decomposition: bool = Field(default=True, description="Enable intent-based decomposition")
    max_decomposition_queries: int = Field(default=5, description="Maximum number of decomposed queries")
    
    # Multi-query strategy settings
    enable_multi_query_strategies: bool = Field(default=True, description="Enable multi-query strategies")
    enable_strategy_combination: bool = Field(default=True, description="Enable strategy combination")
    enable_adaptive_strategy_selection: bool = Field(default=True, description="Enable adaptive strategy selection")
    
    # Performance settings
    optimization_timeout: float = Field(default=10.0, description="Query optimization timeout in seconds")
    enable_caching: bool = Field(default=True, description="Enable optimization result caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    max_concurrent_optimizations: int = Field(default=5, description="Maximum concurrent optimizations")
    
    # Quality settings
    confidence_threshold: float = Field(default=0.7, description="Minimum confidence threshold for optimization")
    enable_quality_validation: bool = Field(default=True, description="Enable optimization quality validation")
    enable_fallback_strategies: bool = Field(default=True, description="Enable fallback optimization strategies")
    
    # Debug settings
    verbose_logging: bool = Field(default=False, description="Enable verbose logging for debugging")
    log_optimization_steps: bool = Field(default=True, description="Log optimization steps for analysis")
    enable_metrics_collection: bool = Field(default=True, description="Enable optimization metrics collection")

class SemanticAnalysisConfig(BaseModel):
    """Configuration for semantic query analysis"""
    
    # Query type detection
    enable_query_type_detection: bool = Field(default=True, description="Enable query type detection")
    supported_query_types: List[str] = Field(default=[
        "factual", "analytical", "comparative", "procedural", "exploratory", "troubleshooting"
    ], description="Supported query types")
    
    # Complexity assessment
    enable_complexity_assessment: bool = Field(default=True, description="Enable complexity assessment")
    complexity_thresholds: Dict[str, int] = Field(default={
        "low": 5,
        "medium": 10,
        "high": 15
    }, description="Word count thresholds for complexity levels")
    
    # Intent detection
    enable_intent_detection: bool = Field(default=True, description="Enable intent detection")
    supported_intents: List[str] = Field(default=[
        "instruction", "information", "comparison", "solution", "general"
    ], description="Supported query intents")
    
    # Domain classification
    enable_domain_classification: bool = Field(default=True, description="Enable domain classification")
    supported_domains: List[str] = Field(default=[
        "code_analysis", "configuration", "architecture", "performance", "security", "general"
    ], description="Supported query domains")

class QueryExpansionConfig(BaseModel):
    """Configuration for query expansion strategies"""
    
    # Synonym replacement
    enable_synonym_replacement: bool = Field(default=True, description="Enable synonym replacement")
    synonym_dictionary_path: str = Field(default="", description="Path to synonym dictionary file")
    max_synonym_expansions: int = Field(default=3, description="Maximum synonym expansions per query")
    
    # Context enhancement
    enable_context_enhancement: bool = Field(default=True, description="Enable context enhancement")
    context_keywords_path: str = Field(default="", description="Path to context keywords file")
    max_context_expansions: int = Field(default=2, description="Maximum context expansions per query")
    
    # Query patterns
    enable_pattern_based_expansion: bool = Field(default=True, description="Enable pattern-based expansion")
    query_patterns_path: str = Field(default="", description="Path to query patterns file")

class QueryRewritingConfig(BaseModel):
    """Configuration for query rewriting strategies"""
    
    # Semantic rewriting
    enable_semantic_rewriting: bool = Field(default=True, description="Enable semantic rewriting")
    enable_intent_based_rewriting: bool = Field(default=True, description="Enable intent-based rewriting")
    enable_domain_based_rewriting: bool = Field(default=True, description="Enable domain-based rewriting")
    
    # Pattern rewriting
    enable_pattern_rewriting: bool = Field(default=True, description="Enable pattern-based rewriting")
    pattern_rules_path: str = Field(default="", description="Path to pattern rules file")
    
    # Quality control
    enable_rewriting_validation: bool = Field(default=True, description="Enable rewriting validation")
    min_rewriting_confidence: float = Field(default=0.6, description="Minimum confidence for rewriting")

class QueryDecompositionConfig(BaseModel):
    """Configuration for query decomposition strategies"""
    
    # Complexity-based decomposition
    enable_complexity_based_decomposition: bool = Field(default=True, description="Enable complexity-based decomposition")
    complexity_decomposition_threshold: int = Field(default=10, description="Word count threshold for decomposition")
    
    # Intent-based decomposition
    enable_intent_based_decomposition: bool = Field(default=True, description="Enable intent-based decomposition")
    enable_comparison_decomposition: bool = Field(default=True, description="Enable comparison query decomposition")
    
    # Quality control
    enable_decomposition_validation: bool = Field(default=True, description="Enable decomposition validation")
    min_decomposition_confidence: float = Field(default=0.7, description="Minimum confidence for decomposition")

# Default configuration
DEFAULT_QUERY_OPTIMIZATION_CONFIG = QueryOptimizationConfig()

# Configuration presets
QUERY_OPTIMIZATION_PRESETS = {
    "basic": QueryOptimizationConfig(
        enable_semantic_analysis=True,
        enable_query_expansion=True,
        enable_query_rewriting=True,
        enable_query_decomposition=False,
        enable_multi_query_strategies=False,
        max_expansion_queries=2,
        confidence_threshold=0.6
    ),
    "standard": QueryOptimizationConfig(),  # Default settings
    "advanced": QueryOptimizationConfig(
        enable_semantic_analysis=True,
        enable_query_expansion=True,
        enable_query_rewriting=True,
        enable_query_decomposition=True,
        enable_multi_query_strategies=True,
        enable_strategy_combination=True,
        enable_adaptive_strategy_selection=True,
        max_expansion_queries=5,
        max_decomposition_queries=8,
        confidence_threshold=0.8,
        enable_quality_validation=True,
        enable_fallback_strategies=True
    ),
    "performance": QueryOptimizationConfig(
        enable_semantic_analysis=True,
        enable_query_expansion=True,
        enable_query_rewriting=True,
        enable_query_decomposition=False,
        enable_multi_query_strategies=False,
        max_expansion_queries=2,
        optimization_timeout=5.0,
        enable_caching=True,
        cache_ttl=7200
    ),
    "quality": QueryOptimizationConfig(
        enable_semantic_analysis=True,
        enable_query_expansion=True,
        enable_query_rewriting=True,
        enable_query_decomposition=True,
        enable_multi_query_strategies=True,
        enable_quality_validation=True,
        enable_fallback_strategies=True,
        confidence_threshold=0.9,
        max_expansion_queries=5,
        max_decomposition_queries=10
    )
}

def get_query_optimization_config(preset: str = "standard") -> QueryOptimizationConfig:
    """Get query optimization configuration by preset name"""
    if preset not in QUERY_OPTIMIZATION_PRESETS:
        raise ValueError(f"Invalid preset: {preset}. Valid presets: {list(QUERY_OPTIMIZATION_PRESETS.keys())}")
    
    return QUERY_OPTIMIZATION_PRESETS[preset]

def get_query_optimization_config_dict(preset: str = "standard") -> Dict[str, Any]:
    """Get query optimization configuration as dictionary by preset name"""
    config = get_query_optimization_config(preset)
    return config.dict()

def validate_query_optimization_config(config_dict: Dict[str, Any]) -> QueryOptimizationConfig:
    """Validate and create query optimization configuration from dictionary"""
    try:
        return QueryOptimizationConfig(**config_dict)
    except Exception as e:
        raise ValueError(f"Invalid query optimization configuration: {str(e)}")

def create_combined_config(rag_preset: str = "standard", react_preset: str = "standard", 
                          query_opt_preset: str = "standard") -> Dict[str, Any]:
    """Create combined configuration for RAG enhancement, ReAct, and query optimization"""
    from .rag_enhancement_config import get_rag_enhancement_config
    from .react_agent_config import get_react_config
    
    rag_config = get_rag_enhancement_config(rag_preset).dict()
    react_config = get_react_config(react_preset).dict()
    query_opt_config = get_query_optimization_config(query_opt_preset).dict()
    
    return {
        "rag_enhancement": rag_config,
        "react_agent": react_config,
        "query_optimization": query_opt_config
    }
