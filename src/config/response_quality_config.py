"""
Response Quality Configuration

Configuration settings for enhanced response quality capabilities including
fact-checking, consistency validation, and interactive elements.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field

class ResponseQualityConfig(BaseModel):
    """Configuration for response quality enhancement features"""
    
    # Fact-checking settings
    enable_fact_checking: bool = Field(default=True, description="Enable fact-checking and verification")
    enable_source_verification: bool = Field(default=True, description="Enable source document verification")
    fact_checking_threshold: float = Field(default=0.7, description="Minimum accuracy threshold for fact-checking")
    enable_factual_improvements: bool = Field(default=True, description="Enable factual accuracy improvements")
    
    # Consistency validation settings
    enable_consistency_validation: bool = Field(default=True, description="Enable response consistency validation")
    enable_contradiction_detection: bool = Field(default=True, description="Enable contradiction detection")
    consistency_threshold: float = Field(default=0.8, description="Minimum consistency threshold")
    enable_consistency_improvements: bool = Field(default=True, description="Enable consistency improvements")
    
    # Interactive elements settings
    enable_interactive_elements: bool = Field(default=True, description="Enable interactive response elements")
    enable_follow_up_suggestions: bool = Field(default=True, description="Enable follow-up question suggestions")
    enable_quality_indicators: bool = Field(default=True, description="Enable quality indicators")
    enable_enhancement_notes: bool = Field(default=True, description="Enable enhancement notes")
    
    # User feedback settings
    enable_user_feedback: bool = Field(default=True, description="Enable user feedback collection")
    enable_rating_system: bool = Field(default=True, description="Enable response rating system")
    enable_feedback_analysis: bool = Field(default=True, description="Enable feedback analysis")
    feedback_storage_enabled: bool = Field(default=True, description="Enable feedback storage")
    
    # Response improvement settings
    enable_response_improvement: bool = Field(default=True, description="Enable response quality improvements")
    enable_structure_enhancement: bool = Field(default=True, description="Enable response structure enhancement")
    enable_clarity_improvements: bool = Field(default=True, description="Enable clarity improvements")
    enable_relevance_enhancement: bool = Field(default=True, description="Enable relevance enhancement")
    
    # Quality assessment settings
    enable_quality_assessment: bool = Field(default=True, description="Enable comprehensive quality assessment")
    enable_confidence_scoring: bool = Field(default=True, description="Enable confidence scoring")
    enable_suggestion_generation: bool = Field(default=True, description="Enable improvement suggestions")
    quality_threshold: float = Field(default=0.8, description="Overall quality threshold")
    
    # Performance settings
    enhancement_timeout: float = Field(default=15.0, description="Response enhancement timeout in seconds")
    max_enhancement_iterations: int = Field(default=3, description="Maximum enhancement iterations")
    enable_caching: bool = Field(default=True, description="Enable enhancement result caching")
    cache_ttl: int = Field(default=1800, description="Cache TTL in seconds")
    
    # Debug settings
    verbose_logging: bool = Field(default=False, description="Enable verbose logging for debugging")
    log_enhancement_steps: bool = Field(default=True, description="Log enhancement steps for analysis")
    enable_metrics_collection: bool = Field(default=True, description="Enable enhancement metrics collection")

class FactCheckingConfig(BaseModel):
    """Configuration for fact-checking features"""
    
    # Verification settings
    enable_source_verification: bool = Field(default=True, description="Enable source document verification")
    enable_cross_reference: bool = Field(default=True, description="Enable cross-reference checking")
    enable_confidence_scoring: bool = Field(default=True, description="Enable confidence scoring for facts")
    
    # Thresholds
    accuracy_threshold: float = Field(default=0.7, description="Minimum accuracy threshold")
    confidence_threshold: float = Field(default=0.8, description="Minimum confidence threshold")
    
    # Improvement settings
    enable_automatic_corrections: bool = Field(default=True, description="Enable automatic fact corrections")
    enable_source_annotations: bool = Field(default=True, description="Enable source annotations")
    enable_verification_notes: bool = Field(default=True, description="Enable verification notes")

class ConsistencyValidationConfig(BaseModel):
    """Configuration for consistency validation features"""
    
    # Validation settings
    enable_internal_consistency: bool = Field(default=True, description="Enable internal consistency checking")
    enable_logical_flow: bool = Field(default=True, description="Enable logical flow validation")
    enable_contradiction_detection: bool = Field(default=True, description="Enable contradiction detection")
    
    # Thresholds
    consistency_threshold: float = Field(default=0.8, description="Minimum consistency threshold")
    flow_threshold: float = Field(default=0.7, description="Minimum logical flow threshold")
    
    # Improvement settings
    enable_automatic_corrections: bool = Field(default=True, description="Enable automatic consistency corrections")
    enable_consistency_notes: bool = Field(default=True, description="Enable consistency notes")

class InteractiveElementsConfig(BaseModel):
    """Configuration for interactive response elements"""
    
    # Element types
    enable_follow_up_questions: bool = Field(default=True, description="Enable follow-up question suggestions")
    enable_quality_indicators: bool = Field(default=True, description="Enable quality indicators")
    enable_enhancement_notes: bool = Field(default=True, description="Enable enhancement notes")
    enable_user_guidance: bool = Field(default=True, description="Enable user guidance elements")
    
    # Customization
    max_follow_up_questions: int = Field(default=3, description="Maximum follow-up questions")
    quality_indicator_style: str = Field(default="emoji", description="Quality indicator style")
    enable_custom_elements: bool = Field(default=True, description="Enable custom interactive elements")

class UserFeedbackConfig(BaseModel):
    """Configuration for user feedback features"""
    
    # Collection settings
    enable_rating_collection: bool = Field(default=True, description="Enable response rating collection")
    enable_text_feedback: bool = Field(default=True, description="Enable text feedback collection")
    enable_quality_metrics: bool = Field(default=True, description="Enable quality metric collection")
    
    # Rating system
    rating_scale: int = Field(default=5, description="Rating scale (1-5)")
    enable_rating_explanations: bool = Field(default=True, description="Enable rating explanations")
    
    # Storage and analysis
    enable_feedback_storage: bool = Field(default=True, description="Enable feedback storage")
    enable_feedback_analysis: bool = Field(default=True, description="Enable feedback analysis")
    feedback_retention_days: int = Field(default=365, description="Feedback retention period in days")

class ResponseImprovementConfig(BaseModel):
    """Configuration for response improvement features"""
    
    # Improvement types
    enable_structure_enhancement: bool = Field(default=True, description="Enable response structure enhancement")
    enable_clarity_improvements: bool = Field(default=True, description="Enable clarity improvements")
    enable_relevance_enhancement: bool = Field(default=True, description="Enable relevance enhancement")
    enable_completeness_improvements: bool = Field(default=True, description="Enable completeness improvements")
    
    # Enhancement settings
    enable_automatic_improvements: bool = Field(default=True, description="Enable automatic improvements")
    enable_improvement_notes: bool = Field(default=True, description="Enable improvement notes")
    max_improvement_iterations: int = Field(default=3, description="Maximum improvement iterations")

# Default configuration
DEFAULT_RESPONSE_QUALITY_CONFIG = ResponseQualityConfig()

# Configuration presets
RESPONSE_QUALITY_PRESETS = {
    "basic": ResponseQualityConfig(
        enable_fact_checking=True,
        enable_consistency_validation=True,
        enable_interactive_elements=False,
        enable_user_feedback=False,
        enable_response_improvement=False,
        quality_threshold=0.7
    ),
    "standard": ResponseQualityConfig(),  # Default settings
    "advanced": ResponseQualityConfig(
        enable_fact_checking=True,
        enable_consistency_validation=True,
        enable_interactive_elements=True,
        enable_user_feedback=True,
        enable_response_improvement=True,
        enable_confidence_scoring=True,
        enable_suggestion_generation=True,
        quality_threshold=0.9,
        max_enhancement_iterations=5
    ),
    "performance": ResponseQualityConfig(
        enable_fact_checking=True,
        enable_consistency_validation=True,
        enable_interactive_elements=False,
        enable_user_feedback=False,
        enable_response_improvement=True,
        enhancement_timeout=10.0,
        max_enhancement_iterations=2,
        enable_caching=True,
        cache_ttl=3600
    ),
    "quality": ResponseQualityConfig(
        enable_fact_checking=True,
        enable_consistency_validation=True,
        enable_interactive_elements=True,
        enable_user_feedback=True,
        enable_response_improvement=True,
        quality_threshold=0.95,
        max_enhancement_iterations=5,
        enable_confidence_scoring=True,
        enable_suggestion_generation=True
    )
}

def get_response_quality_config(preset: str = "standard") -> ResponseQualityConfig:
    """Get response quality configuration by preset name"""
    if preset not in RESPONSE_QUALITY_PRESETS:
        raise ValueError(f"Invalid preset: {preset}. Valid presets: {list(RESPONSE_QUALITY_PRESETS.keys())}")
    
    return RESPONSE_QUALITY_PRESETS[preset]

def get_response_quality_config_dict(preset: str = "standard") -> Dict[str, Any]:
    """Get response quality configuration as dictionary by preset name"""
    config = get_response_quality_config(preset)
    return config.dict()

def validate_response_quality_config(config_dict: Dict[str, Any]) -> ResponseQualityConfig:
    """Validate and create response quality configuration from dictionary"""
    try:
        return ResponseQualityConfig(**config_dict)
    except Exception as e:
        raise ValueError(f"Invalid response quality configuration: {str(e)}")

def create_combined_config(rag_preset: str = "standard", react_preset: str = "standard", 
                          query_opt_preset: str = "standard", response_quality_preset: str = "standard") -> Dict[str, Any]:
    """Create combined configuration for all RAG enhancement components"""
    from .rag_enhancement_config import get_rag_enhancement_config
    from .react_agent_config import get_react_config
    from .query_optimization_config import get_query_optimization_config
    
    rag_config = get_rag_enhancement_config(rag_preset).dict()
    react_config = get_react_config(react_preset).dict()
    query_opt_config = get_query_optimization_config(query_opt_preset).dict()
    response_quality_config = get_response_quality_config(response_quality_preset).dict()
    
    return {
        "rag_enhancement": rag_config,
        "react_agent": react_config,
        "query_optimization": query_opt_config,
        "response_quality": response_quality_config
    }
