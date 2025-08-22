import pytest
from unittest.mock import Mock, MagicMock
from src.agents.agent_router import AgentRouter
from src.config.agent_config import AgentConfig, AgentRoutingConfig
from src.agents.response_models import AgentResponse

class TestAgentRouterConfiguration:
    """Test configuration handling and copying in AgentRouter"""
    
    def test_configuration_copying_on_initialization(self):
        """Test that AgentRouter creates a copy of configuration and handles it properly"""
        # Create a mock RAG agent and diagram agent
        mock_rag_agent = Mock()
        mock_diagram_agent = Mock()
        
        # Create an original configuration
        original_config = AgentConfig(
            routing=AgentRoutingConfig()
        )
        
        # Initialize router with diagram_agent
        router = AgentRouter(
            rag_agent=mock_rag_agent,
            diagram_agent=mock_diagram_agent,
            config=original_config
        )
        
        # Verify that the router's configuration is a copy
        assert router.agent_config is not original_config
        if hasattr(router.agent_config, 'routing') and hasattr(original_config, 'routing'):
            assert router.agent_config.routing is not original_config.routing
    
    def test_configuration_update_method(self):
        """Test that update_configuration creates a copy and works properly"""
        # Create a mock RAG agent and diagram agent
        mock_rag_agent = Mock()
        mock_diagram_agent = Mock()
        
        # Create router with initial configuration
        initial_config = AgentConfig(
            routing=AgentRoutingConfig()
        )
        
        router = AgentRouter(
            rag_agent=mock_rag_agent,
            diagram_agent=mock_diagram_agent,
            config=initial_config
        )
        
        # Create a new configuration to update with
        new_config = AgentConfig(
            routing=AgentRoutingConfig()
        )
        
        # Update configuration
        router.update_configuration(new_config)
        
        # Verify that the router's configuration was updated
        assert router.agent_config is not new_config
        if hasattr(router.agent_config, 'routing') and hasattr(new_config, 'routing'):
            assert router.agent_config.routing is not new_config.routing
    
    def test_get_current_configuration_returns_copy(self):
        """Test that get_current_configuration returns a copy to prevent external modification"""
        # Create a mock RAG agent and diagram agent
        mock_rag_agent = Mock()
        mock_diagram_agent = Mock()
        
        # Create router
        router = AgentRouter(
            rag_agent=mock_rag_agent,
            diagram_agent=mock_diagram_agent
        )
        
        # Get current configuration
        current_config = router.get_current_configuration()
        
        # Verify it's a copy, not the same object
        assert current_config is not router.agent_config
        if hasattr(current_config, 'routing') and hasattr(router.agent_config, 'routing'):
            assert current_config.routing is not router.agent_config.routing
    
    def test_router_with_no_diagram_agent(self):
        """Test router behavior when no diagram agent is provided"""
        mock_rag_agent = Mock()
        
        # Create router without diagram agent
        router = AgentRouter(
            rag_agent=mock_rag_agent,
            diagram_agent=None
        )
        
        # Should still initialize successfully
        assert router.rag_agent is mock_rag_agent
        assert router.diagram_agent is None
        
        # Should have route cache
        assert hasattr(router, '_route_cache')
        assert isinstance(router._route_cache, dict)
