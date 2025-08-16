"""
Test LangGraph Integration

This module tests the LangGraph integration components to ensure they work
correctly and maintain interface compatibility with existing LangChain components.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.config.graph_config import GraphConfig, SystemSelector, WorkflowConfig
from src.workflows.states import QueryState, WorkflowStatus, ChunkingState, EmbeddingState
from src.agents.base_graph_agent import BaseGraphAgent
from src.agents.langgraph_rag_agent import LangGraphRAGAgent
from src.agents.agent_router import AgentRouter
from src.utils.migration_utils import MigrationManager, PerformanceMetrics


class TestGraphConfig:
    """Test LangGraph configuration"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = GraphConfig()
        
        assert config.enable_langgraph == False
        assert config.default_system == SystemSelector.LANGCHAIN
        assert config.max_concurrent_workflows == 10
        assert config.enable_parallel_processing == True
        assert config.chunking_parallel_workers <= config.max_concurrent_workflows
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Valid config
        config = GraphConfig(
            max_concurrent_workflows=5,
            chunking_parallel_workers=3
        )
        assert config.chunking_parallel_workers == 3
        
        # Invalid config - workers exceed max concurrent
        with pytest.raises(ValueError):
            GraphConfig(
                max_concurrent_workflows=2,
                chunking_parallel_workers=5
            )
    
    def test_migration_config(self):
        """Test migration configuration"""
        config = GraphConfig(
            enable_langgraph=True,
            migration_rollout_percentage=0.25,
            enable_ab_testing=True
        )
        
        assert config.enable_langgraph == True
        assert config.migration_rollout_percentage == 0.25
        assert config.enable_ab_testing == True


class TestWorkflowStates:
    """Test workflow state classes"""
    
    def test_base_workflow_state(self):
        """Test base workflow state"""
        from src.workflows.states import BaseWorkflowState
        
        state = BaseWorkflowState(
            workflow_id="test-123",
            workflow_type="test"
        )
        
        assert state.workflow_id == "test-123"
        assert state.workflow_type == "test"
        assert state.status == WorkflowStatus.PENDING
        assert state.retry_count == 0
        assert state.can_retry == True
    
    def test_query_state(self):
        """Test query workflow state"""
        state = QueryState(
            workflow_id="query-123",
            workflow_type="query",
            user_query="What is the meaning of life?",
            initial_k=5
        )
        
        assert state.user_query == "What is the meaning of life?"
        assert state.initial_k == 5
        assert state.parallel_retrieval == True
        assert state.has_sufficient_results == False  # No results yet
        
        # Add some results
        state.final_results = ["result1", "result2", "result3"]
        assert state.has_sufficient_results == True
    
    def test_chunking_state(self):
        """Test chunking workflow state"""
        state = ChunkingState(
            workflow_id="chunk-123",
            workflow_type="chunking",
            file_path="/test/file.py",
            file_content="print('hello')",
            file_type="python"
        )
        
        assert state.file_path == "/test/file.py"
        assert state.file_content == "print('hello')"
        assert state.parallel_processing == True
        assert state.quality_meets_threshold == False  # No quality scores yet
        
        # Add quality scores
        state.quality_scores = [0.8, 0.9, 0.7]
        assert state.average_quality == 0.8
        assert state.quality_meets_threshold == True
    
    def test_embedding_state(self):
        """Test embedding workflow state"""
        state = EmbeddingState(
            workflow_id="embed-123",
            workflow_type="embedding",
            text_content="Hello world",
            content_type="text"
        )
        
        assert state.text_content == "Hello world"
        assert state.batch_processing == True
        assert state.has_successful_embedding == False
        
        # Add embedding
        state.final_embedding = [0.1, 0.2, 0.3]
        assert state.has_successful_embedding == True


