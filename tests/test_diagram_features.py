"""
Test for agent router pattern and diagram generation functionality
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.agents.agent_router import AgentRouter
from src.processors.diagram_handler import DiagramHandler
from src.processors.sequence_detector import SequenceDetector


class TestAgentRouter:
    """Test agent routing functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_rag_agent = Mock()
        self.mock_vectorstore = Mock()
        self.mock_llm = Mock()
        
        self.diagram_handler = DiagramHandler(self.mock_vectorstore, self.mock_llm)
        self.agent_router = AgentRouter(self.mock_rag_agent, self.diagram_handler)
    
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
        self.mock_rag_agent.query.return_value = {
            "answer": "Test answer",
            "source_documents": [],
            "status": "success",
            "num_sources": 0
        }
        
        result = self.agent_router.route_query("How does authentication work?")
        
        self.mock_rag_agent.query.assert_called_once_with("How does authentication work?")
        assert result["answer"] == "Test answer"


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


class TestDiagramHandler:
    """Test diagram generation functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_vectorstore = Mock()
        self.mock_llm = Mock()
        self.handler = DiagramHandler(self.mock_vectorstore, self.mock_llm)
    
    def test_language_detection(self):
        """Test file language detection"""
        assert self.handler._detect_language_from_path("auth.py") == "python"
        assert self.handler._detect_language_from_path("service.js") == "javascript"
        assert self.handler._detect_language_from_path("component.ts") == "typescript"
        assert self.handler._detect_language_from_path("controller.cs") == "csharp"
        assert self.handler._detect_language_from_path("readme.txt") == "unknown"
    
    def test_name_sanitization(self):
        """Test Mermaid name sanitization"""
        assert self.handler._sanitize_name("auth-service") == "auth_service"
        assert self.handler._sanitize_name("user.controller") == "user_controller"
        assert self.handler._sanitize_name("order service") == "order_service"
    
    def test_interaction_validation(self):
        """Test interaction filtering"""
        assert self.handler._is_valid_interaction("Client", "AuthService", "login") == True
        assert self.handler._is_valid_interaction("Service", "Service", "method") == False  # self-call
        assert self.handler._is_valid_interaction("Client", "Service", "get") == False  # noise method
        assert self.handler._is_valid_interaction("A", "B", "c") == False  # too short


if __name__ == "__main__":
    pytest.main([__file__])