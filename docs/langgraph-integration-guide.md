# LangGraph Integration Guide

This guide explains how to use the new LangGraph integration in the Knowledge Base Agent system. The LangGraph system runs as a **parallel system** alongside the existing LangChain implementation, ensuring zero breaking changes.

## Overview

The LangGraph integration provides:

- **Enhanced Workflow Management**: State-driven workflows with checkpointing and recovery
- **Parallel Processing**: Multi-threaded processing for improved performance
- **Advanced Monitoring**: Comprehensive performance tracking and observability
- **Gradual Migration**: Controlled rollout with automatic fallback capabilities
- **Zero Breaking Changes**: Complete interface compatibility with existing system

## Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Agent Router  │    │  Migration Mgr  │
│                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ LangChain   │ │    │ │ Performance │ │
│ │ RAG Agent   │ │◄───┤ │ Tracking    │ │
│ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ LangGraph   │ │    │ │ Rollback    │ │
│ │ RAG Agent   │ │◄───┤ │ Controls    │ │
│ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘
        │                        │
        ▼                        ▼
┌─────────────────────────────────────────┐
│           LangGraph Workflows           │
│                                         │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐     │
│ │Chunking │ │Embedding│ │  Query  │     │
│ │Workflow │ │Workflow │ │Workflow │     │
│ └─────────┘ └─────────┘ └─────────┘     │
└─────────────────────────────────────────┘
```

## Quick Start

### 1. Basic Configuration

```python
from src.config.graph_config import GraphConfig, SystemSelector

# Create LangGraph configuration
config = GraphConfig(
    enable_langgraph=True,
    default_system=SystemSelector.LANGCHAIN,  # Safe default
    migration_rollout_percentage=0.0,  # Start with 0% rollout
    enable_parallel_processing=True,
    max_concurrent_workflows=10
)
```

### 2. Initialize Agents

```python
from src.agents.langgraph_rag_agent import LangGraphRAGAgent
from src.agents.agent_router import AgentRouter

# Create LangGraph RAG agent (parallel to existing LangChain agent)
langgraph_agent = LangGraphRAGAgent(
    llm=your_llm,
    vectorstore=your_vectorstore,
    config=config
)

# Create enhanced router supporting both systems
router = AgentRouter(
    rag_agent=existing_langchain_agent,  # Keep existing agent
    diagram_handler=diagram_handler,
    langgraph_rag_agent=langgraph_agent,  # Add new agent
    config=config
)
```

### 3. Use Existing Interface (Zero Breaking Changes)

```python
# This works exactly as before - no code changes needed
result = router.route_query("What is the purpose of this system?")

print(result["answer"])
print(f"Processed by: {result['metadata']['processing_system']}")
```

### 4. Force System Selection (Optional)

```python
# Force LangChain system
langchain_result = router.route_query(
    "Test query", 
    force_system="langchain"
)

# Force LangGraph system  
langgraph_result = router.route_query(
    "Test query", 
    force_system="langgraph"
)
```

## Configuration Options

### System Selection

```python
config = GraphConfig(
    # System enabling
    enable_langgraph=True,
    
    # Default system selection
    default_system=SystemSelector.LANGCHAIN,  # LANGCHAIN, LANGGRAPH, AUTO
    
    # Migration controls
    migration_rollout_percentage=0.25,  # 25% traffic to LangGraph
    enable_ab_testing=True,
    
    # Performance settings
    enable_parallel_processing=True,
    max_concurrent_workflows=10
)
```

### Workflow Configuration

```python
from src.config.graph_config import WorkflowConfig

workflow_config = WorkflowConfig(
    # Chunking settings
    chunking_quality_threshold=0.7,
    chunking_max_retries=3,
    chunking_batch_size=10,
    
    # Embedding settings
    embedding_quality_threshold=0.8,
    embedding_batch_size=50,
    enable_multi_model_embeddings=True,
    
    # Retrieval settings
    retrieval_min_results=3,
    retrieval_timeout_seconds=30.0,
    enable_cross_repository_search=True
)
```

## Migration Strategies

### 1. Conservative Approach (Recommended)

```python
# Start with LangGraph disabled, existing system only
config = GraphConfig(
    enable_langgraph=False,  # Keep existing system
    default_system=SystemSelector.LANGCHAIN
)

# Enable LangGraph for testing
config.enable_langgraph = True

# Test specific queries with LangGraph
test_result = router.route_query("test query", force_system="langgraph")

# Gradually increase rollout
config.migration_rollout_percentage = 0.05  # 5%
config.migration_rollout_percentage = 0.25  # 25%
config.migration_rollout_percentage = 1.0   # 100%
```

### 2. A/B Testing Approach

```python
config = GraphConfig(
    enable_langgraph=True,
    default_system=SystemSelector.AUTO,
    enable_ab_testing=True,
    migration_rollout_percentage=0.5  # 50/50 split
)

# Monitor performance
stats = router.get_routing_stats()
print(f"LangChain: {stats['langchain_percentage']:.1f}%")
print(f"LangGraph: {stats['langgraph_percentage']:.1f}%")
```

### 3. Performance-Based Migration

```python
from src.utils.migration_utils import MigrationManager

# Create migration manager
migration_manager = MigrationManager()

# Compare system performance
def test_langchain(query):
    return langchain_agent.query(query)

def test_langgraph(query):
    return langgraph_agent.query(query)

