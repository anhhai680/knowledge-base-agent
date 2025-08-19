"""
Test ReAct Agent

Tests for the ReAct agent implementation including tool usage,
action planning, and execution monitoring.
"""

import pytest
from unittest.mock import Mock, MagicMock
from langchain.docstore.document import Document

from src.agents.react_agent import (
    ReActAgent, ActionType, ActionStatus, Action, ReasoningStep,
    ActionPlanner, ActionExecutor, ReasoningEngine
)
from src.agents.tools import get_default_tools, SearchTool, CalculatorTool
from src.config.react_agent_config import ReActAgentConfig, get_react_config

class TestAction:
    """Test Action dataclass"""
    
    def test_action_creation(self):
        """Test creating Action objects"""
        action = Action(
            action_type=ActionType.SEARCH,
            name="web_search",
            description="Search for information",
            parameters={"query": "test query"}
        )
        
        assert action.action_type == ActionType.SEARCH
        assert action.name == "web_search"
        assert action.description == "Search for information"
        assert action.parameters == {"query": "test query"}
        assert action.status == ActionStatus.PENDING
        assert action.result is None
        assert action.error is None
    
    def test_action_status_updates(self):
        """Test action status updates"""
        action = Action(
            action_type=ActionType.CALCULATE,
            name="calculator",
            description="Calculate expression",
            parameters={"expression": "2 + 2"}
        )
        
        # Update status
        action.status = ActionStatus.EXECUTING
        assert action.status == ActionStatus.EXECUTING
        
        action.status = ActionStatus.COMPLETED
        assert action.status == ActionStatus.COMPLETED
        
        action.status = ActionStatus.FAILED
        assert action.status == ActionStatus.FAILED

class TestReasoningStep:
    """Test ReasoningStep dataclass"""
    
    def test_reasoning_step_creation(self):
        """Test creating ReasoningStep objects"""
        step = ReasoningStep(
            step_number=1,
            thought="This is a test thought",
            action=None,
            observation="No observation yet",
            reasoning="Initial reasoning"
        )
        
        assert step.step_number == 1
        assert step.thought == "This is a test thought"
        assert step.action is None
        assert step.observation == "No observation yet"
        assert step.reasoning == "Initial reasoning"
    
    def test_reasoning_step_with_action(self):
        """Test ReasoningStep with an action"""
        action = Action(
            action_type=ActionType.SEARCH,
            name="web_search",
            description="Search for information",
            parameters={"query": "test"}
        )
        
        step = ReasoningStep(
            step_number=2,
            thought="Planning to search",
            action=action,
            observation="Action planned",
            reasoning="Need to search for more information"
        )
        
        assert step.action is not None
        assert step.action.name == "web_search"
        assert step.reasoning == "Need to search for more information"

class TestActionPlanner:
    """Test ActionPlanner class"""
    
    def setup_method(self):
        """Setup test method"""
        self.mock_llm = Mock()
        # Fix Mock setup - set names as string values, not Mock objects
        self.mock_tools = [
            Mock(name="web_search", description="Search tool"),
            Mock(name="calculator", description="Calculator tool"),
            Mock(name="code_executor", description="Code execution tool")
        ]
        # Set the name attributes as strings
        self.mock_tools[0].name = "web_search"
        self.mock_tools[1].name = "calculator"
        self.mock_tools[2].name = "code_executor"
        
        self.config = {"max_tool_calls_per_iteration": 3}
        self.planner = ActionPlanner(self.mock_llm, self.mock_tools, self.config)
    
    def test_extract_search_query(self):
        """Test search query extraction"""
        reasoning = "I need to search for Python tutorials"
        question = "What is Python?"
        
        query = self.planner._extract_search_query(reasoning, question)
        assert "Python tutorials" in query
    
    def test_extract_calculation(self):
        """Test calculation expression extraction"""
        reasoning = "I need to calculate 15 + 27 * 3"
        
        expression = self.planner._extract_calculation(reasoning)
        assert "15 + 27 * 3" in expression
    
    def test_extract_code(self):
        """Test code extraction"""
        reasoning = "I need to execute this code: ```print('Hello')```"
        
        code = self.planner._extract_code(reasoning)
        assert "print('Hello')" in code
    
    def test_plan_action_search(self):
        """Test planning search action"""
        reasoning = "I need to search for information about machine learning"
        # Fix Mock setup - set name as a string value, not a Mock object
        mock_tool = Mock()
        mock_tool.name = "web_search"  # Set as string, not Mock
        mock_tool.description = "Search tool"
        available_tools = [mock_tool]
        context = []
        question = "What is machine learning?"
        
        action = self.planner.plan_action(reasoning, available_tools, context, question)
        
        assert action is not None
        assert action.action_type == ActionType.SEARCH
        assert action.name == "web_search"
    
    def test_plan_action_calculate(self):
        """Test planning calculation action"""
        reasoning = "I need to calculate the result of 10 * 5"
        # Fix Mock setup - set name as a string value, not a Mock object
        mock_tool = Mock()
        mock_tool.name = "calculator"  # Set as string, not Mock
        mock_tool.description = "Calculator tool"
        available_tools = [mock_tool]
        context = []
        question = "What is 10 * 5?"
        
        action = self.planner.plan_action(reasoning, available_tools, context, question)
        
        assert action is not None
        assert action.action_type == ActionType.CALCULATE
        assert action.name == "calculator"
    
    def test_plan_action_no_tools(self):
        """Test planning action with no available tools"""
        reasoning = "I need to search for information"
        available_tools = []
        context = []
        question = "Test question"
        
        action = self.planner.plan_action(reasoning, available_tools, context, question)
        
        assert action is None

