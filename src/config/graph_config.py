"""
LangGraph Configuration Module

This module provides configuration for LangGraph workflows, state management,
and migration settings. All configuration follows the parallel system approach
to ensure zero breaking changes during migration.
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
from enum import Enum


class WorkflowExecutionMode(str, Enum):
    """Workflow execution modes for LangGraph"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"


class CheckpointStrategy(str, Enum):
    """Checkpoint strategies for workflow persistence"""
    NONE = "none"
    PERIODIC = "periodic"
    ON_ERROR = "on_error"
    ALWAYS = "always"


class SystemSelector(str, Enum):
    """System selection for routing between LangChain and LangGraph"""
    LANGCHAIN = "langchain"
    LANGGRAPH = "langgraph"
    AUTO = "auto"  # Automatic selection based on feature flags


class GraphConfig(BaseModel):
    """Enhanced configuration for LangGraph workflows"""
    
    # System Selection and Migration
    enable_langgraph: bool = Field(default=False, description="Enable LangGraph system")
    default_system: SystemSelector = Field(default=SystemSelector.LANGCHAIN, description="Default system to use")
    migration_rollout_percentage: float = Field(default=0.0, ge=0.0, le=1.0, description="Percentage of traffic to route to LangGraph")
    enable_ab_testing: bool = Field(default=False, description="Enable A/B testing between systems")
    
    # Workflow Execution Settings
    enable_parallel_processing: bool = Field(default=True, description="Enable parallel workflow processing")
    max_concurrent_workflows: int = Field(default=10, ge=1, le=100, description="Maximum concurrent workflows")
    workflow_timeout_seconds: int = Field(default=300, ge=30, le=3600, description="Workflow timeout in seconds")
    default_execution_mode: WorkflowExecutionMode = Field(default=WorkflowExecutionMode.PARALLEL, description="Default execution mode")
    
    # State Management and Checkpointing
    checkpoint_strategy: CheckpointStrategy = Field(default=CheckpointStrategy.PERIODIC, description="Checkpoint strategy")
    checkpoint_frequency: int = Field(default=10, ge=1, le=100, description="Checkpoint every N steps")
    checkpoint_retention_days: int = Field(default=7, ge=1, le=30, description="Checkpoint retention period")
    enable_state_persistence: bool = Field(default=True, description="Enable workflow state persistence")
    
    # Workflow-Specific Settings
    chunking_parallel_workers: int = Field(default=4, ge=1, le=20, description="Parallel workers for chunking")
    embedding_parallel_workers: int = Field(default=2, ge=1, le=10, description="Parallel workers for embeddings")
    retrieval_parallel_workers: int = Field(default=3, ge=1, le=10, description="Parallel workers for retrieval")
    
    # Performance and Monitoring
    enable_workflow_caching: bool = Field(default=True, description="Enable workflow result caching")
    cache_ttl_seconds: int = Field(default=3600, ge=60, le=86400, description="Cache TTL in seconds")
    enable_performance_monitoring: bool = Field(default=True, description="Enable performance monitoring")
    enable_custom_metrics: bool = Field(default=True, description="Enable custom metrics collection")
    
    # Error Handling and Resilience
    enable_automatic_retry: bool = Field(default=True, description="Enable automatic retry on failures")
    max_retry_attempts: int = Field(default=3, ge=1, le=10, description="Maximum retry attempts")
    retry_backoff_factor: float = Field(default=2.0, ge=1.0, le=10.0, description="Retry backoff factor")
    enable_circuit_breaker: bool = Field(default=True, description="Enable circuit breaker pattern")
    
    # Optional LangSmith Integration
    enable_langsmith_integration: bool = Field(default=False, description="Enable LangSmith monitoring")
    langsmith_project_name: Optional[str] = Field(None, description="LangSmith project name")
    langsmith_api_key: Optional[str] = Field(None, description="LangSmith API key")
    
    @validator('chunking_parallel_workers', 'embedding_parallel_workers', 'retrieval_parallel_workers')
    def validate_parallel_workers(cls, v, values):
        """Validate parallel workers don't exceed max concurrent workflows"""
        max_concurrent = values.get('max_concurrent_workflows', 10)
        if v > max_concurrent:
            raise ValueError(f"Parallel workers ({v}) cannot exceed max_concurrent_workflows ({max_concurrent})")
        return v
    
    @validator('migration_rollout_percentage')
    def validate_rollout_percentage(cls, v):
        """Validate rollout percentage is between 0.0 and 1.0"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("migration_rollout_percentage must be between 0.0 and 1.0")
        return v


class WorkflowConfig(BaseModel):
    """Configuration for specific workflow types"""
    
    # Chunking Workflow Configuration
    chunking_quality_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum chunk quality threshold")
    chunking_max_retries: int = Field(default=3, ge=1, le=10, description="Maximum chunking retries")
    chunking_batch_size: int = Field(default=10, ge=1, le=100, description="Chunking batch size")
    
    # Embedding Workflow Configuration  
    embedding_quality_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="Minimum embedding quality threshold")
    embedding_max_retries: int = Field(default=3, ge=1, le=10, description="Maximum embedding retries")
    embedding_batch_size: int = Field(default=50, ge=1, le=200, description="Embedding batch size")
    enable_multi_model_embeddings: bool = Field(default=True, description="Enable multi-model embedding generation")
    
    # Retrieval Workflow Configuration
    retrieval_min_results: int = Field(default=3, ge=1, le=20, description="Minimum retrieval results")
    retrieval_max_expansion: int = Field(default=2, ge=1, le=10, description="Maximum query expansion rounds")
    retrieval_timeout_seconds: float = Field(default=30.0, ge=5.0, le=120.0, description="Retrieval timeout in seconds")
    enable_cross_repository_search: bool = Field(default=True, description="Enable cross-repository search")


class MigrationConfig(BaseModel):
    """Configuration for system migration and rollback"""
    
    # Safety Settings
    enable_safety_checks: bool = Field(default=True, description="Enable migration safety checks")
    require_performance_validation: bool = Field(default=True, description="Require performance validation before migration")
    min_success_rate_threshold: float = Field(default=0.95, ge=0.5, le=1.0, description="Minimum success rate for migration")
    
    # Rollback Configuration
    enable_automatic_rollback: bool = Field(default=True, description="Enable automatic rollback on failures")
    rollback_trigger_threshold: float = Field(default=0.1, ge=0.05, le=0.5, description="Error rate threshold for automatic rollback")
    rollback_evaluation_window_minutes: int = Field(default=5, ge=1, le=60, description="Evaluation window for rollback decisions")
    
    # Migration Phases
    phase_1_percentage: float = Field(default=0.05, ge=0.01, le=0.2, description="Phase 1 traffic percentage")
    phase_2_percentage: float = Field(default=0.25, ge=0.1, le=0.5, description="Phase 2 traffic percentage") 
    phase_3_percentage: float = Field(default=1.0, description="Phase 3 traffic percentage (full migration)")
    
    # Validation Settings
    performance_improvement_threshold: float = Field(default=1.1, ge=1.0, le=5.0, description="Required performance improvement")
    validation_sample_size: int = Field(default=100, ge=10, le=1000, description="Sample size for validation")


# Default configuration instances
DEFAULT_GRAPH_CONFIG = GraphConfig()
DEFAULT_WORKFLOW_CONFIG = WorkflowConfig()
DEFAULT_MIGRATION_CONFIG = MigrationConfig()