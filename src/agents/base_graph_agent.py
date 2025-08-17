"""
Base LangGraph Agent

This module provides the base class for all LangGraph-based agents in the system.
It implements the same interface as the existing LangChain agents to ensure
zero breaking changes during parallel system deployment.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from ..config.graph_config import GraphConfig, DEFAULT_GRAPH_CONFIG
from ..workflows.states import BaseWorkflowState, WorkflowStatus
from ..utils.logging import get_logger

logger = get_logger(__name__)


class BaseGraphAgent(ABC):
    """
    Base class for all LangGraph agents.
    
    Provides common functionality for workflow management, state persistence,
    and parallel execution while maintaining interface compatibility with
    existing LangChain agents.
    """
    
    def __init__(self, 
                 config: Optional[GraphConfig] = None,
                 **kwargs):
        """
        Initialize the base graph agent.
        
        Args:
            config: LangGraph configuration
            **kwargs: Additional configuration parameters
        """
        self.config = config or DEFAULT_GRAPH_CONFIG
        self.agent_id = str(uuid.uuid4())
        self.created_at = datetime.utcnow()
        
        # Workflow tracking
        self.active_workflows: Dict[str, BaseWorkflowState] = {}
        self.completed_workflows: Dict[str, BaseWorkflowState] = {}
        
        # Performance metrics
        self.metrics = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_execution_time": 0.0,
            "total_execution_time": 0.0
        }
        
        logger.info(f"Initialized {self.__class__.__name__} with ID: {self.agent_id}")
    
    @abstractmethod
    async def process_workflow(self, workflow_state: BaseWorkflowState) -> BaseWorkflowState:
        """
        Process a workflow using LangGraph.
        
        Args:
            workflow_state: Initial workflow state
            
        Returns:
            Updated workflow state after processing
        """
        pass
    
    @abstractmethod
    def create_workflow_graph(self):
        """
        Create the LangGraph workflow graph.
        
        Returns:
            Compiled LangGraph workflow
        """
        pass
    
    def start_workflow(self, workflow_type: str, **kwargs) -> str:
        """
        Start a new workflow.
        
        Args:
            workflow_type: Type of workflow to start
            **kwargs: Workflow-specific parameters
            
        Returns:
            Workflow ID
        """
        workflow_id = str(uuid.uuid4())
        
        # Create initial workflow state based on type
        workflow_state = self._create_initial_state(workflow_type, workflow_id, **kwargs)
        
        # Track the workflow
        self.active_workflows[workflow_id] = workflow_state
        self.metrics["total_workflows"] += 1
        
        logger.info(f"Started workflow {workflow_id} of type {workflow_type}")
        return workflow_id
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        Execute a workflow by ID.
        
        Args:
            workflow_id: ID of workflow to execute
            
        Returns:
            Workflow execution result
        """
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow_state = self.active_workflows[workflow_id]
        start_time = datetime.utcnow()
        
        try:
            # Update status
            workflow_state.status = WorkflowStatus.RUNNING
            
            # Process the workflow
            result_state = await self.process_workflow(workflow_state)
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            result_state.execution_time = execution_time
            
            # Update metrics
            self._update_metrics(result_state, execution_time)
            
            # Move to completed workflows
            self.completed_workflows[workflow_id] = result_state
            del self.active_workflows[workflow_id]
            
            logger.info(f"Completed workflow {workflow_id} in {execution_time:.2f}s")
            
            return {
                "workflow_id": workflow_id,
                "status": result_state.status.value,
                "execution_time": execution_time,
                "result": self._extract_result(result_state)
            }
            
        except Exception as e:
            # Handle workflow failure
            workflow_state.status = WorkflowStatus.FAILED
            workflow_state.error = str(e)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            workflow_state.execution_time = execution_time
            
            self.metrics["failed_workflows"] += 1
            self.completed_workflows[workflow_id] = workflow_state
            del self.active_workflows[workflow_id]
            
            logger.error(f"Workflow {workflow_id} failed after {execution_time:.2f}s: {e}")
            
            return {
                "workflow_id": workflow_id,
                "status": WorkflowStatus.FAILED.value,
                "execution_time": execution_time,
                "error": str(e)
            }
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        Get status of a workflow.
        
        Args:
            workflow_id: ID of workflow to check
            
        Returns:
            Workflow status information
        """
        # Check active workflows
        if workflow_id in self.active_workflows:
            state = self.active_workflows[workflow_id]
            return {
                "workflow_id": workflow_id,
                "status": state.status.value,
                "progress": self._calculate_progress(state),
                "execution_time": state.execution_time,
                "error": state.error
            }
        
        # Check completed workflows
        if workflow_id in self.completed_workflows:
            state = self.completed_workflows[workflow_id]
            return {
                "workflow_id": workflow_id,
                "status": state.status.value,
                "execution_time": state.execution_time,
                "error": state.error,
                "completed": True
            }
        
        raise ValueError(f"Workflow {workflow_id} not found")
    
    def list_active_workflows(self) -> List[Dict[str, Any]]:
        """
        List all active workflows.
        
        Returns:
            List of active workflow information
        """
        return [
            {
                "workflow_id": wf_id,
                "workflow_type": state.workflow_type,
                "status": state.status.value,
                "started_at": state.timestamp.isoformat(),
                "execution_time": state.execution_time
            }
            for wf_id, state in self.active_workflows.items()
        ]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get agent performance metrics.
        
        Returns:
            Performance metrics dictionary
        """
        return {
            **self.metrics,
            "active_workflows_count": len(self.active_workflows),
            "completed_workflows_count": len(self.completed_workflows),
            "agent_id": self.agent_id,
            "uptime_seconds": (datetime.utcnow() - self.created_at).total_seconds()
        }
    
    def _create_initial_state(self, workflow_type: str, workflow_id: str, **kwargs) -> BaseWorkflowState:
        """
        Create initial workflow state based on type.
        
        Args:
            workflow_type: Type of workflow
            workflow_id: Unique workflow identifier
            **kwargs: Additional parameters
            
        Returns:
            Initial workflow state
        """
        return BaseWorkflowState(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            **kwargs
        )
    
    def _update_metrics(self, workflow_state: BaseWorkflowState, execution_time: float):
        """
        Update performance metrics.
        
        Args:
            workflow_state: Completed workflow state
            execution_time: Execution time in seconds
        """
        if workflow_state.status == WorkflowStatus.COMPLETED:
            self.metrics["successful_workflows"] += 1
        elif workflow_state.status == WorkflowStatus.FAILED:
            self.metrics["failed_workflows"] += 1
        
        # Update execution time metrics
        self.metrics["total_execution_time"] += execution_time
        total_completed = self.metrics["successful_workflows"] + self.metrics["failed_workflows"]
        if total_completed > 0:
            self.metrics["average_execution_time"] = self.metrics["total_execution_time"] / total_completed
    
    def _calculate_progress(self, workflow_state: BaseWorkflowState) -> float:
        """
        Calculate workflow progress percentage.
        
        Args:
            workflow_state: Current workflow state
            
        Returns:
            Progress percentage (0.0 to 1.0)
        """
        # Default implementation - subclasses can override
        if workflow_state.status == WorkflowStatus.COMPLETED:
            return 1.0
        elif workflow_state.status == WorkflowStatus.FAILED:
            return 0.0
        elif workflow_state.status == WorkflowStatus.RUNNING:
            # Estimate based on node execution history
            if hasattr(workflow_state, 'node_execution_history'):
                # This is a simple estimation - can be made more sophisticated
                return min(0.9, len(workflow_state.node_execution_history) * 0.2)
            return 0.1
        else:
            return 0.0
    
    def _extract_result(self, workflow_state: BaseWorkflowState) -> Any:
        """
        Extract result from completed workflow state.
        
        Args:
            workflow_state: Completed workflow state
            
        Returns:
            Workflow result
        """
        # Default implementation - subclasses should override for specific result extraction
        return {
            "status": workflow_state.status.value,
            "execution_time": workflow_state.execution_time,
            "metadata": workflow_state.metadata
        }