class TestActionExecutor:
    """Test ActionExecutor class"""
    
    def setup_method(self):
        """Setup test method"""
        # Fix Mock setup - set name as a string value, not a Mock object
        mock_tool = Mock()
        mock_tool.name = "test_tool"  # Set as string, not Mock
        mock_tool.run = Mock(return_value="Tool result")
        
        self.mock_tools = [mock_tool]
        self.config = {"action_timeout": 30.0}
        self.executor = ActionExecutor(self.mock_tools, self.config)
    
    def test_execute_action_success(self):
        """Test successful action execution"""
        action = Action(
            action_type=ActionType.SEARCH,
            name="test_tool",
            description="Test action",
            parameters={"param": "value"}
        )
        
        result = self.executor.execute_action(action)
        
        assert result["status"] == "success"
        assert result["result"] == "Tool result"
        assert result["tool_name"] == "test_tool"
        assert action.status == ActionStatus.COMPLETED
        assert action.result == result  # action.result should be the full result dict
    
    def test_execute_action_tool_not_found(self):
        """Test action execution with non-existent tool"""
        action = Action(
            action_type=ActionType.SEARCH,
            name="non_existent_tool",
            description="Test action",
            parameters={"param": "value"}
        )
        
        result = self.executor.execute_action(action)
        
        assert result["status"] == "error"
        assert "not found" in result["error"]
        assert action.status == ActionStatus.FAILED
        assert action.error is not None
    
    def test_execute_action_tool_error(self):
        """Test action execution when tool raises an error"""
        # Create a tool that raises an error
        error_tool = Mock(name="error_tool", run=Mock(side_effect=Exception("Tool error")))
        self.executor.tools = [error_tool]
        self.executor.tool_map = {"error_tool": error_tool}
        
        action = Action(
            action_type=ActionType.SEARCH,
            name="error_tool",
            description="Test action",
            parameters={"param": "value"}
        )
        
        result = self.executor.execute_action(action)
        
        assert result["status"] == "error"
        assert "Tool error" in result["error"]
        assert action.status == ActionStatus.FAILED

class TestReasoningEngine:
    """Test ReasoningEngine class"""
    
    def setup_method(self):
        """Setup test method"""
        self.mock_llm = Mock()
        self.config = {"max_reasoning_steps": 8, "verbose_reasoning": True}
        self.engine = ReasoningEngine(self.mock_llm, self.config)
    
    def test_reasoning_generation(self):
        """Test reasoning generation"""
        question = "What is Python?"
        context = [Document(page_content="Python is a language", metadata={})]
        observation = "Current state observation"
        action_history = []
        available_tools = []
        iteration = 1
        
        reasoning_step = self.engine.reason(
            question, context, observation, action_history, available_tools, iteration
        )
        
        assert reasoning_step.step_number == 1
        assert "Step 1" in reasoning_step.thought
        assert reasoning_step.observation == observation
        assert reasoning_step.reasoning is not None
    
    def test_should_plan_action_early_iteration(self):
        """Test action planning decision for early iterations"""
        should_plan = self.engine._should_plan_action(1, [], [])
        assert should_plan is True
    
    def test_should_plan_action_late_iteration(self):
        """Test action planning decision for late iterations"""
        should_plan = self.engine._should_plan_action(5, [Mock(), Mock()], [Mock(), Mock(), Mock()])
        assert should_plan is False
    
    def test_should_plan_action_few_context(self):
        """Test action planning decision when context is limited"""
        should_plan = self.engine._should_plan_action(4, [], [Mock()])
        assert should_plan is True
    
    def test_simple_action_planning(self):
        """Test simple action planning"""
        question = "Search for information"
        context = []
        # Fix Mock setup - set name as a string value, not a Mock object
        mock_tool = Mock()
        mock_tool.name = "web_search"  # Set as string, not Mock
        mock_tool.description = "Search tool"
        available_tools = [mock_tool]
        
        action = self.engine._plan_simple_action(question, context, available_tools)
        
        assert action is not None
        assert action.action_type == ActionType.SEARCH
        assert action.name == "web_search"