comparison = migration_manager.compare_systems(
    langchain_function=test_langchain,
    langgraph_function=test_langgraph,
    test_input="performance test query"
)

print(f"Performance improvement: {comparison.performance_improvement:.2f}x")
print(f"Recommendation: {comparison.recommendation}")

# Check if should migrate
decision = migration_manager.should_migrate()
if decision["should_migrate"]:
    print(f"Migration recommended: {decision['reason']}")
    # Increase rollout percentage
    new_percentage = decision["recommended_rollout"]
    router.config.migration_rollout_percentage = new_percentage
```

## Advanced Features

### 1. Workflow Management

```python
# Start a specific workflow
workflow_id = langgraph_agent.start_query_workflow(
    "What are the key components of this system?"
)

# Check workflow status
status = langgraph_agent.get_workflow_status(workflow_id)
print(f"Status: {status['status']}")
print(f"Progress: {status['progress']:.1%}")

# List active workflows
active_workflows = langgraph_agent.list_active_workflows()
for workflow in active_workflows:
    print(f"- {workflow['workflow_id']}: {workflow['status']}")
```

### 2. Performance Monitoring

```python
# Get agent performance metrics
metrics = langgraph_agent.get_performance_metrics()
print(f"Total workflows: {metrics['total_workflows']}")
print(f"Success rate: {metrics['successful_workflows']}/{metrics['total_workflows']}")
print(f"Average execution time: {metrics['average_execution_time']:.3f}s")

# Get routing statistics
routing_stats = router.get_routing_stats()
print(f"Total requests: {routing_stats['total_requests']}")
print(f"System selection overrides: {routing_stats['system_selection_overrides']}")
```

### 3. Error Handling and Rollback

```python
# Check if automatic rollback should occur
rollback_decision = migration_manager.should_rollback()
if rollback_decision["should_rollback"]:
    print(f"Rollback recommended: {rollback_decision['reason']}")
    
    # Disable LangGraph or reduce rollout
    router.config.migration_rollout_percentage = 0.0
    # or
    router.config.enable_langgraph = False
```

### 4. Custom Workflow States

```python
from src.workflows.states import QueryState, WorkflowStatus

# Create custom workflow state
custom_state = QueryState(
    workflow_id="custom-001",
    workflow_type="query",
    user_query="Custom query",
    initial_k=10,
    parallel_retrieval=True
)

# Process with custom configuration
result = await langgraph_agent.process_workflow(custom_state)
```

## Migration Checklist

### Phase 1: Preparation
- [ ] Install LangGraph dependencies: `pip install -r requirements-langgraph.txt`
- [ ] Configure LangGraph settings in your configuration
- [ ] Initialize LangGraph agents alongside existing agents
- [ ] Set up monitoring and logging

### Phase 2: Testing
- [ ] Test LangGraph agents with forced system selection
- [ ] Compare performance between systems
- [ ] Validate response quality and accuracy
- [ ] Test error handling and fallback mechanisms

### Phase 3: Gradual Rollout
- [ ] Start with 5% traffic to LangGraph
- [ ] Monitor performance metrics and error rates
- [ ] Gradually increase rollout percentage
- [ ] Implement automatic rollback triggers

### Phase 4: Full Migration
- [ ] Achieve 100% rollout to LangGraph
- [ ] Monitor system stability
- [ ] Deprecate LangChain components (optional)
- [ ] Clean up unused code and dependencies

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Install required dependencies
   pip install -r requirements-langgraph.txt
   ```

2. **Configuration Errors**
   ```python
   # Validate configuration
   config = GraphConfig()
   print(config.model_dump())  # Check all settings
   ```

3. **Performance Issues**
   ```python
   # Check performance metrics
   metrics = langgraph_agent.get_performance_metrics()
   if metrics['average_execution_time'] > 5.0:
       # Investigate slow workflows
       pass
   ```

4. **Migration Issues**
   ```python
   # Check migration status
   status = migration_manager.get_migration_status()
   print(status)
   
   # Force rollback if needed
   router.config.migration_rollout_percentage = 0.0
   ```

### Debugging

```python
# Enable debug logging
import logging
logging.getLogger('src.agents.langgraph_rag_agent').setLevel(logging.DEBUG)
logging.getLogger('src.utils.migration_utils').setLevel(logging.DEBUG)

# Check workflow execution history
workflow_state = langgraph_agent.completed_workflows[workflow_id]
for execution in workflow_state.node_execution_history:
    print(f"Node: {execution['node']}, Time: {execution['execution_time']:.3f}s")
```

## Best Practices

1. **Start Conservative**: Begin with LangGraph disabled and gradually enable features
2. **Monitor Continuously**: Track performance metrics and error rates
3. **Test Thoroughly**: Compare results between systems before migration
4. **Plan Rollback**: Always have a rollback plan and automatic triggers
5. **Document Changes**: Keep track of configuration changes and their impacts

## API Reference

For detailed API documentation, see:
- [GraphConfig API](src/config/graph_config.py)
- [LangGraphRAGAgent API](src/agents/langgraph_rag_agent.py)
- [AgentRouter API](src/agents/agent_router.py)
- [MigrationManager API](src/utils/migration_utils.py)

## Examples

See the [examples directory](examples/) for complete working examples:
- `langgraph_demo.py`: Complete demonstration of parallel system functionality
- Additional examples coming in Phase 2 implementation