"""
Tests for standardized response models and adapters
"""

import pytest
from src.agents.response_models import (
    AgentResponse, ResponseStatus, ResponseType,
    ResponseAdapter, RAGResponseAdapter, DiagramResponseAdapter, ReActResponseAdapter,
    adapt_agent_response, create_error_response, create_success_response
)


class TestAgentResponse:
    """Test the standardized AgentResponse class"""
    
    def test_basic_response_creation(self):
        """Test creating a basic response"""
        response = AgentResponse(
            answer="Test answer",
            status=ResponseStatus.SUCCESS,
            response_type=ResponseType.TEXT
        )
        
        assert response.answer == "Test answer"
        assert response.status == ResponseStatus.SUCCESS
        assert response.response_type == ResponseType.TEXT
        assert response.is_success() is True
        assert response.has_error() is False
    
    def test_response_with_diagram(self):
        """Test creating a response with diagram data"""
        response = AgentResponse(
            answer="Generated sequence diagram",
            status=ResponseStatus.SUCCESS,
            response_type=ResponseType.DIAGRAM,
            mermaid_code="sequenceDiagram\nA->>B: Hello",
            diagram_type="sequence"
        )
        
        assert response.mermaid_code == "sequenceDiagram\nA->>B: Hello"
        assert response.diagram_type == "sequence"
        assert response.response_type == ResponseType.DIAGRAM
        
        diagram_data = response.get_diagram_data()
        assert diagram_data is not None
        assert diagram_data["mermaid_code"] == "sequenceDiagram\nA->>B: Hello"
    
    def test_response_validation(self):
        """Test response validation and derived fields"""
        response = AgentResponse(
            answer="Test answer",
            source_documents=[{"content": "doc1"}, {"content": "doc2"}]
        )
        
        # num_sources should be automatically set
        assert response.num_sources == 2
        
        # Status should be automatically set to ERROR if error is present
        response_with_error = AgentResponse(
            answer="Test answer",
            error="Something went wrong"
        )
        assert response_with_error.status == ResponseStatus.ERROR
        assert response_with_error.has_error() is True
    
    def test_to_dict_conversion(self):
        """Test conversion to dictionary format"""
        response = AgentResponse(
            answer="Test answer",
            status=ResponseStatus.SUCCESS,
            response_type=ResponseType.TEXT,
            mermaid_code="test diagram",
            diagram_type="sequence"
        )
        
        response_dict = response.to_dict()
        assert response_dict["answer"] == "Test answer"
        assert response_dict["status"] == "success"
        assert response_dict["response_type"] == "text"
        assert response_dict["mermaid_code"] == "test diagram"
        assert response_dict["diagram_type"] == "sequence"
    
    def test_from_dict_creation(self):
        """Test creating response from dictionary"""
        data = {
            "answer": "Test answer",
            "status": "success",
            "response_type": "diagram",
            "mermaid_code": "test diagram"
        }
        
        response = AgentResponse.from_dict(data)
        assert response.answer == "Test answer"
        assert response.status == ResponseStatus.SUCCESS
        assert response.response_type == ResponseType.DIAGRAM
        assert response.mermaid_code == "test diagram"


class TestResponseAdapter:
    """Test the base ResponseAdapter class"""
    
    def test_adapt_empty_response(self):
        """Test adapting empty response"""
        response = ResponseAdapter.adapt({}, "TestAgent")
        
        assert response.answer == "No answer provided"
        assert response.status == ResponseStatus.SUCCESS
        assert response.metadata["original_agent"] == "TestAgent"
    
    def test_adapt_falsy_response(self):
        """Test adapting falsy response (None, empty dict)"""
        # Empty dict should use fallback logic
        response = ResponseAdapter.adapt({}, "TestAgent")
        assert response.answer == "No answer provided"
        assert response.status == ResponseStatus.SUCCESS
        
        # None should trigger error response
        response = ResponseAdapter.adapt(None, "TestAgent")
        assert response.answer == "No response received from agent"
        assert response.status == ResponseStatus.ERROR
    
    def test_adapt_none_response(self):
        """Test adapting None response"""
        response = ResponseAdapter.adapt(None, "TestAgent")
        
        assert response.answer == "No response received from agent"
        assert response.status == ResponseStatus.ERROR
        assert response.error == "Empty response from agent"
    
    def test_adapt_with_diagram(self):
        """Test adapting response with diagram data"""
        raw_response = {
            "analysis_summary": "Generated sequence diagram",
            "mermaid_code": "sequenceDiagram\nA->>B: Hello",
            "diagram_type": "sequence",
            "source_documents": [{"content": "doc1"}]
        }
        
        response = ResponseAdapter.adapt(raw_response, "DiagramAgent")
        
        assert response.answer == "Generated sequence diagram"
        assert response.response_type == ResponseType.DIAGRAM
        assert response.mermaid_code == "sequenceDiagram\nA->>B: Hello"
        assert response.diagram_type == "sequence"
        assert response.num_sources == 1
    
    def test_adapt_with_error(self):
        """Test adapting response with error"""
        raw_response = {
            "answer": "Something went wrong",
            "status": "error",
            "error": "Test error"
        }
        
        response = ResponseAdapter.adapt(raw_response, "TestAgent")
        
        assert response.answer == "Something went wrong"
        assert response.status == ResponseStatus.ERROR
        assert response.error == "Test error"