class TestReActAgent:
    """Test ReAct Agent"""
    
    def setup_method(self):
        """Setup test method"""
        self.mock_llm = Mock()
        self.mock_vectorstore = Mock()
        self.mock_vectorstore.as_retriever.return_value = Mock()
        self.mock_vectorstore.similarity_search.return_value = []
        
        # Mock QA chain
        self.mock_qa_chain = Mock()
        self.mock_qa_chain.__call__ = Mock(return_value={
            "result": "Test result",
            "source_documents": []
        })
        self.mock_qa_chain.invoke = Mock(return_value={
            "answer": "Test answer",
            "context": []
        })
        
        # Create ReAct agent with tools
        self.tools = get_default_tools()
        self.agent = ReActAgent(
            self.mock_llm,
            self.mock_vectorstore,
            tools=self.tools
        )
        self.agent.qa_chain = self.mock_qa_chain
    
    def test_react_agent_initialization(self):
        """Test ReAct agent initialization"""
        assert len(self.agent.tools) == 5  # Default tools
        assert self.agent.tool_map is not None
        assert self.agent.action_planner is not None
        assert self.agent.action_executor is not None
        assert self.agent.reasoning_engine is not None
    
    def test_should_use_react_high_complexity(self):
        """Test ReAct decision for high complexity queries"""
        query_analysis = Mock()
        query_analysis.complexity = "high"
        question = "Simple question"
        
        should_use = self.agent._should_use_react(query_analysis, question)
        assert should_use is True
    
    def test_should_use_react_tool_indicators(self):
        """Test ReAct decision for queries with tool indicators"""
        query_analysis = Mock()
        query_analysis.complexity = "medium"
        question = "I need to calculate 2 + 2"
        
        should_use = self.agent._should_use_react(query_analysis, question)
        assert should_use is True
    
    def test_should_use_react_troubleshooting_intent(self):
        """Test ReAct decision for troubleshooting intent"""
        query_analysis = Mock()
        query_analysis.complexity = "medium"
        query_analysis.intent = "troubleshooting"
        question = "How to fix this issue?"
        
        should_use = self.agent._should_use_react(query_analysis, question)
        assert should_use is True
    
    def test_should_use_react_simple_query(self):
        """Test ReAct decision for simple queries"""
        query_analysis = Mock()
        query_analysis.complexity = "low"
        query_analysis.intent = "general"
        question = "What is this?"
        
        should_use = self.agent._should_use_react(query_analysis, question)
        assert should_use is False
    
    def test_observe_current_state(self):
        """Test current state observation"""
        question = "Test question"
        context = [Mock(), Mock()]
        action_history = []
        
        observation = self.agent._observe_current_state(question, context, action_history)
        
        assert "Current question: Test question" in observation
        assert "Context documents: 2" in observation
        assert "Actions executed: 0" in observation
    
    def test_observe_current_state_with_actions(self):
        """Test current state observation with action history"""
        question = "Test question"
        context = [Mock()]
        # Fix Mock setup - create proper Action objects instead of Mock objects
        action1 = Action(
            action_type=ActionType.SEARCH,
            name="action1",
            description="Test action 1",
            parameters={}
        )
        action2 = Action(
            action_type=ActionType.CALCULATE,
            name="action2",
            description="Test action 2",
            parameters={}
        )
        action_history = [action1, action2]
        
        observation = self.agent._observe_current_state(question, context, action_history)
        
        assert "Recent actions: action1(search), action2(calculate)" in observation
    
    def test_should_stop_reasoning_final_answer(self):
        """Test reasoning stop condition for final answer"""
        reasoning_step = ReasoningStep(
            step_number=3,
            thought="Test thought",
            reasoning="This is the final answer to the question"
        )
        
        should_stop = self.agent._should_stop_reasoning(reasoning_step)
        assert should_stop is True
    
    def test_should_stop_reasoning_max_steps(self):
        """Test reasoning stop condition for max steps"""
        # Set max reasoning steps to 3
        self.agent.react_config["max_reasoning_steps"] = 3
        
        reasoning_step = ReasoningStep(
            step_number=3,
            thought="Test thought",
            reasoning="Still reasoning"
        )
        
        should_stop = self.agent._should_stop_reasoning(reasoning_step)
        
        assert should_stop is True
    
    def test_should_stop_reasoning_continue(self):
        """Test reasoning continue condition"""
        reasoning_step = ReasoningStep(
            step_number=2,
            thought="Test thought",
            reasoning="Still reasoning"
        )
        
        should_stop = self.agent._should_stop_reasoning(reasoning_step)
        assert should_stop is False
    
    def test_add_tool(self):
        """Test adding a new tool"""
        # Create a proper tool with string name
        new_tool = Mock()
        new_tool.name = "new_tool"  # Set as string, not Mock
        new_tool.description = "New tool"
        
        self.agent.add_tool(new_tool)
        
        assert "new_tool" in self.agent.tool_map
        assert new_tool in self.agent.tools
    
    def test_remove_tool(self):
        """Test removing a tool"""
        tool_name = "web_search"
        
        self.agent.remove_tool(tool_name)
        
        assert tool_name not in self.agent.tool_map
        assert not any(tool.name == tool_name for tool in self.agent.tools)
    
    def test_get_tool_info(self):
        """Test getting tool information"""
        tool_info = self.agent.get_tool_info()
        
        # Should have 5 tools (default tools)
        assert len(tool_info) == 5
        assert all("name" in info for info in tool_info)
        assert all("description" in info for info in tool_info)
        assert all("type" in info for info in tool_info)

if __name__ == "__main__":
    pytest.main([__file__])
