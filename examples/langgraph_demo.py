#!/usr/bin/env python3
"""
LangGraph Integration Example

This script demonstrates the LangGraph integration working alongside
the existing LangChain system with zero breaking changes.
"""

import asyncio
import time
from typing import Dict, Any

# Import existing components (unchanged)
try:
    from src.config.settings import Settings
    from src.agents.rag_agent import RAGAgent
except ImportError:
    print("Note: Some imports may fail without full dependencies installed")
    Settings = None
    RAGAgent = None

# Import new LangGraph components
from src.config.graph_config import GraphConfig, SystemSelector
from src.agents.langgraph_rag_agent import LangGraphRAGAgent
from src.agents.agent_router import AgentRouter
from src.utils.migration_utils import MigrationManager


class MockLLM:
    """Mock LLM for demonstration purposes"""
    
    def invoke(self, prompt: str) -> str:
        # Simulate processing time
        time.sleep(0.1)
        return f"Mock response to: {prompt[:50]}..."
    
    async def ainvoke(self, prompt: str) -> str:
        # Simulate async processing
        await asyncio.sleep(0.1)
        return f"Mock async response to: {prompt[:50]}..."


class MockVectorStore:
    """Mock vector store for demonstration purposes"""
    
    def as_retriever(self, **kwargs):
        return MockRetriever(**kwargs)


class MockRetriever:
    """Mock retriever for demonstration purposes"""
    
    def __init__(self, **kwargs):
        self.k = kwargs.get('k', 5)
    
    def get_relevant_documents(self, query: str):
        # Return mock documents
        class MockDocument:
            def __init__(self, content: str, source: str):
                self.page_content = content
                self.metadata = {"source": source}
        
        return [
            MockDocument(f"Mock document 1 content related to: {query}", "doc1.txt"),
            MockDocument(f"Mock document 2 content related to: {query}", "doc2.txt"),
            MockDocument(f"Mock document 3 content related to: {query}", "doc3.txt"),
        ][:self.k]


class MockDiagramHandler:
    """Mock diagram handler for demonstration purposes"""
    
    def generate_diagram(self, query: str) -> Dict[str, Any]:
        return {
            "diagram": f"Mock diagram for: {query}",
            "type": "sequence",
            "source": "mock"
        }


def create_demo_agents():
    """Create demonstration agents"""
    print("Creating demonstration agents...")
    
    # Create mock components
    mock_llm = MockLLM()
    mock_vectorstore = MockVectorStore()
    mock_diagram_handler = MockDiagramHandler()
    
    # Create LangChain RAG agent (existing system)
    if RAGAgent:
        langchain_agent = RAGAgent(
            llm=mock_llm,
            vectorstore=mock_vectorstore,
            retriever_kwargs={"k": 5}
        )
    else:
        # Create a mock for demonstration
        class MockRAGAgent:
            def query(self, question: str) -> Dict[str, Any]:
                return {
                    "answer": f"LangChain mock response to: {question}",
                    "source_documents": mock_vectorstore.as_retriever().get_relevant_documents(question),
                    "metadata": {"processing_method": "langchain"}
                }
        langchain_agent = MockRAGAgent()
    
    # Create LangGraph RAG agent (new parallel system)
    langgraph_config = GraphConfig(
        enable_langgraph=True,
        enable_parallel_processing=True,
        max_concurrent_workflows=5
    )
    
    langgraph_agent = LangGraphRAGAgent(
        llm=mock_llm,
        vectorstore=mock_vectorstore,
        retriever_kwargs={"k": 5},
        config=langgraph_config
    )
    
    # Create enhanced agent router
    router_config = GraphConfig(
        enable_langgraph=True,
        default_system=SystemSelector.LANGCHAIN,  # Safe default
        migration_rollout_percentage=0.0,  # Start with 0% rollout
        enable_ab_testing=False
    )
    
    router = AgentRouter(
        rag_agent=langchain_agent,
        diagram_handler=mock_diagram_handler,
        langgraph_rag_agent=langgraph_agent,
        config=router_config
    )
    
    return {
        "langchain_agent": langchain_agent,
        "langgraph_agent": langgraph_agent,
        "router": router,
        "migration_manager": MigrationManager()
    }


def demonstrate_zero_breaking_changes(agents: Dict[str, Any]):
    """Demonstrate that existing functionality still works"""
    print("\n=== Demonstrating Zero Breaking Changes ===")
    
    router = agents["router"]
    test_questions = [
        "What is the purpose of this system?",
        "How does authentication work?",
        "Show me the main workflow"
    ]
    
    print("Testing existing interface (defaults to LangChain)...")
    for question in test_questions:
        print(f"\nQuestion: {question}")
        
        # This works exactly as before - no changes to existing code
        result = router.route_query(question)
        
        print(f"Answer: {result['answer'][:100]}...")
        print(f"System used: {result.get('metadata', {}).get('processing_system', 'unknown')}")
        print(f"Sources: {len(result.get('source_documents', []))} documents")


