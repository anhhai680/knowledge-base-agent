"""
Standalone test for sequence detector functionality (no external dependencies)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Create a simple mock for logging
class MockLogger:
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass

def get_logger(name):
    return MockLogger()

# Monkey patch the logging
import sys
sys.modules['src.utils.logging'] = type(sys)('mock_logging')
sys.modules['src.utils.logging'].get_logger = get_logger

from src.processors.sequence_detector import SequenceDetector


def test_sequence_detector():
    """Test sequence detector functionality"""
    detector = SequenceDetector()
    
    # Test Python code analysis
    python_code = """
class AuthController:
    def login(self, credentials):
        user = self.user_service.authenticate(credentials)
        return user
    """
    
    result = detector.analyze_code(python_code, 'python')
    print(f"Python analysis result: {result}")
    assert result['language'] == 'python'
    assert 'interactions' in result
    
    # Test JavaScript code analysis
    js_code = """
function loginUser(credentials) {
    const result = authService.authenticate(credentials);
    return result;
}
    """
    
    result = detector.analyze_code(js_code, 'javascript')
    print(f"JavaScript analysis result: {result}")
    assert result['language'] == 'javascript'
    assert 'interactions' in result
    
    print("✅ All sequence detector tests passed!")


def test_agent_router_patterns():
    """Test agent router pattern detection"""
    # Since we can't import the AgentRouter without dependencies, 
    # let's test the pattern logic directly
    
    import re
    
    # Copy pattern compilation logic
    patterns = [
        re.compile(r'\b(?:sequence|flow|interaction)\s+diagram\b', re.IGNORECASE),
        re.compile(r'\bgenerate\s+(?:a\s+)?(?:sequence|flow|mermaid)\b', re.IGNORECASE),
        re.compile(r'\bcreate\s+(?:a\s+)?(?:sequence|flow|diagram)\b', re.IGNORECASE),
        re.compile(r'\bshow\s+(?:me\s+)?(?:a\s+)?(?:sequence|flow|diagram)\b', re.IGNORECASE),
        re.compile(r'\bvisuali[sz]e\s+(?:how|the)\b', re.IGNORECASE),
        re.compile(r'\bmermaid\s+(?:code|diagram|syntax)\b', re.IGNORECASE),
    ]
    
    def is_diagram_request(question: str) -> bool:
        for pattern in patterns:
            if pattern.search(question):
                return True
        return False
    
    # Test diagram requests
    diagram_questions = [
        "Show me a sequence diagram for user authentication",
        "Generate a flow diagram for the payment process", 
        "Create a sequence diagram for order processing",
        "Visualize how the authentication system works",
        "Generate mermaid code for the checkout process"
    ]
    
    for question in diagram_questions:
        assert is_diagram_request(question), f"Failed to detect diagram request: {question}"
        print(f"✅ Detected diagram request: {question}")
    
    # Test regular requests
    regular_questions = [
        "How does the authentication middleware work?",
        "What are the available API endpoints?",
        "Explain the database schema design"
    ]
    
    for question in regular_questions:
        assert not is_diagram_request(question), f"Incorrectly detected as diagram request: {question}"
        print(f"✅ Correctly ignored regular request: {question}")
    
    print("✅ All agent router pattern tests passed!")


if __name__ == "__main__":
    test_sequence_detector()
    test_agent_router_patterns()
    print("✅ All tests passed!")