class TestSpecializedAdapters:
    """Test specialized adapters for different agent types"""
    
    def test_rag_response_adapter(self):
        """Test RAG response adapter"""
        raw_response = {
            "answer": "RAG response",
            "context_quality_score": 0.85,
            "enhancement_iterations": 3,
            "source_documents": [{"content": "doc1"}]
        }
        
        response = RAGResponseAdapter.adapt(raw_response)
        
        assert response.answer == "RAG response"
        assert response.context_quality_score == 0.85
        assert response.enhancement_iterations == 3
        assert response.metadata["original_agent"] == "RAGAgent"
    
    def test_diagram_response_adapter(self):
        """Test diagram response adapter"""
        raw_response = {
            "analysis_summary": "Generated diagram",
            "mermaid_code": "sequenceDiagram\nA->>B: Hello",
            "diagram_type": "sequence",
            "status": "warning"
        }
        
        response = DiagramResponseAdapter.adapt(raw_response)
        
        assert response.answer == "Generated diagram"
        assert response.response_type == ResponseType.DIAGRAM
        assert response.diagram_type == "sequence"
        # Warning with diagram should be converted to success
        assert response.status == ResponseStatus.SUCCESS
        assert response.metadata["original_status"] == "warning"
    
    def test_react_response_adapter(self):
        """Test ReAct response adapter"""
        raw_response = {
            "answer": "ReAct response",
            "reasoning_chain": ["Step 1", "Step 2"],
            "action_history": ["Action 1", "Action 2"],
            "iteration_count": 3
        }
        
        response = ReActResponseAdapter.adapt(raw_response)
        
        assert response.answer == "ReAct response"
        assert response.reasoning_steps == ["Step 1", "Step 2"]
        assert response.metadata["action_history"] == ["Action 1", "Action 2"]
        assert response.metadata["iteration_count"] == 3


class TestFactoryFunctions:
    """Test factory functions for creating responses"""
    
    def test_adapt_agent_response(self):
        """Test the main factory function"""
        raw_response = {
            "answer": "Test response",
            "mermaid_code": "test diagram"
        }
        
        # Test with different agent types
        rag_response = adapt_agent_response(raw_response, "rag")
        diagram_response = adapt_agent_response(raw_response, "diagram")
        generic_response = adapt_agent_response(raw_response, "generic")
        
        assert rag_response.metadata["original_agent"] == "RAGAgent"
        assert diagram_response.metadata["original_agent"] == "DiagramAgent"
        assert generic_response.metadata["original_agent"] == "Unknown"
    
    def test_create_error_response(self):
        """Test creating error responses"""
        error_response = create_error_response(
            "Test error message",
            "TEST_ERROR",
            "TestAgent"
        )
        
        assert error_response.answer == "Error: Test error message"
        assert error_response.status == ResponseStatus.ERROR
        assert error_response.error == "Test error message"
        assert error_response.error_code == "TEST_ERROR"
        assert error_response.metadata["agent"] == "TestAgent"
    
    def test_create_success_response(self):
        """Test creating success responses"""
        success_response = create_success_response(
            "Test success",
            ResponseType.DIAGRAM,
            mermaid_code="test diagram",
            diagram_type="sequence"
        )
        
        assert success_response.answer == "Test success"
        assert success_response.status == ResponseStatus.SUCCESS
        assert success_response.response_type == ResponseType.DIAGRAM
        assert success_response.mermaid_code == "test diagram"
        assert success_response.diagram_type == "sequence"


if __name__ == "__main__":
    pytest.main([__file__])
