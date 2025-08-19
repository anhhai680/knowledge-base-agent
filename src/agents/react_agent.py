"""
ReAct Agent Implementation

Implements a ReAct (Reasoning and Acting) agent that extends the enhanced RAG agent
with tool usage capabilities, action planning, and execution monitoring.
"""

from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import json
import re
from langchain.tools import BaseTool
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from ..utils.logging import get_logger
from .rag_agent import RAGAgent, QueryAnalysis

logger = get_logger(__name__)

class ActionType(Enum):
    """Types of actions the ReAct agent can perform"""
    SEARCH = "search"
    CALCULATE = "calculate"
    EXECUTE_CODE = "execute_code"
    API_CALL = "api_call"
    FILE_OPERATION = "file_operation"
    CUSTOM = "custom"

class ActionStatus(Enum):
    """Status of action execution"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class Action:
    """Represents an action to be executed"""
    action_type: ActionType
    name: str
    description: str
    parameters: Dict[str, Any]
    status: ActionStatus = ActionStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None

@dataclass
class ReasoningStep:
    """Represents a reasoning step in the ReAct process"""
    step_number: int
    thought: str
    action: Optional[Action] = None
    observation: Optional[str] = None
    reasoning: Optional[str] = None

class ReActAgent(RAGAgent):
    """
    ReAct (Reasoning and Acting) Agent that extends RAG capabilities with tool usage
    
    The ReAct agent follows the pattern:
    1. Observe: Analyze the current situation
    2. Think: Reason about what needs to be done
    3. Act: Execute actions using available tools
    4. Repeat: Continue until the goal is achieved
    """
    
    def __init__(self, llm, vectorstore, tools: Optional[List[BaseTool]] = None, 
                 retriever_kwargs=None, enhancement_config=None, react_config=None):
        super().__init__(llm, vectorstore, retriever_kwargs, enhancement_config)
        
        # ReAct-specific configuration
        self.react_config = react_config or self._get_default_react_config()
        
        # Available tools
        self.tools = tools or []
        self.tool_map = {tool.name: tool for tool in self.tools}
        
        # ReAct state
        self.reasoning_chain: List[ReasoningStep] = []
        self.action_history: List[Action] = []
        self.max_iterations = self.react_config.get("max_iterations", 10)
        self.iteration_count = 0
        
        # Initialize ReAct components
        self.action_planner = ActionPlanner(llm, self.tools, self.react_config)
        self.action_executor = ActionExecutor(self.tools, self.react_config)
        self.reasoning_engine = ReasoningEngine(llm, self.react_config)
    
    def _get_default_react_config(self) -> Dict[str, Any]:
        """Get default ReAct configuration"""
        return {
            "max_iterations": 10,
            "max_reasoning_steps": 8,
            "action_timeout": 30.0,
            "enable_tool_usage": True,
            "enable_action_planning": True,
            "enable_execution_monitoring": True,
            "safety_checks": True,
            "verbose_reasoning": True,
            "max_tool_calls_per_iteration": 3,
            "reasoning_model": "chain_of_thought",
            "action_validation": True
        }
    
    def process_query(self, question: str) -> Dict[str, Any]:
        """
        Enhanced query processing with ReAct capabilities
        
        This method implements the full ReAct loop:
        1. Initial reasoning and planning
        2. Action execution and observation
        3. Iterative refinement until goal completion
        """
        logger.info(f"Processing ReAct query: {question[:100]}...")
        
        try:
            # Initialize ReAct state
            self.reasoning_chain = []
            self.action_history = []
            self.iteration_count = 0
            
            # Step 1: Initial query analysis (inherited from RAG agent)
            query_analysis = self._analyze_query(question)
            logger.info(f"Query analysis: intent={query_analysis.intent}, complexity={query_analysis.complexity}")
            
            # Step 2: Determine if ReAct processing is needed
            if self._should_use_react(query_analysis, question):
                logger.info("Using ReAct processing for complex query")
                return self._process_with_react(question, query_analysis)
            else:
                logger.info("Using standard RAG processing for simple query")
                return super().process_query(question)
                
        except Exception as e:
            logger.error(f"ReAct query processing failed: {str(e)}")
            return self._fallback_to_rag(question, e)
    
    def _should_use_react(self, query_analysis: QueryAnalysis, question: str) -> bool:
        """Determine if ReAct processing is needed for this query"""
        # Use ReAct for complex queries that might benefit from tool usage
        if query_analysis.complexity == "high":
            return True
        
        # Use ReAct for queries that might need external tools
        tool_indicators = [
            "calculate", "compute", "execute", "run", "call", "fetch",
            "download", "upload", "create", "modify", "delete", "search",
            "api", "http", "url", "file", "database", "query"
        ]
        
        question_lower = question.lower()
        if any(indicator in question_lower for indicator in tool_indicators):
            return True
        
        # Use ReAct for queries with specific intents that benefit from tools
        if query_analysis.intent in ["troubleshooting", "architecture"]:
            return True
        
        return False
    
    def _process_with_react(self, question: str, query_analysis: QueryAnalysis) -> Dict[str, Any]:
        """Process query using the ReAct methodology"""
        logger.info("Starting ReAct processing loop")
        
        # Initial context from RAG
        initial_context = self._build_context_with_reasoning(question, query_analysis)
        current_context = initial_context
        current_question = question
        
        while self.iteration_count < self.max_iterations:
            self.iteration_count += 1
            logger.info(f"ReAct iteration {self.iteration_count}/{self.max_iterations}")
            
            # Step 1: Observe current state
            observation = self._observe_current_state(current_question, current_context, self.action_history)
            
            # Step 2: Think and plan next actions
            reasoning_step = self.reasoning_engine.reason(
                question=current_question,
                context=current_context,
                observation=observation,
                action_history=self.action_history,
                available_tools=self.tools,
                iteration=self.iteration_count
            )
            
            self.reasoning_chain.append(reasoning_step)
            
            # Step 3: Check if we should stop
            if self._should_stop_reasoning(reasoning_step):
                logger.info("ReAct reasoning complete, generating final response")
                break
            
            # Step 4: Execute planned actions
            if reasoning_step.action:
                action_result = self.action_executor.execute_action(reasoning_step.action)
                reasoning_step.observation = action_result.get("result", "Action completed")
                reasoning_step.action.status = ActionStatus.COMPLETED
                reasoning_step.action.result = action_result
                
                self.action_history.append(reasoning_step.action)
                
                # Update context with action results
                current_context = self._update_context_with_action_results(
                    current_context, action_result, reasoning_step.action
                )
                
                # Refine question based on new information
                current_question = self._refine_question_based_on_actions(
                    question, self.action_history, current_context
                )
            else:
                logger.info("No action planned, continuing with reasoning")
        
        # Generate final response
        final_response = self._generate_react_response(question, current_context, query_analysis)
        
        # Add ReAct metadata
        final_response.update({
            "react_metadata": {
                "iterations": self.iteration_count,
                "reasoning_steps": len(self.reasoning_chain),
                "actions_executed": len(self.action_history),
                "reasoning_chain": [step.__dict__ for step in self.reasoning_chain],
                "action_history": [action.__dict__ for action in self.action_history]
            }
        })
        
        return final_response
    
    def _observe_current_state(self, question: str, context: List, action_history: List[Action]) -> str:
        """Observe the current state for reasoning"""
        observation_parts = [
            f"Current question: {question}",
            f"Context documents: {len(context)}",
            f"Actions executed: {len(action_history)}"
        ]
        
        if action_history:
            recent_actions = action_history[-3:]  # Last 3 actions
            action_summaries = []
            for a in recent_actions:
                if hasattr(a, 'name') and hasattr(a, 'action_type'):
                    if isinstance(a.name, str) and hasattr(a.action_type, 'value'):
                        action_summaries.append(f"{a.name}({a.action_type.value})")
                    else:
                        action_summaries.append(f"action({getattr(a.action_type, 'value', 'unknown')})")
                else:
                    action_summaries.append("action(unknown)")
            
            if action_summaries:
                observation_parts.append(f"Recent actions: {', '.join(action_summaries)}")
        
        return "; ".join(observation_parts)
    
    def _should_stop_reasoning(self, reasoning_step: ReasoningStep) -> bool:
        """Determine if ReAct reasoning should stop"""
        # Stop if we have a clear answer
        if reasoning_step.reasoning and any(phrase in reasoning_step.reasoning.lower() 
                                         for phrase in ["final answer", "conclusion", "answer is"]):
            return True
        
        # Stop if no action is planned and we have sufficient context
        if not reasoning_step.action and len(self.reasoning_chain) >= 3:
            return True
        
        # Stop if we've reached max reasoning steps
        max_steps = self.react_config.get("max_reasoning_steps", 8)
        if reasoning_step.step_number >= max_steps:
            return True
        
        return False
    
    def _update_context_with_action_results(self, context: List, action_result: Dict, action: Action) -> List:
        """Update context with results from executed actions"""
        # Create a new document from action results
        if action_result and "result" in action_result:
            result_content = f"Action {action.name} ({action.action_type.value}) result: {action_result['result']}"
            
            # Add to context (this would typically be added to the vector store)
            # For now, we'll just return the enhanced context
            enhanced_context = context.copy()
            # In a real implementation, you'd add the result to the vector store
            # and retrieve updated context
            
            return enhanced_context
        
        return context
    
    def _refine_question_based_on_actions(self, original_question: str, action_history: List[Action], 
                                         context: List) -> str:
        """Refine the question based on executed actions and new context"""
        if not action_history:
            return original_question
        
        # Simple refinement: add context about what we've learned
        recent_actions = action_history[-2:]  # Last 2 actions
        action_summary = ", ".join([f"executed {a.name}" for a in recent_actions])
        
        refined_question = f"{original_question} (After {action_summary})"
        return refined_question
    
    def _generate_react_response(self, question: str, context: List, query_analysis: QueryAnalysis) -> Dict[str, Any]:
        """Generate final response incorporating ReAct reasoning and actions"""
        # Use the enhanced RAG response generation
        response = self._generate_response_with_reasoning(question, context, query_analysis)
        
        # Enhance with ReAct insights
        if self.reasoning_chain:
            final_reasoning = self.reasoning_chain[-1]
            if final_reasoning.reasoning:
                response["answer"] += f"\n\n**ReAct Reasoning Summary**: {final_reasoning.reasoning}"
        
        return response
    
    def _fallback_to_rag(self, question: str, error: Exception) -> Dict[str, Any]:
        """Fallback to standard RAG processing if ReAct fails"""
        logger.info("Falling back to standard RAG processing")
        try:
            return super().process_query(question)
        except Exception as fallback_error:
            logger.error(f"Fallback RAG also failed: {str(fallback_error)}")
            return {
                "answer": "I encountered an error while processing your query. Please try again.",
                "source_documents": [],
                "status": "error",
                "num_sources": 0,
                "error": str(error),
                "react_metadata": {
                    "iterations": 0,
                    "reasoning_steps": 0,
                    "actions_executed": 0,
                    "fallback_used": True
                }
            }
    
    def add_tool(self, tool: BaseTool):
        """Add a new tool to the ReAct agent"""
        self.tools.append(tool)
        if hasattr(tool, 'name') and isinstance(tool.name, str):
            self.tool_map[tool.name] = tool
            logger.info(f"Added tool: {tool.name}")
        else:
            logger.warning("Tool added but name is not a string, skipping tool_map update")
    
    def remove_tool(self, tool_name: str):
        """Remove a tool from the ReAct agent"""
        if tool_name in self.tool_map:
            del self.tool_map[tool_name]
            self.tools = [tool for tool in self.tools if not (hasattr(tool, 'name') and tool.name == tool_name)]
            logger.info(f"Removed tool: {tool_name}")
        else:
            logger.warning(f"Tool {tool_name} not found in tool_map")
    
    def get_tool_info(self) -> List[Dict[str, Any]]:
        """Get information about available tools"""
        tool_info = []
        for tool in self.tools:
            if hasattr(tool, 'name') and hasattr(tool, 'description'):
                tool_info.append({
                    "name": tool.name,
                    "description": tool.description,
                    "type": type(tool).__name__
                })
            else:
                # Handle Mock objects or tools without proper attributes
                tool_info.append({
                    "name": getattr(tool, 'name', 'unknown'),
                    "description": getattr(tool, 'description', 'No description'),
                    "type": type(tool).__name__
                })
        return tool_info

class ActionPlanner:
    """Plans actions based on reasoning and available tools"""
    
    def __init__(self, llm, tools: List[BaseTool], config: Dict[str, Any]):
        self.llm = llm
        self.tools = tools
        self.config = config
    
    def plan_action(self, reasoning: str, available_tools: List[BaseTool], 
                   context: List, question: str) -> Optional[Action]:
        """Plan the next action based on reasoning"""
        if not available_tools:
            return None
        
        # Simple action planning based on reasoning content
        # In a real implementation, this would use the LLM to plan actions
        
        # Check for common action patterns
        if "search" in reasoning.lower() or "find" in reasoning.lower():
            # Look for search tools - handle Mock objects properly
            search_tools = []
            for tool in available_tools:
                if hasattr(tool, 'name') and isinstance(tool.name, str):
                    if "search" in tool.name.lower():
                        search_tools.append(tool)
            
            if search_tools:
                return Action(
                    action_type=ActionType.SEARCH,
                    name=search_tools[0].name,
                    description=f"Search for information: {reasoning}",
                    parameters={"query": self._extract_search_query(reasoning, question)}
                )
        
        elif "calculate" in reasoning.lower() or "compute" in reasoning.lower():
            # Look for calculation tools - handle Mock objects properly
            calc_tools = []
            for tool in available_tools:
                if hasattr(tool, 'name') and isinstance(tool.name, str):
                    if "calc" in tool.name.lower() or "math" in tool.name.lower():
                        calc_tools.append(tool)
            
            if calc_tools:
                return Action(
                    action_type=ActionType.CALCULATE,
                    name=calc_tools[0].name,
                    description=f"Perform calculation: {reasoning}",
                    parameters={"expression": self._extract_calculation(reasoning)}
                )
        
        elif "execute" in reasoning.lower() or "run" in reasoning.lower():
            # Look for execution tools - handle Mock objects properly
            exec_tools = []
            for tool in available_tools:
                if hasattr(tool, 'name') and isinstance(tool.name, str):
                    if "exec" in tool.name.lower() or "run" in tool.name.lower():
                        exec_tools.append(tool)
            
            if exec_tools:
                return Action(
                    action_type=ActionType.EXECUTE_CODE,
                    name=exec_tools[0].name,
                    description=f"Execute code: {reasoning}",
                    parameters={"code": self._extract_code(reasoning)}
                )
        
        return None
    
    def _extract_search_query(self, reasoning: str, question: str) -> str:
        """Extract search query from reasoning"""
        # Simple extraction - in practice, use LLM for better extraction
        if "search for" in reasoning.lower():
            start = reasoning.lower().find("search for") + 11
            end = reasoning.find(".", start)
            if end == -1:
                end = len(reasoning)
            return reasoning[start:end].strip()
        return question
    
    def _extract_calculation(self, reasoning: str) -> str:
        """Extract calculation expression from reasoning"""
        # Simple extraction - look for mathematical expressions
        import re
        math_pattern = r'[\d\+\-\*\/\(\)\s]+'
        matches = re.findall(math_pattern, reasoning)
        if matches:
            # Find the longest match that looks like a calculation
            longest_match = max(matches, key=len)
            # Ensure it has at least one operator
            if any(op in longest_match for op in ['+', '-', '*', '/']):
                return longest_match.strip()
        return "1 + 1"  # Default fallback
    
    def _extract_code(self, reasoning: str) -> str:
        """Extract code from reasoning"""
        # Simple extraction - look for code blocks
        if "```" in reasoning:
            start = reasoning.find("```") + 3
            end = reasoning.find("```", start)
            if end != -1:
                return reasoning[start:end].strip()
        return "print('Hello, World!')"  # Default fallback

class ActionExecutor:
    """Executes planned actions using available tools"""
    
    def __init__(self, tools: List[BaseTool], config: Dict[str, Any]):
        self.tools = tools
        self.config = config
        self.tool_map = {tool.name: tool for tool in tools}
    
    def execute_action(self, action: Action) -> Dict[str, Any]:
        """Execute a planned action"""
        try:
            action.status = ActionStatus.EXECUTING
            
            if action.name not in self.tool_map:
                raise ValueError(f"Tool '{action.name}' not found")
            
            tool = self.tool_map[action.name]
            
            # Execute the tool
            tool_result = tool.run(**action.parameters)
            
            # Create the full result dictionary
            full_result = {
                "status": "success",
                "result": tool_result,
                "tool_name": action.name,
                "execution_time": 0.0  # Would measure actual time in practice
            }
            
            action.status = ActionStatus.COMPLETED
            action.result = full_result
            
            return full_result
            
        except Exception as e:
            action.status = ActionStatus.FAILED
            action.error = str(e)
            
            return {
                "status": "error",
                "error": str(e),
                "tool_name": action.name
            }

class ReasoningEngine:
    """Manages the reasoning process for the ReAct agent"""
    
    def __init__(self, llm, config: Dict[str, Any]):
        self.llm = llm
        self.config = config
    
    def reason(self, question: str, context: List, observation: str, 
               action_history: List[Action], available_tools: List[Action], 
               iteration: int) -> ReasoningStep:
        """Generate reasoning for the next step"""
        
        # Simple reasoning generation - in practice, use LLM for sophisticated reasoning
        reasoning_parts = [
            f"Step {iteration}: Analyzing the current situation",
            f"Observation: {observation}",
            f"Available tools: {len(available_tools)}",
            f"Previous actions: {len(action_history)}"
        ]
        
        thought = " ".join(reasoning_parts)
        
        # Determine if we should plan an action
        should_act = self._should_plan_action(iteration, action_history, context)
        
        if should_act:
            # Simple action planning
            action = self._plan_simple_action(question, context, available_tools)
            reasoning = f"Based on the analysis, I should {action.description if action else 'continue reasoning'}"
        else:
            action = None
            reasoning = "I have sufficient information to provide an answer"
        
        return ReasoningStep(
            step_number=iteration,
            thought=thought,
            action=action,
            observation=observation,  # Include the observation
            reasoning=reasoning
        )
    
    def _should_plan_action(self, iteration: int, action_history: List[Action], context: List) -> bool:
        """Determine if we should plan an action"""
        # Plan actions in early iterations
        if iteration <= 3:
            return True
        
        # Plan actions if we have few context documents
        if len(context) < 3:
            return True
        
        # Plan actions if we haven't executed many actions yet
        if len(action_history) < 2:
            return True
        
        return False
    
    def _plan_simple_action(self, question: str, context: List, available_tools: List[Action]) -> Optional[Action]:
        """Plan a simple action based on available tools"""
        if not available_tools:
            return None
        
        # Simple action selection based on question content
        question_lower = question.lower()
        
        # Fix Mock object iteration issue by checking if tool.name is a string
        for tool in available_tools:
            if hasattr(tool, 'name') and isinstance(tool.name, str):
                if "search" in question_lower and "search" in tool.name.lower():
                    return Action(
                        action_type=ActionType.SEARCH,
                        name=tool.name,
                        description="Search for additional information",
                        parameters={"query": question}
                    )
        
        return None
