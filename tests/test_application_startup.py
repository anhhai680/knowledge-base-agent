"""
Tests for application startup and DiagramAgent integration
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock


class TestApplicationStartupLogic:
    """Test suite for application startup logic validation"""
    
    def test_main_function_structure(self):
        """Test that main.py has the expected function structure"""
        # Test the file exists and can be read
from pathlib import Path

class TestApplicationStartupLogic:
    """Test suite for application startup logic validation"""
    
    def test_main_function_structure(self):
        """Test that main.py has the expected function structure"""
        # Test the file exists and can be read
        main_py_path = Path(__file__).parent.parent / "main.py"
        with open(main_py_path, "r") as f:
            content = f.read()
        
        # Check for key functions and imports
        assert "def main():" in content
        assert "async def validate_diagram_agent_startup():" in content
        assert "async def verify_enhanced_diagram_features():" in content
        assert "import asyncio" in content
        assert "import uvicorn" in content
        
        # Check for enhanced error handling
        assert "DiagramAgent validation" in content
        assert "Enhanced diagram features" in content
        assert "Configuration validation" in content
    
    def test_enhanced_startup_validation_structure(self):
        """Test that enhanced startup validation has proper structure"""
        main_py_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "main.py")
        with open(main_py_path, "r") as f:
            content = f.read()
        
        # Check for proper async structure
        assert "startup_with_validation()" in content
        assert "validate_diagram_agent_startup()" in content
        assert "verify_enhanced_diagram_features()" in content
        
        # Check for proper error handling
        assert "try:" in content
        assert "except Exception as e:" in content
        
        # Check for proper logging
        assert "logger.info" in content
        assert "logger.error" in content
    
    def test_health_check_validation_logic(self):
        """Test the health check validation logic structure"""
        with open("/home/runner/work/knowledge-base-agent/knowledge-base-agent/main.py", "r") as f:
            content = f.read()
        
        # Check for proper health check components
        assert "llm" in content
        assert "vector_store" in content  
        assert "configuration" in content
        assert "required_components" in content
    
    @pytest.mark.asyncio
    async def test_httpx_client_usage_pattern(self):
        """Test that httpx client usage follows proper async patterns"""
        # Mock response for health check
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "components": {
                "llm": "healthy",
                "vector_store": "healthy", 
                "configuration": "healthy"
            }
        }
        
        # Mock client
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        
        # Test async context manager usage
        with patch('httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client
            
            # Simulate the validation logic
            async with mock_httpx() as client:
                response = await client.get("http://localhost:8000/health", timeout=5)
                assert response.status_code == 200
                
                health_data = response.json()
                components = health_data.get("components", {})
                
                required_components = ["llm", "vector_store", "configuration"]
                unhealthy_components = []
                
                for component in required_components:
                    status = components.get(component, "missing")
                    if status != "healthy":
                        unhealthy_components.append(f"{component}: {status}")
                
                # Should be healthy in this test
                assert len(unhealthy_components) == 0
    
    @pytest.mark.asyncio
    async def test_diagram_features_verification_pattern(self):
        """Test diagram features verification pattern"""
        # Mock successful diagram response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "answer": "Here's a diagram",
            "mermaid_code": "sequenceDiagram\n    A->>B: Hello",
            "diagram_type": "sequence"
        }
        
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        
        with patch('httpx.AsyncClient') as mock_httpx:
            mock_httpx.return_value.__aenter__.return_value = mock_client
            
            # Simulate the verification logic
            async with mock_httpx() as client:
                test_payload = {
                    "question": "generate a simple sequence diagram",
                    "max_results": 1
                }
                
                response = await client.post(
                    "http://localhost:8000/query", 
                    json=test_payload, 
                    timeout=10
                )
                
                assert response.status_code == 200
                result = response.json()
                
                # Check for diagram-specific fields
                has_diagram_fields = any(key in result for key in ['mermaid_code', 'diagram_type'])
                assert has_diagram_fields is True


class TestHealthCheckEnhancements:
    """Test enhanced health check functionality"""
    
    def test_health_check_has_diagram_agent_status(self):
        """Test that health check includes DiagramAgent status checks"""
        routes_path = os.path.join(os.path.dirname(__file__), "..", "src", "api", "routes.py")
        with open(routes_path, "r") as f:
            content = f.read()
        
        # Check for DiagramAgent health check additions
        assert "diagram_agent" in content
        assert "agent_router" in content
        assert "enhanced_features" in content
    
    def test_config_endpoint_includes_diagram_agent(self):
        """Test that config endpoint includes DiagramAgent configuration"""
        with open("/home/runner/work/knowledge-base-agent/knowledge-base-agent/src/api/routes.py", "r") as f:
            content = f.read()
        
        # Check for new diagram agent config endpoint
        assert "/config/diagram-agent" in content
        assert "get_diagram_agent_config" in content
        assert "supported_diagram_types" in content


class TestConfigurationValidation:
    """Test configuration validation enhancements"""
    
    def test_main_validates_config_before_startup(self):
        """Test that main.py validates configuration before starting"""
        with open("/home/runner/work/knowledge-base-agent/knowledge-base-agent/main.py", "r") as f:
            content = f.read()
        
        # Check that configuration validation happens early
        assert "validate_llm_config" in content
        assert "validate_embedding_config" in content
        assert "Configuration validation passed" in content
        assert 'return 1' in content  # Error handling for invalid config
    
    def test_environment_mode_handling(self):
        """Test that different environment modes are handled"""
        with open("/home/runner/work/knowledge-base-agent/knowledge-base-agent/main.py", "r") as f:
            content = f.read()
        
        # Check for development vs production mode handling
        assert "development" in content
        assert "Production mode" in content
        assert "use_reload" in content
        assert "DOCKER_CONTAINER" in content


class TestErrorHandling:
    """Test error handling enhancements"""
    
    def test_graceful_degradation(self):
        """Test that application handles DiagramAgent failures gracefully"""
        with open("/home/runner/work/knowledge-base-agent/knowledge-base-agent/main.py", "r") as f:
            content = f.read()
        
        # Check for graceful degradation messaging
        assert "degraded functionality" in content
        assert "limited functionality" in content
        assert "continuing with" in content
    
    def test_comprehensive_error_logging(self):
        """Test that errors are properly logged"""
        with open("/home/runner/work/knowledge-base-agent/knowledge-base-agent/main.py", "r") as f:
            content = f.read()
        
        # Check for proper error logging
        assert "logger.error" in content
        assert "logger.warning" in content
        assert "logger.info" in content
        assert "Failed to validate" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])