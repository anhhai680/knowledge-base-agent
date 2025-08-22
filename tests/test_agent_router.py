import pytest
from unittest.mock import Mock, MagicMock
from src.agents.agent_router import AgentRouter
from src.config.agent_config import AgentConfig, DiagramAgentType, AgentRoutingConfig
from src.agents.response_models import AgentResponse

class TestAgentRouterConfiguration:
    """Test configuration handling and copying in AgentRouter"""
    
    def test_configuration_copying_on_initialization(self):
        """Test that AgentRouter creates a copy of configuration instead of modifying original"""
        # Create a mock RAG agent and diagram handler
        mock_rag_agent = Mock()
        mock_diagram_handler = Mock()
        
        # Create an original configuration
        original_config = AgentConfig(
            routing=AgentRoutingConfig(
                preferred_diagram_agent=DiagramAgentType.DIAGRAM_AGENT
            )
        )
        
        # Store the original preferred_diagram_agent value
        original_preferred = original_config.routing.preferred_diagram_agent
        
        # Initialize router without diagram_agent (should trigger fallback)
        router = AgentRouter(
            rag_agent=mock_rag_agent,
            diagram_handler=mock_diagram_handler,
            diagram_agent=None,  # No diagram agent available
            agent_config=original_config
        )
        
        # Verify that the original configuration was NOT modified
        assert original_config.routing.preferred_diagram_agent == original_preferred
        assert original_config.routing.preferred_diagram_agent == DiagramAgentType.DIAGRAM_AGENT
        
        # Verify that the router's configuration is a copy with fallback applied
        assert router.agent_config.routing.preferred_diagram_agent == DiagramAgentType.DIAGRAM_HANDLER
        
        # Verify they are different objects
        assert router.agent_config is not original_config
        assert router.agent_config.routing is not original_config.routing
    
    def test_configuration_update_method(self):
        """Test that update_configuration creates a copy and validates properly"""
        # Create a mock RAG agent and diagram handler
        mock_rag_agent = Mock()
        mock_diagram_handler = Mock()
        
        # Create router with initial configuration
        initial_config = AgentConfig(
            routing=AgentRoutingConfig(
                preferred_diagram_agent=DiagramAgentType.DIAGRAM_HANDLER
            )
        )
        
        router = AgentRouter(
            rag_agent=mock_rag_agent,
            diagram_handler=mock_diagram_handler,
            diagram_agent=None,
            agent_config=initial_config
        )
        
        # Create a new configuration to update with
        new_config = AgentConfig(
            routing=AgentRoutingConfig(
                preferred_diagram_agent=DiagramAgentType.DIAGRAM_AGENT
            )
        )
        
        # Store original values
        original_new_config_preferred = new_config.routing.preferred_diagram_agent
        
        # Update configuration
        router.update_configuration(new_config)
        
        # Verify that the new_config was NOT modified
        assert new_config.routing.preferred_diagram_agent == original_new_config_preferred
        assert new_config.routing.preferred_diagram_agent == DiagramAgentType.DIAGRAM_AGENT
        
        # Verify that the router's configuration reflects the update with validation
        # Since no diagram_agent is available, it should fallback to DIAGRAM_HANDLER
        assert router.agent_config.routing.preferred_diagram_agent == DiagramAgentType.DIAGRAM_HANDLER
        
        # Verify they are different objects
        assert router.agent_config is not new_config
        assert router.agent_config.routing is not new_config.routing
    
    def test_get_current_configuration_returns_copy(self):
        """Test that get_current_configuration returns a copy to prevent external modification"""
        # Create a mock RAG agent and diagram handler
        mock_rag_agent = Mock()
        mock_diagram_handler = Mock()
        
        # Create router
        router = AgentRouter(
            rag_agent=mock_rag_agent,
            diagram_handler=mock_diagram_handler,
            diagram_agent=None
        )
        
        # Get current configuration
        current_config = router.get_current_configuration()
        
        # Verify it's a copy, not the same object
        assert current_config is not router.agent_config
        assert current_config.routing is not router.agent_config.routing
        
        # Modify the returned configuration
        current_config.routing.preferred_diagram_agent = DiagramAgentType.DIAGRAM_AGENT
        
        # Verify that the router's configuration was NOT affected
        assert router.agent_config.routing.preferred_diagram_agent != DiagramAgentType.DIAGRAM_AGENT
