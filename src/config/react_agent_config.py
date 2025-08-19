"""
ReAct Agent Configuration

Configuration settings for ReAct agent capabilities including tool usage,
action planning, and execution monitoring.
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field
from .rag_enhancement_config import RAGEnhancementConfig

class ReActAgentConfig(BaseModel):
    """Configuration for ReAct agent features"""
    
    # ReAct core settings
    max_iterations: int = Field(default=10, description="Maximum ReAct iterations")
    max_reasoning_steps: int = Field(default=8, description="Maximum reasoning steps per iteration")
    action_timeout: float = Field(default=30.0, description="Action execution timeout in seconds")
    
    # Tool usage settings
    enable_tool_usage: bool = Field(default=True, description="Enable tool usage capabilities")
    enable_action_planning: bool = Field(default=True, description="Enable action planning")
    enable_execution_monitoring: bool = Field(default=True, description="Enable execution monitoring")
    max_tool_calls_per_iteration: int = Field(default=3, description="Maximum tool calls per iteration")
    
    # Safety and validation settings
    safety_checks: bool = Field(default=True, description="Enable safety checks for actions")
    action_validation: bool = Field(default=True, description="Validate actions before execution")
    tool_parameter_validation: bool = Field(default=True, description="Validate tool parameters")
    
    # Reasoning settings
    reasoning_model: str = Field(default="chain_of_thought", description="Reasoning model to use")
    verbose_reasoning: bool = Field(default=True, description="Enable verbose reasoning output")
    enable_self_reflection: bool = Field(default=True, description="Enable self-reflection in reasoning")
    
    # Performance settings
    enable_caching: bool = Field(default=True, description="Enable action result caching")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    parallel_execution: bool = Field(default=False, description="Enable parallel action execution")
    
    # Debug settings
    log_actions: bool = Field(default=True, description="Log all actions for debugging")
    log_reasoning: bool = Field(default=True, description="Log reasoning steps for debugging")
    enable_metrics: bool = Field(default=True, description="Enable performance metrics collection")

class ReActToolConfig(BaseModel):
    """Configuration for individual tools"""
    
    name: str
    enabled: bool = Field(default=True, description="Whether the tool is enabled")
    max_calls_per_minute: int = Field(default=60, description="Rate limiting for tool calls")
    timeout: float = Field(default=30.0, description="Tool-specific timeout")
    retry_count: int = Field(default=3, description="Number of retries on failure")
    safety_level: str = Field(default="medium", description="Safety level: low, medium, high")

# Default configuration
DEFAULT_REACT_CONFIG = ReActAgentConfig()

# Configuration presets
REACT_AGENT_PRESETS = {
    "basic": ReActAgentConfig(
        max_iterations=5,
        max_reasoning_steps=4,
        enable_tool_usage=True,
        enable_action_planning=True,
        enable_execution_monitoring=False,
        safety_checks=True,
        verbose_reasoning=False
    ),
    "standard": ReActAgentConfig(),  # Default settings
    "advanced": ReActAgentConfig(
        max_iterations=15,
        max_reasoning_steps=12,
        enable_tool_usage=True,
        enable_action_planning=True,
        enable_execution_monitoring=True,
        safety_checks=True,
        verbose_reasoning=True,
        enable_self_reflection=True,
        parallel_execution=True
    ),
    "performance": ReActAgentConfig(
        max_iterations=8,
        max_reasoning_steps=6,
        enable_tool_usage=True,
        enable_action_planning=True,
        enable_execution_monitoring=False,
        safety_checks=False,
        verbose_reasoning=False,
        enable_caching=True,
        cache_ttl=7200
    ),
    "safety": ReActAgentConfig(
        max_iterations=6,
        max_reasoning_steps=5,
        enable_tool_usage=True,
        enable_action_planning=True,
        enable_execution_monitoring=True,
        safety_checks=True,
        action_validation=True,
        tool_parameter_validation=True,
        verbose_reasoning=True
    )
}

def get_react_config(preset: str = "standard") -> ReActAgentConfig:
    """Get ReAct agent configuration by preset name"""
    if preset not in REACT_AGENT_PRESETS:
        raise ValueError(f"Invalid preset: {preset}. Valid presets: {list(REACT_AGENT_PRESETS.keys())}")
    
    return REACT_AGENT_PRESETS[preset]

def get_react_config_dict(preset: str = "standard") -> Dict[str, Any]:
    """Get ReAct agent configuration as dictionary by preset name"""
    config = get_react_config(preset)
    return config.dict()

def validate_react_config(config_dict: Dict[str, Any]) -> ReActAgentConfig:
    """Validate and create ReAct agent configuration from dictionary"""
    try:
        return ReActAgentConfig(**config_dict)
    except Exception as e:
        raise ValueError(f"Invalid ReAct agent configuration: {str(e)}")

def create_combined_config(rag_preset: str = "standard", react_preset: str = "standard") -> Dict[str, Any]:
    """Create combined configuration for RAG enhancement and ReAct capabilities"""
    rag_config = get_react_config(rag_preset).dict()
    react_config = get_react_config(react_preset).dict()
    
    return {
        "rag_enhancement": rag_config,
        "react_agent": react_config
    }
