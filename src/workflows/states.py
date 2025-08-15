"""
Workflow State Definitions

This module defines the state management classes for LangGraph workflows.
All states inherit from BaseWorkflowState and provide type-safe workflow
state management with validation and persistence support.
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class WorkflowStatus(str, Enum):
    """Workflow status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class BaseWorkflowState(BaseModel):
    """Base state for all LangGraph workflows"""
    
    # Core Identification
    workflow_id: str = Field(..., description="Unique workflow identifier")
    workflow_type: str = Field(..., description="Type of workflow")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Workflow creation timestamp")
    
    # Status Management
    status: WorkflowStatus = Field(default=WorkflowStatus.PENDING, description="Current workflow status")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    # Retry and Recovery
    retry_count: int = Field(default=0, ge=0, description="Number of retry attempts")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    
    # Metadata and Context
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional workflow metadata")
    
    # State Persistence
    checkpoint_id: Optional[str] = Field(None, description="Checkpoint identifier for state persistence")
    
    # Performance Tracking
    execution_time: Optional[float] = Field(None, ge=0.0, description="Total execution time in seconds")
    node_execution_history: List[Dict[str, Any]] = Field(default_factory=list, description="Node execution history")
    memory_usage: Optional[float] = Field(None, ge=0.0, description="Memory usage in MB")
    
    @validator('status')
    def validate_status_transition(cls, v, values):
        """Validate status transitions are logical"""
        # Add status transition validation logic if needed
        return v
    
    @property
    def can_retry(self) -> bool:
        """Check if workflow can be retried"""
        return self.retry_count < self.max_retries and self.status in [WorkflowStatus.FAILED, WorkflowStatus.RETRYING]
    
    def record_node_execution(self, node_name: str, execution_time: float, **kwargs):
        """Record node execution in history"""
        execution_record = {
            "node": node_name,
            "execution_time": execution_time,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs
        }
        self.node_execution_history.append(execution_record)


class ChunkingState(BaseWorkflowState):
    """State for chunking workflow with LangGraph optimizations"""
    
    # Input Data
    file_path: str = Field(..., description="Path to file being chunked")
    file_content: str = Field(..., description="Content of the file")
    file_type: str = Field(..., description="Type/extension of the file")
    
    # Processing Configuration
    chunking_strategy: Optional[str] = Field(None, description="Selected chunking strategy")
    parallel_processing: bool = Field(default=True, description="Enable parallel processing")
    chunk_batch_size: int = Field(default=10, ge=1, le=100, description="Batch size for parallel processing")
    
    # Processing State
    ast_elements: Optional[List[Any]] = Field(None, description="AST elements for semantic chunking")
    chunks: List[Dict[str, Any]] = Field(default_factory=list, description="Generated chunks")
    quality_scores: List[float] = Field(default_factory=list, description="Quality scores for chunks")
    regenerate_chunks: bool = Field(default=False, description="Flag to regenerate chunks")
    
    # Quality Control
    quality_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum quality threshold")
    
    @property
    def average_quality(self) -> float:
        """Calculate average quality score"""
        if not self.quality_scores:
            return 0.0
        return sum(self.quality_scores) / len(self.quality_scores)
    
    @property
    def quality_meets_threshold(self) -> bool:
        """Check if quality meets threshold"""
        return self.average_quality >= self.quality_threshold


class EmbeddingState(BaseWorkflowState):
    """State for embedding workflow with LangGraph optimizations"""
    
    # Input Data
    text_content: str = Field(..., description="Text content to embed")
    content_type: str = Field(..., description="Type of content being embedded")
    
    # Processing Configuration
    embedding_strategy: Optional[str] = Field(None, description="Selected embedding strategy")
    candidate_models: List[str] = Field(default_factory=list, description="Candidate embedding models")
    batch_processing: bool = Field(default=True, description="Enable batch processing")
    batch_size: int = Field(default=50, ge=1, le=200, description="Batch size for embeddings")
    
    # Results
    final_embedding: Optional[List[float]] = Field(None, description="Final selected embedding")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Embedding quality score")
    selected_model: Optional[str] = Field(None, description="Selected embedding model")
    
    # Error Tracking
    errors: Dict[str, str] = Field(default_factory=dict, description="Errors per model")
    
    # Performance Metrics
    model_performance_metrics: Dict[str, Dict[str, float]] = Field(
        default_factory=dict, 
        description="Performance metrics per model"
    )
    embedding_dimensions: Optional[int] = Field(None, ge=1, description="Embedding dimensions")
    
    @property
    def has_successful_embedding(self) -> bool:
        """Check if embedding was successfully generated"""
        return self.final_embedding is not None and len(self.final_embedding) > 0