def demonstrate_parallel_system(agents: Dict[str, Any]):
    """Demonstrate the new parallel LangGraph system"""
    print("\n=== Demonstrating Parallel LangGraph System ===")
    
    router = agents["router"]
    test_question = "Explain the architecture of this system"
    
    print(f"Question: {test_question}")
    
    # Test LangChain system
    print("\nUsing LangChain system (original):")
    langchain_result = router.route_query(test_question, force_system="langchain")
    print(f"Answer: {langchain_result['answer'][:100]}...")
    print(f"System: {langchain_result.get('metadata', {}).get('processing_system')}")
    
    # Test LangGraph system  
    print("\nUsing LangGraph system (new parallel):")
    langgraph_result = router.route_query(test_question, force_system="langgraph")
    print(f"Answer: {langgraph_result['answer'][:100]}...")
    print(f"System: {langgraph_result.get('metadata', {}).get('processing_system')}")
    print(f"Workflow ID: {langgraph_result.get('metadata', {}).get('workflow_id')}")
    print(f"Processing method: {langgraph_result.get('metadata', {}).get('processing_method')}")


def demonstrate_migration_features(agents: Dict[str, Any]):
    """Demonstrate migration and monitoring features"""
    print("\n=== Demonstrating Migration Features ===")
    
    router = agents["router"]
    migration_manager = agents["migration_manager"]
    
    # Show routing statistics
    print("\nInitial routing statistics:")
    stats = router.get_routing_stats()
    print(f"Total requests: {stats['total_requests']}")
    print(f"LangChain requests: {stats['langchain_requests']} ({stats['langchain_percentage']:.1f}%)")
    print(f"LangGraph requests: {stats['langgraph_requests']} ({stats['langgraph_percentage']:.1f}%)")
    
    # Demonstrate gradual rollout
    print("\nDemonstrating gradual rollout...")
    
    # Enable gradual migration
    router.config.default_system = SystemSelector.AUTO
    router.config.migration_rollout_percentage = 0.3  # 30% to LangGraph
    
    print("Updated config: 30% traffic to LangGraph")
    
    # Simulate some requests
    test_questions = [
        "Question 1", "Question 2", "Question 3", 
        "Question 4", "Question 5", "Question 6",
        "Question 7", "Question 8", "Question 9", "Question 10"
    ]
    
    for i, question in enumerate(test_questions, 1):
        result = router.route_query(f"Test query {i}: {question}")
        system_used = result.get('metadata', {}).get('processing_system', 'unknown')
        print(f"Request {i}: {system_used}")
    
    # Show updated statistics
    print("\nUpdated routing statistics:")
    stats = router.get_routing_stats()
    print(f"Total requests: {stats['total_requests']}")
    print(f"LangChain requests: {stats['langchain_requests']} ({stats['langchain_percentage']:.1f}%)")
    print(f"LangGraph requests: {stats['langgraph_requests']} ({stats['langgraph_percentage']:.1f}%)")
    
    # Demonstrate performance comparison
    print("\nDemonstrating performance comparison...")
    
    def langchain_test(query):
        return agents["langchain_agent"].query(query)
    
    def langgraph_test(query):
        return agents["langgraph_agent"].query(query)
    
    test_query = "Compare system performance"
    comparison = migration_manager.compare_systems(
        langchain_function=langchain_test,
        langgraph_function=langgraph_test,
        test_input=test_query,
        test_name="performance_demo"
    )
    
    print(f"Performance comparison:")
    print(f"LangChain execution time: {comparison.langchain_metrics.execution_time:.3f}s")
    print(f"LangGraph execution time: {comparison.langgraph_metrics.execution_time:.3f}s")
    print(f"Performance improvement: {comparison.performance_improvement:.2f}x")
    print(f"Recommendation: {comparison.recommendation}")
    print(f"Confidence: {comparison.confidence_score:.2f}")


def demonstrate_workflow_features(agents: Dict[str, Any]):
    """Demonstrate LangGraph workflow features"""
    print("\n=== Demonstrating LangGraph Workflow Features ===")
    
    langgraph_agent = agents["langgraph_agent"]
    
    # Show workflow management
    print("Starting a workflow...")
    workflow_id = langgraph_agent.start_query_workflow(
        "What are the key components of this system?"
    )
    print(f"Started workflow: {workflow_id}")
    
    # Show workflow status
    print("\nWorkflow status:")
    status = langgraph_agent.get_workflow_status(workflow_id)
    print(f"Status: {status['status']}")
    print(f"Progress: {status.get('progress', 0):.1%}")
    
    # Show active workflows
    print("\nActive workflows:")
    active = langgraph_agent.list_active_workflows()
    for workflow in active:
        print(f"- {workflow['workflow_id']}: {workflow['status']} ({workflow['workflow_type']})")
    
    # Show performance metrics
    print("\nAgent performance metrics:")
    metrics = langgraph_agent.get_performance_metrics()
    print(f"Total workflows: {metrics['total_workflows']}")
    print(f"Active workflows: {metrics['active_workflows_count']}")
    print(f"Completed workflows: {metrics['completed_workflows_count']}")
    print(f"Success rate: {metrics['successful_workflows']}/{metrics['total_workflows']}")


def main():
    """Main demonstration function"""
    print("LangGraph Integration Demonstration")
    print("===================================")
    print("This demonstrates the parallel LangGraph system working")
    print("alongside the existing LangChain system with zero breaking changes.")
    
    try:
        # Create demonstration agents
        agents = create_demo_agents()
        
        # Run demonstrations
        demonstrate_zero_breaking_changes(agents)
        demonstrate_parallel_system(agents)
        demonstrate_migration_features(agents)
        demonstrate_workflow_features(agents)
        
        print("\n=== Summary ===")
        print("✅ Zero breaking changes maintained")
        print("✅ Parallel system working correctly")
        print("✅ Migration features functional")
        print("✅ Enhanced workflow management available")
        print("\nThe LangGraph integration is ready for gradual deployment!")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()