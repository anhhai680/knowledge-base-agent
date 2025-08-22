"""
Test for agent router pattern and diagram generation functionality
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.agents.agent_router import AgentRouter
from src.processors.sequence_detector import SequenceDetector


class TestAgentRouter:
    """Test agent routing functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_rag_agent = Mock()
        self.mock_diagram_agent = Mock()
        
        # Set up RAG agent mock
        self.mock_rag_agent.vectorstore = Mock()
        self.mock_rag_agent.process_query = Mock()
        
        # Set up DiagramAgent mock
        self.mock_diagram_agent.process_query = Mock()
        
        self.agent_router = AgentRouter(self.mock_rag_agent, self.mock_diagram_agent)
    
    def test_diagram_request_detection(self):
        """Test that diagram requests are properly detected"""
        diagram_questions = [
            "Show me a sequence diagram for user authentication",
            "Generate a flow diagram for the payment process",
            "Create a sequence diagram for order processing",
            "Visualize how the authentication system works",
            "Show me how data flows through the API",
            "Generate mermaid code for the checkout process"
        ]
        
        for question in diagram_questions:
            assert self.agent_router._is_diagram_request(question), f"Failed to detect diagram request: {question}"
    
    def test_regular_request_detection(self):
        """Test that regular questions are not detected as diagram requests"""
        regular_questions = [
            "How does the authentication middleware work?",
            "What are the available API endpoints?", 
            "Explain the database schema design",
            "How do I set up the development environment?",
            "What are the deployment requirements?"
        ]
        
        for question in regular_questions:
            assert not self.agent_router._is_diagram_request(question), f"Incorrectly detected as diagram request: {question}"
    
    def test_rag_agent_routing(self):
        """Test routing to RAG agent for regular queries"""
        # Mock successful RAG response
        self.mock_rag_agent.process_query.return_value = {
            "answer": "Test answer",
            "source_documents": [],
            "status": "success",
            "num_sources": 0
        }
        
        result = self.agent_router.route_query("How does authentication work?")
        
        self.mock_rag_agent.process_query.assert_called_once_with("How does authentication work?")
        # Note: result format will depend on adapt_agent_response implementation
    
    def test_diagram_agent_routing(self):
        """Test routing to DiagramAgent for diagram queries"""
        # Mock successful diagram response
        self.mock_diagram_agent.process_query.return_value = {
            "mermaid_code": "sequenceDiagram\n    A->>B: Request",
            "analysis_summary": "Test diagram generated",
            "status": "success"
        }
        
        result = self.agent_router.route_query("Show me a sequence diagram for authentication")
        
        self.mock_diagram_agent.process_query.assert_called_once_with("Show me a sequence diagram for authentication")
        # Note: result format will depend on adapt_agent_response implementation
    
    def test_diagram_agent_unavailable(self):
        """Test behavior when DiagramAgent is not available"""
        # Create router without diagram agent
        agent_router_no_diagram = AgentRouter(self.mock_rag_agent, None)
        
        result = agent_router_no_diagram.route_query("Show me a sequence diagram")
        
        # Should return error response about diagram functionality not being available
        assert "error" in str(result).lower() or "not available" in str(result).lower()


class TestSequenceDetector:
    """Test sequence detection functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.detector = SequenceDetector()
    
    def test_python_code_analysis(self):
        """Test Python code pattern detection"""
        python_code = """
class AuthController:
    def login(self, credentials):
        user = self.user_service.authenticate(credentials)
        return user
        """
        
        result = self.detector.analyze_code(python_code, 'python')
        
        assert result['language'] == 'python'
        assert 'interactions' in result
    
    def test_javascript_code_analysis(self):
        """Test JavaScript code pattern detection"""
        js_code = """
function loginUser(credentials) {
    const result = authService.authenticate(credentials);
    return result;
}
        """
        
        result = self.detector.analyze_code(js_code, 'javascript')
        
        assert result['language'] == 'javascript'
        assert 'interactions' in result


# Note: TestDiagramHandler has been removed as part of diagram backward compatibility cleanup
# All diagram functionality now uses the enhanced DiagramAgent


if __name__ == "__main__":
    pytest.main([__file__])