class QueryState(BaseWorkflowState):
    """State for query workflow with LangGraph optimizations"""
    
    # Input Query
    user_query: str = Field(..., description="Original user query")
    query_intent: Optional[str] = Field(None, description="Detected query intent")
    query_complexity: Optional[str] = Field(None, description="Query complexity level")
    
    # Retrieval Configuration
    retrieval_strategy: Optional[str] = Field(None, description="Selected retrieval strategy")
    retrieval_depth: Optional[str] = Field(None, description="Retrieval depth level")
    initial_k: int = Field(default=5, ge=1, le=50, description="Initial number of results to retrieve")
    min_results_threshold: int = Field(default=3, ge=1, le=20, description="Minimum results threshold")
    
    # Processing Settings
    parallel_retrieval: bool = Field(default=True, description="Enable parallel retrieval")
    retrieval_timeout: float = Field(default=30.0, ge=5.0, le=120.0, description="Retrieval timeout in seconds")
    context_window_size: int = Field(default=8000, ge=1000, le=32000, description="Context window size in tokens")
    
    # Results
    retrieval_results: Dict[str, List[Any]] = Field(default_factory=dict, description="Retrieval results by strategy")
    final_results: List[Any] = Field(default_factory=list, description="Final processed results")
    cross_repo_results: List[Any] = Field(default_factory=list, description="Cross-repository results")
    
    # Execution Plan
    query_execution_plan: Optional[Dict[str, Any]] = Field(None, description="Query execution plan")
    
    @property
    def has_sufficient_results(self) -> bool:
        """Check if we have sufficient results"""
        return len(self.final_results) >= self.min_results_threshold


class OrchestrationState(BaseWorkflowState):
    """State for master workflow orchestration"""
    
    # Workflow Management
    sub_workflows: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Sub-workflow states")
    workflow_dependencies: Dict[str, List[str]] = Field(default_factory=dict, description="Workflow dependencies")
    execution_order: List[str] = Field(default_factory=list, description="Execution order of workflows")
    
    # Execution Configuration
    parallel_execution: bool = Field(default=True, description="Enable parallel execution")
    max_concurrent_workflows: int = Field(default=5, ge=1, le=20, description="Max concurrent workflows")
    
    # Orchestration State
    workflow_graph: Optional[Dict[str, Any]] = Field(None, description="Workflow graph definition")
    checkpoint_frequency: int = Field(default=10, ge=1, le=100, description="Checkpoint every N steps")
    error_recovery_strategy: str = Field(default="retry", description="Error recovery strategy")
    
    # Execution Tracking
    completed_workflows: List[str] = Field(default_factory=list, description="Completed workflow IDs")
    failed_workflows: List[str] = Field(default_factory=list, description="Failed workflow IDs")
    running_workflows: List[str] = Field(default_factory=list, description="Currently running workflow IDs")
    
    @property
    def dependencies_valid(self) -> bool:
        """Check if all dependencies are satisfied"""
        # Implement dependency validation logic
        return True
    
    @property
    def execution_successful(self) -> bool:
        """Check if execution is successful so far"""
        return len(self.failed_workflows) == 0
    
    @property
    def all_workflows_completed(self) -> bool:
        """Check if all workflows are completed"""
        total_workflows = len(self.sub_workflows)
        return len(self.completed_workflows) + len(self.failed_workflows) == total_workflows