class TestBaseGraphAgent:
    """Test base graph agent functionality"""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock graph agent for testing"""
        class MockGraphAgent(BaseGraphAgent):
            async def process_workflow(self, workflow_state):
                # Simulate processing
                workflow_state.status = WorkflowStatus.RUNNING
                await asyncio.sleep(0.01)  # Simulate work
                workflow_state.status = WorkflowStatus.COMPLETED
                return workflow_state
            
            def create_workflow_graph(self):
                return {"type": "mock_graph"}
        
        return MockGraphAgent()
    
    def test_agent_initialization(self, mock_agent):
        """Test agent initialization"""
        assert mock_agent.agent_id is not None
        assert mock_agent.created_at is not None
        assert len(mock_agent.active_workflows) == 0
        assert mock_agent.metrics["total_workflows"] == 0
    
    def test_start_workflow(self, mock_agent):
        """Test starting a workflow"""
        workflow_id = mock_agent.start_workflow("test", test_param="value")
        
        assert workflow_id is not None
        assert workflow_id in mock_agent.active_workflows
        assert mock_agent.metrics["total_workflows"] == 1
        
        workflow_state = mock_agent.active_workflows[workflow_id]
        assert workflow_state.workflow_type == "test"
        assert workflow_state.status == WorkflowStatus.PENDING
    
    @pytest.mark.asyncio
    async def test_execute_workflow(self, mock_agent):
        """Test executing a workflow"""
        workflow_id = mock_agent.start_workflow("test")
        result = await mock_agent.execute_workflow(workflow_id)
        
        assert result["workflow_id"] == workflow_id
        assert result["status"] == "completed"
        assert result["execution_time"] > 0
        assert workflow_id not in mock_agent.active_workflows
        assert workflow_id in mock_agent.completed_workflows
    
    def test_get_performance_metrics(self, mock_agent):
        """Test getting performance metrics"""
        workflow_id = mock_agent.start_workflow("test")
        metrics = mock_agent.get_performance_metrics()
        
        assert "total_workflows" in metrics
        assert "active_workflows_count" in metrics
        assert "agent_id" in metrics
        assert metrics["active_workflows_count"] == 1


class TestLangGraphRAGAgent:
    """Test LangGraph RAG agent"""
    
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM"""
        llm = Mock()
        llm.invoke = Mock(return_value="This is a test response")
        return llm
    
    @pytest.fixture
    def mock_vectorstore(self):
        """Create a mock vectorstore"""
        vectorstore = Mock()
        retriever = Mock()
        
        # Mock document
        doc = Mock()
        doc.page_content = "This is test content"
        doc.metadata = {"source": "test.txt"}
        
        retriever.get_relevant_documents = Mock(return_value=[doc])
        vectorstore.as_retriever = Mock(return_value=retriever)
        
        return vectorstore
    
    @pytest.fixture
    def rag_agent(self, mock_llm, mock_vectorstore):
        """Create a LangGraph RAG agent for testing"""
        config = GraphConfig(enable_langgraph=True)
        return LangGraphRAGAgent(
            llm=mock_llm,
            vectorstore=mock_vectorstore,
            config=config
        )
    
    def test_agent_initialization(self, rag_agent):
        """Test RAG agent initialization"""
        assert rag_agent.llm is not None
        assert rag_agent.vectorstore is not None
        assert rag_agent.config.enable_langgraph == True
    
    def test_query_interface_compatibility(self, rag_agent):
        """Test that query interface matches existing RAG agent"""
        question = "What is the purpose of this system?"
        result = rag_agent.query(question)
        
        # Check interface compatibility
        assert "answer" in result
        assert "source_documents" in result
        assert "metadata" in result
        
        # Check LangGraph-specific metadata
        assert result["metadata"]["processing_method"] == "langgraph"
        assert "execution_time" in result["metadata"]
        assert "workflow_id" in result["metadata"]
    
    def test_query_intent_analysis(self, rag_agent):
        """Test query intent analysis"""
        assert rag_agent._analyze_query_intent("How does this work?") == "explanation"
        assert rag_agent._analyze_query_intent("Show me a diagram") == "visualization"
        assert rag_agent._analyze_query_intent("Give me an example") == "example"
        assert rag_agent._analyze_query_intent("Find the login function") == "code_search"
    
    def test_query_complexity_analysis(self, rag_agent):
        """Test query complexity analysis"""
        assert rag_agent._analyze_query_complexity("Hello") == "simple"
        assert rag_agent._analyze_query_complexity("How does authentication work in this system?") == "medium"
        assert rag_agent._analyze_query_complexity("Can you explain the complete workflow from user login through data processing and provide examples?") == "complex"


