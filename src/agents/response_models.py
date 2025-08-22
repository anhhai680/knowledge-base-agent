"""
Standardized response models and adapters for consistent agent response handling

This module provides a unified response format that all agents can use,
eliminating the complexity of handling different response structures in the router.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ResponseStatus(Enum):
    """Standard response status values"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PARTIAL = "partial"


class ResponseType(Enum):
    """Standard response types"""
    TEXT = "text"
    DIAGRAM = "diagram"
    CODE = "code"
    ANALYSIS = "analysis"
    MULTIMODAL = "multimodal"


@dataclass
class AgentResponse:
    """
    Standardized response format for all agents
    
    This provides a consistent structure that eliminates the need for
    complex response handling logic in the router.
    """
    
    # Core response fields
    answer: str
    status: ResponseStatus = ResponseStatus.SUCCESS
    response_type: ResponseType = ResponseType.TEXT
    
    # Source and metadata
    source_documents: List[Dict[str, Any]] = field(default_factory=list)
    num_sources: int = 0
    
    # Error handling
    error: Optional[str] = None
    error_code: Optional[str] = None
    
    # Enhanced fields (optional)
    reasoning_steps: List[str] = field(default_factory=list)
    query_analysis: Optional[Dict[str, Any]] = None
    context_quality_score: Optional[float] = None
    enhancement_iterations: int = 0
    
    # Diagram-specific fields
    mermaid_code: Optional[str] = None
    diagram_type: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and set derived fields"""
        if self.num_sources == 0 and self.source_documents:
            self.num_sources = len(self.source_documents)
        
        if self.error and self.status == ResponseStatus.SUCCESS:
            self.status = ResponseStatus.ERROR
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for API responses"""
        return {
            "answer": self.answer,
            "status": self.status.value,
            "response_type": self.response_type.value,
            "source_documents": self.source_documents,
            "num_sources": self.num_sources,
            "error": self.error,
            "error_code": self.error_code,
            "reasoning_steps": self.reasoning_steps,
            "query_analysis": self.query_analysis,
            "context_quality_score": self.context_quality_score,
            "enhancement_iterations": self.enhancement_iterations,
            "mermaid_code": self.mermaid_code,
            "diagram_type": self.diagram_type,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentResponse':
        """Create AgentResponse from dictionary"""
        # Handle status enum conversion
        if isinstance(data.get('status'), str):
            try:
                data['status'] = ResponseStatus(data['status'])
            except ValueError:
                data['status'] = ResponseStatus.SUCCESS
        
        # Handle response_type enum conversion
        if isinstance(data.get('response_type'), str):
            try:
                data['response_type'] = ResponseType(data['response_type'])
            except ValueError:
                data['response_type'] = ResponseType.TEXT
        
        return cls(**data)
    
    def is_success(self) -> bool:
        """Check if response indicates success"""
        return self.status == ResponseStatus.SUCCESS
    
    def has_error(self) -> bool:
        """Check if response has an error"""
        return self.error is not None or self.status == ResponseStatus.ERROR
    
    def get_diagram_data(self) -> Optional[Dict[str, Any]]:
        """Get diagram-specific data if available"""
        if self.mermaid_code:
            return {
                "mermaid_code": self.mermaid_code,
                "diagram_type": self.diagram_type,
                "response_type": self.response_type.value
            }
        return None


class ResponseAdapter:
    """Base class for adapting different agent response formats to AgentResponse"""
    
    @staticmethod
    def adapt(response: Dict[str, Any], agent_name: str = "Unknown") -> AgentResponse:
        """
        Adapt any agent response to standardized AgentResponse format
        
        Args:
            response: Raw agent response dictionary
            agent_name: Name of the agent for logging purposes
            
        Returns:
            Standardized AgentResponse
        """
        try:
            # Handle None responses
            if response is None:
                return AgentResponse(
                    answer="No response received from agent",
                    status=ResponseStatus.ERROR,
                    error="Empty response from agent"
                )
            
            # Extract core fields with fallbacks
            answer = response.get("answer") or response.get("analysis_summary") or "No answer provided"
            
            # Determine status
            status_str = response.get("status", "success")
            try:
                status = ResponseStatus(status_str)
            except ValueError:
                status = ResponseStatus.SUCCESS if status_str == "success" else ResponseStatus.ERROR
            
            # Determine response type
            response_type = ResponseType.TEXT
            if response.get("mermaid_code"):
                response_type = ResponseType.DIAGRAM
            elif response.get("code") or response.get("syntax"):
                response_type = ResponseType.CODE
            elif "analysis" in response.get("answer", "").lower():
                response_type = ResponseType.ANALYSIS
            
            # Extract source documents
            source_docs = response.get("source_documents", [])
            if not source_docs and response.get("sources"):
                source_docs = response.get("sources", [])
            
            # Create standardized response
            adapted_response = AgentResponse(
                answer=answer,
                status=status,
                response_type=response_type,
                source_documents=source_docs,
                num_sources=response.get("num_sources", len(source_docs)),
                error=response.get("error"),
                error_code=response.get("error_code"),
                reasoning_steps=response.get("reasoning_steps", []),
                query_analysis=response.get("query_analysis"),
                context_quality_score=response.get("context_quality_score"),
                enhancement_iterations=response.get("enhancement_iterations", 0),
                mermaid_code=response.get("mermaid_code"),
                diagram_type=response.get("diagram_type"),
                metadata={
                    "original_agent": agent_name,
                    "original_response_keys": list(response.keys()),
                    **response.get("metadata", {})
                }
            )
            
            logger.debug(f"Successfully adapted {agent_name} response to AgentResponse")
            return adapted_response
            
        except Exception as e:
            logger.error(f"Failed to adapt {agent_name} response: {str(e)}")
            # Return error response
            return AgentResponse(
                answer=f"Response adaptation failed: {str(e)}",
                status=ResponseStatus.ERROR,
                error=f"Adaptation error: {str(e)}",
                metadata={"original_agent": agent_name, "adaptation_failed": True}
            )


class RAGResponseAdapter(ResponseAdapter):
    """Specialized adapter for RAG agent responses"""
    
    @staticmethod
    def adapt(response: Dict[str, Any], agent_name: str = "RAGAgent") -> AgentResponse:
        """Adapt RAG agent response with enhanced field mapping"""
        try:
            # RAG responses typically have more detailed fields
            base_response = ResponseAdapter.adapt(response, agent_name)
            
            # Enhance with RAG-specific fields
            if response.get("context_quality_score") is not None:
                base_response.context_quality_score = response["context_quality_score"]
            
            if response.get("enhancement_iterations") is not None:
                base_response.enhancement_iterations = response["enhancement_iterations"]
            
            # Set response type based on content
            if "diagram" in response.get("answer", "").lower():
                base_response.response_type = ResponseType.DIAGRAM
            
            return base_response
            
        except Exception as e:
            logger.error(f"Failed to adapt RAG response: {str(e)}")
            return ResponseAdapter.adapt(response, agent_name)


class DiagramResponseAdapter(ResponseAdapter):
    """Specialized adapter for diagram agent responses"""
    
    @staticmethod
    def adapt(response: Dict[str, Any], agent_name: str = "DiagramAgent") -> AgentResponse:
        """Adapt diagram agent response with diagram-specific field mapping"""
        try:
            # Diagram responses have specific structure
            base_response = ResponseAdapter.adapt(response, agent_name)
            
            # Ensure diagram type is set correctly
            if response.get("mermaid_code"):
                base_response.response_type = ResponseType.DIAGRAM
                base_response.diagram_type = response.get("diagram_type", "sequence")
            
            # Handle diagram-specific status mapping
            if response.get("status") == "warning" and response.get("mermaid_code"):
                # Warning with diagram is still useful
                base_response.status = ResponseStatus.SUCCESS
                base_response.metadata["original_status"] = "warning"
            
            return base_response
            
        except Exception as e:
            logger.error(f"Failed to adapt diagram response: {str(e)}")
            return ResponseAdapter.adapt(response, agent_name)


class ReActResponseAdapter(ResponseAdapter):
    """Specialized adapter for ReAct agent responses"""
    
    @staticmethod
    def adapt(response: Dict[str, Any], agent_name: str = "ReActAgent") -> AgentResponse:
        """Adapt ReAct agent response with reasoning-specific field mapping"""
        try:
            # ReAct responses have reasoning chains
            base_response = ResponseAdapter.adapt(response, agent_name)
            
            # Enhance with ReAct-specific fields
            if response.get("reasoning_chain"):
                base_response.reasoning_steps = response["reasoning_chain"]
            
            if response.get("action_history"):
                base_response.metadata["action_history"] = response["action_history"]
            
            if response.get("iteration_count"):
                base_response.metadata["iteration_count"] = response["iteration_count"]
            
            # Set response type based on content
            if response.get("mermaid_code"):
                base_response.response_type = ResponseType.DIAGRAM
            
            return base_response
            
        except Exception as e:
            logger.error(f"Failed to adapt ReAct response: {str(e)}")
            return ResponseAdapter.adapt(response, agent_name)


def adapt_agent_response(response: Dict[str, Any], agent_type: str = "generic") -> AgentResponse:
    """
    Factory function to adapt any agent response using the appropriate adapter
    
    Args:
        response: Raw agent response
        agent_type: Type of agent for specialized adaptation
        
    Returns:
        Standardized AgentResponse
    """
    adapter_map = {
        "rag": RAGResponseAdapter,
        "diagram": DiagramResponseAdapter,
        "react": ReActResponseAdapter,
        "generic": ResponseAdapter
    }
    
    adapter_class = adapter_map.get(agent_type.lower(), ResponseAdapter)
    
    # For specialized adapters, use their default agent names
    if agent_type.lower() == "rag":
        return adapter_class.adapt(response, "RAGAgent")
    elif agent_type.lower() == "diagram":
        return adapter_class.adapt(response, "DiagramAgent")
    elif agent_type.lower() == "react":
        return adapter_class.adapt(response, "ReActAgent")
    else:
        return adapter_class.adapt(response, "Unknown")


def create_error_response(message: str, error_code: str = None, agent_name: str = "System") -> AgentResponse:
    """Create a standardized error response"""
    return AgentResponse(
        answer=f"Error: {message}",
        status=ResponseStatus.ERROR,
        error=message,
        error_code=error_code,
        metadata={"agent": agent_name, "error_type": "system_error"}
    )


def create_success_response(answer: str, response_type: ResponseType = ResponseType.TEXT, **kwargs) -> AgentResponse:
    """Create a standardized success response"""
    return AgentResponse(
        answer=answer,
        status=ResponseStatus.SUCCESS,
        response_type=response_type,
        **kwargs
    )
