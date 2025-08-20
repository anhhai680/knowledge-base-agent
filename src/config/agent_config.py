"""
Agent Configuration - Configuration for agent routing and selection

This module provides configuration settings for agent routing, including
agent selection preferences and backward compatibility options.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum

class DiagramAgentType(str, Enum):
    """Available diagram agent types"""
    DIAGRAM_HANDLER = "diagram_handler"  # Legacy DiagramHandler
    DIAGRAM_AGENT = "diagram_agent"      # New DiagramAgent
    AUTO = "auto"                        # Intelligent selection based on query complexity

class AgentRoutingConfig(BaseModel):
    """Configuration for agent routing and selection"""
    
    # Diagram agent selection
    preferred_diagram_agent: DiagramAgentType = Field(
        default=DiagramAgentType.DIAGRAM_HANDLER,
        description="Preferred diagram agent for routing"
    )
    
    # Fallback configuration
    enable_agent_fallback: bool = Field(
        default=True,
        description="Enable fallback to alternative agent if primary fails"
    )
    
    # Auto-selection criteria
    auto_selection_enabled: bool = Field(
        default=True,
        description="Enable intelligent agent selection based on query complexity"
    )
    
    # Query complexity thresholds for auto-selection
    complex_query_keywords: List[str] = Field(
        default=[
            "flowchart", "class diagram", "component diagram", "er diagram",
            "multiple", "architecture", "system design", "relationships"
        ],
        description="Keywords that indicate complex diagram requests requiring DiagramAgent"
    )
    
    # Backward compatibility
    maintain_legacy_compatibility: bool = Field(
        default=True,
        description="Maintain compatibility with legacy DiagramHandler interface"
    )
    
    # Performance settings
    agent_timeout_seconds: float = Field(
        default=30.0,
        description="Timeout for agent operations in seconds"
    )
    
    # Experimental features
    enable_enhanced_code_retrieval: bool = Field(
        default=True,
        description="Enable enhanced code retrieval in DiagramAgent"
    )
    
    enable_multi_diagram_types: bool = Field(
        default=True,
        description="Enable multiple diagram type support in DiagramAgent"
    )

class AgentConfig(BaseModel):
    """Overall agent configuration"""
    
    # Routing configuration
    routing: AgentRoutingConfig = Field(default_factory=AgentRoutingConfig)
    
    # Agent initialization settings
    initialize_diagram_agent: bool = Field(
        default=True,
        description="Initialize DiagramAgent alongside DiagramHandler"
    )
    
    # Migration settings
    migration_mode: bool = Field(
        default=False,
        description="Enable migration mode for gradual transition to new agents"
    )

# Default configuration
DEFAULT_AGENT_CONFIG = AgentConfig()

# Configuration presets
AGENT_CONFIG_PRESETS = {
    "legacy": AgentConfig(
        routing=AgentRoutingConfig(
            preferred_diagram_agent=DiagramAgentType.DIAGRAM_HANDLER,
            auto_selection_enabled=False,
            enable_enhanced_code_retrieval=False,
            enable_multi_diagram_types=False
        ),
        initialize_diagram_agent=False
    ),
    "modern": AgentConfig(
        routing=AgentRoutingConfig(
            preferred_diagram_agent=DiagramAgentType.DIAGRAM_AGENT,
            auto_selection_enabled=True,
            enable_enhanced_code_retrieval=True,
            enable_multi_diagram_types=True
        ),
        initialize_diagram_agent=True
    ),
    "hybrid": AgentConfig(
        routing=AgentRoutingConfig(
            preferred_diagram_agent=DiagramAgentType.AUTO,
            auto_selection_enabled=True,
            enable_agent_fallback=True,
            enable_enhanced_code_retrieval=True,
            enable_multi_diagram_types=True
        ),
        initialize_diagram_agent=True,
        migration_mode=True
    )
}