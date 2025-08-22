"""
Test Agent Router Integration - TASK031

This test suite validates the integration of DiagramAgent with AgentRouter,
including dual-agent support, intelligent routing, and backward compatibility.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from src.agents.agent_router import AgentRouter
from src.config.agent_config import AgentConfig, DiagramAgentType, AGENT_CONFIG_PRESETS


class TestAgentRouterIntegration(unittest.TestCase):
    """Test agent router integration with dual diagram agent support"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock dependencies
        self.mock_rag_agent = Mock()
        self.mock_diagram_handler = Mock()
        self.mock_diagram_agent = Mock()
        
        # Mock diagram handler methods
        self.mock_diagram_handler.generate_sequence_diagram.return_value = {
            "analysis_summary": "Handler generated diagram",
            "mermaid_code": "sequenceDiagram\n    A->>B: test",
            "diagram_type": "sequence",
            "source_documents": [],
            "status": "success"
        }
        
        # Mock diagram agent methods
        self.mock_diagram_agent.process_query.return_value = {
            "answer": "Agent generated diagram",
            "mermaid_code": "flowchart TD\n    A --> B",
            "diagram_type": "flowchart",
            "source_documents": [],
            "status": "success"
        }
    
    def test_backward_compatibility_initialization(self):
        """Test that old initialization pattern still works"""
        # Should work with just rag_agent and diagram_handler
        router = AgentRouter(self.mock_rag_agent, self.mock_diagram_handler)
        
        # Should initialize with default config
        self.assertIsNotNone(router.agent_config)
        self.assertEqual(router.rag_agent, self.mock_rag_agent)
        self.assertEqual(router.diagram_handler, self.mock_diagram_handler)
        self.assertIsNone(router.diagram_agent)
    
    def test_enhanced_initialization(self):
        """Test initialization with DiagramAgent"""
        config = AGENT_CONFIG_PRESETS["modern"]
        
        router = AgentRouter(
            self.mock_rag_agent, 
            self.mock_diagram_handler,
            self.mock_diagram_agent,
            config
        )
        
        self.assertEqual(router.diagram_agent, self.mock_diagram_agent)
        self.assertEqual(router.agent_config, config)
    
    def test_agent_selection_diagram_handler_preference(self):
        """Test agent selection with DiagramHandler preference"""
        config = AGENT_CONFIG_PRESETS["legacy"]
        
        router = AgentRouter(
            self.mock_rag_agent,
            self.mock_diagram_handler,
            self.mock_diagram_agent,
            config
        )
        
        # Should select DiagramHandler
        selected = router._select_diagram_agent("create a sequence diagram")
        self.assertEqual(selected, self.mock_diagram_handler)
    
    def test_agent_selection_diagram_agent_preference(self):
        """Test agent selection with DiagramAgent preference"""
        config = AGENT_CONFIG_PRESETS["modern"]
        
        router = AgentRouter(
            self.mock_rag_agent,
            self.mock_diagram_handler,
            self.mock_diagram_agent,
            config
        )
        
        # Should select DiagramAgent
        selected = router._select_diagram_agent("create a flowchart diagram")
        self.assertEqual(selected, self.mock_diagram_agent)
    
    def test_auto_selection_simple_query(self):
        """Test auto-selection for simple queries"""
        config = AGENT_CONFIG_PRESETS["hybrid"]
        
        router = AgentRouter(
            self.mock_rag_agent,
            self.mock_diagram_handler,
            self.mock_diagram_agent,
            config
        )
        
        # Simple sequence diagram request should use DiagramHandler
        selected = router._select_diagram_agent("show me a sequence diagram")
        self.assertEqual(selected, self.mock_diagram_handler)
    
    def test_auto_selection_complex_query(self):
        """Test auto-selection for complex queries"""
        config = AGENT_CONFIG_PRESETS["hybrid"]
        
        router = AgentRouter(
            self.mock_rag_agent,
            self.mock_diagram_handler,
            self.mock_diagram_agent,
            config
        )
        
        # Complex request should use DiagramAgent
        complex_query = "create a flowchart and class diagram showing the system architecture"
        selected = router._select_diagram_agent(complex_query)
        self.assertEqual(selected, self.mock_diagram_agent)
    
    def test_complex_query_detection(self):
        """Test complex query detection logic"""
        config = AGENT_CONFIG_PRESETS["hybrid"]
        
        router = AgentRouter(
            self.mock_rag_agent,
            self.mock_diagram_handler,
            self.mock_diagram_agent,
            config
        )
        
        # Simple queries
        self.assertFalse(router._is_complex_diagram_request("show me a sequence diagram"))
        self.assertFalse(router._is_complex_diagram_request("create interaction diagram"))
        
        # Complex queries
        self.assertTrue(router._is_complex_diagram_request("create flowchart and class diagram"))
        self.assertTrue(router._is_complex_diagram_request("analyze the system architecture"))
        self.assertTrue(router._is_complex_diagram_request("show component relationships"))
    
    def test_diagram_generation_with_handler(self):
        """Test diagram generation using DiagramHandler"""
        config = AGENT_CONFIG_PRESETS["legacy"]
        
        router = AgentRouter(
            self.mock_rag_agent,
            self.mock_diagram_handler,
            self.mock_diagram_agent,
            config
        )
        
        # Mock the diagram request detection
        router._is_diagram_request = Mock(return_value=True)
        router._is_mermaid_specific_request = Mock(return_value=False)
        
        result = router._generate_diagram_response("create sequence diagram")
        
        # Should call DiagramHandler
        self.mock_diagram_handler.generate_sequence_diagram.assert_called_once_with("create sequence diagram")
        self.assertEqual(result["answer"], "Handler generated diagram")
    
    def test_diagram_generation_with_agent(self):
        """Test diagram generation using DiagramAgent"""
        config = AGENT_CONFIG_PRESETS["modern"]
        
        router = AgentRouter(
            self.mock_rag_agent,
            self.mock_diagram_handler,
            self.mock_diagram_agent,
            config
        )
        
        # Mock the diagram request detection
        router._is_diagram_request = Mock(return_value=True)
        router._is_mermaid_specific_request = Mock(return_value=False)
        
        # Use a query that should definitely select DiagramAgent (modern config prefers it)
        result = router._generate_diagram_response("create flowchart showing system architecture")
        
        # Should call DiagramAgent
        self.mock_diagram_agent.process_query.assert_called_once_with("create flowchart showing system architecture")
        self.assertEqual(result["answer"], "Agent generated diagram")
    
    def test_fallback_mechanism(self):
        """Test fallback when primary agent fails"""
        config = AGENT_CONFIG_PRESETS["hybrid"]
        config.routing.enable_agent_fallback = True
        
        router = AgentRouter(
            self.mock_rag_agent,
            self.mock_diagram_handler,
            self.mock_diagram_agent,
            config
        )
        
        # Make DiagramAgent fail
        self.mock_diagram_agent.process_query.side_effect = Exception("Agent failed")
        
        # Mock diagram request detection
        router._is_diagram_request = Mock(return_value=True)
        router._is_mermaid_specific_request = Mock(return_value=False)
        
        # This should be a complex query that would normally route to DiagramAgent
        result = router._generate_diagram_response("create complex flowchart showing system architecture")
        
        # Should attempt DiagramAgent first, then fallback to DiagramHandler
        self.mock_diagram_agent.process_query.assert_called()
        self.mock_diagram_handler.generate_sequence_diagram.assert_called()
        
        # Result should indicate fallback was used
        self.assertIn("Fallback Response", result["answer"])
        self.assertTrue(result.get("fallback_used", False))
    
    def test_no_diagram_agent_graceful_degradation(self):
        """Test graceful degradation when DiagramAgent is not available"""
        config = AGENT_CONFIG_PRESETS["modern"]
        
        # Initialize without DiagramAgent
        router = AgentRouter(
            self.mock_rag_agent,
            self.mock_diagram_handler,
            diagram_agent=None,  # No DiagramAgent available
            agent_config=config
        )
        
        # Should always select DiagramHandler
        selected = router._select_diagram_agent("create complex flowchart")
        self.assertEqual(selected, self.mock_diagram_handler)
    
    def test_unified_agent_interface(self):
        """Test unified interface for different agent types"""
        router = AgentRouter(self.mock_rag_agent, self.mock_diagram_handler)
        
        # Test DiagramHandler interface
        result_handler = router._generate_with_agent(self.mock_diagram_handler, "test query")
        self.mock_diagram_handler.generate_sequence_diagram.assert_called_with("test query")
        
        # Test DiagramAgent interface
        result_agent = router._generate_with_agent(self.mock_diagram_agent, "test query")
        self.mock_diagram_agent.process_query.assert_called_with("test query")
    
    def test_configuration_validation(self):
        """Test configuration validation and warnings"""
        # Test invalid configuration (DiagramAgent preferred but not provided)
        config = AGENT_CONFIG_PRESETS["modern"].copy(deep=True)
        
        with patch('src.agents.agent_router.logger') as mock_logger:
            router = AgentRouter(
                self.mock_rag_agent,
                self.mock_diagram_handler,
                diagram_agent=None,
                agent_config=config
            )
            
            # Should log warning and fallback to DiagramHandler
            mock_logger.warning.assert_called()
            self.assertEqual(router.agent_config.routing.preferred_diagram_agent, 
                           DiagramAgentType.DIAGRAM_HANDLER)


if __name__ == '__main__':
    unittest.main()