class TestAgentRouter:
    """Test enhanced agent router"""
    
    @pytest.fixture
    def mock_rag_agent(self):
        """Create a mock LangChain RAG agent"""
        agent = Mock()
        agent.query = Mock(return_value={
            "answer": "LangChain response",
            "source_documents": [],
            "metadata": {}
        })
        return agent
    
    @pytest.fixture
    def mock_langgraph_agent(self):
        """Create a mock LangGraph RAG agent"""
        agent = Mock()
        agent.query = Mock(return_value={
            "answer": "LangGraph response",
            "source_documents": [],
            "metadata": {"processing_method": "langgraph"}
        })
        return agent
    
    @pytest.fixture
    def mock_diagram_handler(self):
        """Create a mock diagram handler"""
        return Mock()
    
    @pytest.fixture
    def router(self, mock_rag_agent, mock_diagram_handler, mock_langgraph_agent):
        """Create an agent router for testing"""
        config = GraphConfig(
            enable_langgraph=True,
            default_system=SystemSelector.LANGCHAIN
        )
        return AgentRouter(
            rag_agent=mock_rag_agent,
            diagram_handler=mock_diagram_handler,
            langgraph_rag_agent=mock_langgraph_agent,
            config=config
        )
    
    def test_router_initialization(self, router):
        """Test router initialization"""
        assert router.rag_agent is not None
        assert router.langgraph_rag_agent is not None
        assert router.config.enable_langgraph == True
        assert router.routing_stats["total_requests"] == 0
    
    def test_langchain_routing(self, router):
        """Test routing to LangChain system"""
        result = router.route_query("What is the meaning of life?")
        
        assert "answer" in result
        assert result["metadata"]["processing_system"] == "langchain"
        assert router.routing_stats["langchain_requests"] == 1
        assert router.routing_stats["langgraph_requests"] == 0
    
    def test_langgraph_routing(self, router):
        """Test routing to LangGraph system"""
        result = router.route_query("What is the meaning of life?", force_system="langgraph")
        
        assert "answer" in result
        assert result["metadata"]["processing_system"] == "langgraph"
        assert router.routing_stats["langgraph_requests"] == 1
        assert router.routing_stats["system_selection_overrides"] == 1
    
    def test_routing_stats(self, router):
        """Test routing statistics"""
        # Make some requests
        router.route_query("Test 1")  # LangChain (default)
        router.route_query("Test 2", force_system="langgraph")  # LangGraph (forced)
        router.route_query("Test 3")  # LangChain (default)
        
        stats = router.get_routing_stats()
        
        assert stats["total_requests"] == 3
        assert stats["langchain_requests"] == 2
        assert stats["langgraph_requests"] == 1
        assert stats["langchain_percentage"] == 66.67  # Approximately
        assert stats["langgraph_percentage"] == 33.33  # Approximately
    
    def test_system_selection(self, router):
        """Test system selection logic"""
        # Default system
        system = router._select_system()
        assert system == SystemSelector.LANGCHAIN
        
        # Forced system
        system = router._select_system("langgraph")
        assert system == SystemSelector.LANGGRAPH
        
        # Auto system with rollout
        router.config.default_system = SystemSelector.AUTO
        router.config.migration_rollout_percentage = 1.0  # 100% rollout
        system = router._select_system()
        assert system == SystemSelector.LANGGRAPH


class TestMigrationUtils:
    """Test migration utilities"""
    
    def test_performance_metrics(self):
        """Test performance metrics tracking"""
        metrics = PerformanceMetrics(
            system_name="test_system",
            execution_time=1.5,
            memory_usage=100.0,
            success=True
        )
        
        assert metrics.system_name == "test_system"
        assert metrics.execution_time == 1.5
        assert metrics.memory_usage == 100.0
        assert metrics.success == True
        assert metrics.timestamp is not None
    
    def test_migration_manager(self):
        """Test migration manager"""
        manager = MigrationManager()
        
        assert manager.current_rollout_percentage == 0.0
        assert manager.migration_active == False
        assert len(manager.performance_history) == 0
    
    def test_performance_tracking(self):
        """Test performance tracking context manager"""
        manager = MigrationManager()
        
        with manager.performance_tracker("test_system"):
            # Simulate some work
            import time
            time.sleep(0.01)
        
        assert len(manager.performance_history) == 1
        metrics = manager.performance_history[0]
        assert metrics.system_name == "test_system"
        assert metrics.execution_time > 0
        assert metrics.success == True
    
    def test_rollout_percentage_update(self):
        """Test updating rollout percentage"""
        manager = MigrationManager()
        
        # Valid update
        assert manager.update_rollout_percentage(0.25) == True
        assert manager.current_rollout_percentage == 0.25
        
        # Invalid update
        assert manager.update_rollout_percentage(1.5) == False
        assert manager.current_rollout_percentage == 0.25  # Unchanged


if __name__ == "__main__":
    pytest.main([__file__, "-v"])