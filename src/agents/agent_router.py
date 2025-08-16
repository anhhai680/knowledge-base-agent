"""
AgentRouter - Routes queries to appropriate specialized agents with enhanced pattern detection

Enhanced to support routing between LangChain and LangGraph systems for zero-downtime migration.
"""

import re
import random
from typing import Dict, Any, List, Optional
from ..utils.logging import get_logger
from ..config.graph_config import GraphConfig, SystemSelector, DEFAULT_GRAPH_CONFIG

logger = get_logger(__name__)


class AgentRouter:
    """Routes queries to appropriate specialized agents with enhanced pattern detection"""
    
    def __init__(self, 
                 rag_agent, 
                 diagram_handler,
                 langgraph_rag_agent: Optional[Any] = None,
                 config: Optional[GraphConfig] = None):
        # Original agents (LangChain-based)
        self.rag_agent = rag_agent
        self.diagram_handler = diagram_handler
        
        # New LangGraph agents (parallel system)
        self.langgraph_rag_agent = langgraph_rag_agent
        self.config = config or DEFAULT_GRAPH_CONFIG
        
        # Pre-compile regex patterns for better performance
        self._diagram_patterns = self._compile_diagram_patterns()
        
        # Migration tracking
        self.routing_stats = {
            "langchain_requests": 0,
            "langgraph_requests": 0,
            "total_requests": 0,
            "system_selection_overrides": 0
        }
        
        logger.info(f"AgentRouter initialized with LangGraph support: {self.config.enable_langgraph}")
        if self.config.enable_langgraph:
            logger.info(f"Default system: {self.config.default_system.value}, "
                       f"Migration rollout: {self.config.migration_rollout_percentage * 100:.1f}%")
    
    def route_query(self, question: str, force_system: Optional[str] = None) -> Dict[str, Any]:
        """Route query to appropriate agent based on content analysis"""
        
        # Increment total request counter
        self.routing_stats["total_requests"] += 1
        
        # Check for repository information requests
        if self._is_repository_info_request(question):
            logger.info(f"Routing to repository information: {question[:100]}...")
            return self._generate_repository_info_response(question)
        
        # Detect diagram requests using enhanced pattern matching
        if self._is_diagram_request(question):
            logger.info(f"Routing to diagram generation: {question[:100]}...")
            return self._generate_diagram_response(question)
        
        # Route to RAG agent - with system selection
        logger.info(f"Routing to RAG agent: {question[:100]}...")
        return self._route_to_rag_agent(question, force_system)
    
    def _route_to_rag_agent(self, question: str, force_system: Optional[str] = None) -> Dict[str, Any]:
        """Route to appropriate RAG agent (LangChain vs LangGraph)"""
        
        # Determine which system to use
        selected_system = self._select_system(force_system)
        
        try:
            if selected_system == SystemSelector.LANGGRAPH:
                if self.langgraph_rag_agent is None:
                    logger.warning("LangGraph agent not available, falling back to LangChain")
                    selected_system = SystemSelector.LANGCHAIN
                else:
                    self.routing_stats["langgraph_requests"] += 1
                    logger.info(f"Using LangGraph RAG agent for query")
                    result = self.langgraph_rag_agent.query(question)
                    
                    # Add system identification to metadata
                    if "metadata" not in result:
                        result["metadata"] = {}
                    result["metadata"]["processing_system"] = "langgraph"
                    result["metadata"]["system_selection_reason"] = self._get_selection_reason(force_system)
                    
                    return result
            
            # Default to LangChain system
            self.routing_stats["langchain_requests"] += 1
            logger.info(f"Using LangChain RAG agent for query")
            result = self.rag_agent.query(question)
            
            # Add system identification to metadata
            if "metadata" not in result:
                result["metadata"] = {}
            result["metadata"]["processing_system"] = "langchain"
            result["metadata"]["system_selection_reason"] = self._get_selection_reason(force_system)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in RAG agent routing: {e}")
            
            # Fallback mechanism
            if selected_system == SystemSelector.LANGGRAPH:
                logger.info("LangGraph failed, falling back to LangChain")
                try:
                    self.routing_stats["langchain_requests"] += 1
                    result = self.rag_agent.query(question)
                    
                    if "metadata" not in result:
                        result["metadata"] = {}
                    result["metadata"]["processing_system"] = "langchain"
                    result["metadata"]["system_selection_reason"] = "langgraph_fallback"
                    result["metadata"]["fallback_error"] = str(e)
                    
                    return result
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
            
            # Final error response
            return {
                "answer": f"I apologize, but I encountered an error processing your request: {str(e)}",
                "source_documents": [],
                "metadata": {
                    "error": str(e),
                    "processing_system": "error",
                    "attempted_system": selected_system.value if isinstance(selected_system, SystemSelector) else str(selected_system)
                }
            }
    
    def _select_system(self, force_system: Optional[str] = None) -> SystemSelector:
        """Select which system to use for processing"""
        
        # Handle forced system selection
        if force_system:
            self.routing_stats["system_selection_overrides"] += 1
            if force_system.lower() == "langgraph":
                return SystemSelector.LANGGRAPH
            elif force_system.lower() == "langchain":
                return SystemSelector.LANGCHAIN
        
        # If LangGraph is not enabled, always use LangChain
        if not self.config.enable_langgraph:
            return SystemSelector.LANGCHAIN
        
        # Handle different selection strategies
        if self.config.default_system == SystemSelector.LANGGRAPH:
            return SystemSelector.LANGGRAPH
        elif self.config.default_system == SystemSelector.LANGCHAIN:
            return SystemSelector.LANGCHAIN
        elif self.config.default_system == SystemSelector.AUTO:
            # Auto selection based on rollout percentage
            if self.config.enable_ab_testing:
                # A/B testing - randomly route based on rollout percentage
                if random.random() < self.config.migration_rollout_percentage:
                    return SystemSelector.LANGGRAPH
                else:
                    return SystemSelector.LANGCHAIN
            else:
                # Gradual rollout - use percentage for migration
                if random.random() < self.config.migration_rollout_percentage:
                    return SystemSelector.LANGGRAPH
                else:
                    return SystemSelector.LANGCHAIN
        
        # Default fallback
        return SystemSelector.LANGCHAIN
    
    def _get_selection_reason(self, force_system: Optional[str] = None) -> str:
        """Get reason for system selection"""
        if force_system:
            return f"forced_{force_system.lower()}"
        elif not self.config.enable_langgraph:
            return "langgraph_disabled"
        elif self.config.default_system != SystemSelector.AUTO:
            return f"default_{self.config.default_system.value}"
        elif self.config.enable_ab_testing:
            return "ab_testing"
        else:
            return "gradual_rollout"
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        stats = self.routing_stats.copy()
        
        if stats["total_requests"] > 0:
            stats["langchain_percentage"] = (stats["langchain_requests"] / stats["total_requests"]) * 100
            stats["langgraph_percentage"] = (stats["langgraph_requests"] / stats["total_requests"]) * 100
        else:
            stats["langchain_percentage"] = 0.0
            stats["langgraph_percentage"] = 0.0
        
        stats["config"] = {
            "enable_langgraph": self.config.enable_langgraph,
            "default_system": self.config.default_system.value,
            "migration_rollout_percentage": self.config.migration_rollout_percentage,
            "enable_ab_testing": self.config.enable_ab_testing
        }
        
        return stats
    
    def reset_routing_stats(self):
        """Reset routing statistics"""
        self.routing_stats = {
            "langchain_requests": 0,
            "langgraph_requests": 0,
            "total_requests": 0,
            "system_selection_overrides": 0
        }
    
    def _compile_diagram_patterns(self) -> List[re.Pattern]:
        """Pre-compile regex patterns for diagram detection"""
        patterns = [
            # Direct diagram requests
            re.compile(r'\\b(?:sequence|flow|interaction)\\s+diagram\\b', re.IGNORECASE),
            re.compile(r'\\bgenerate\\s+(?:a\\s+)?(?:sequence|flow|mermaid)\\b', re.IGNORECASE),
            re.compile(r'\\bcreate\\s+(?:a\\s+)?(?:sequence|flow|diagram)\\b', re.IGNORECASE),
            re.compile(r'\\bshow\\s+(?:me\\s+)?(?:a\\s+)?(?:sequence|flow|diagram)\\b', re.IGNORECASE),
            
            # Visualization requests  
            re.compile(r'\\bvisuali[sz]e\\s+(?:how|the)\\b', re.IGNORECASE),
            re.compile(r'\\bmap\\s+out\\s+the\\b', re.IGNORECASE),
            re.compile(r'\\bdisplay\\s+the\\s+interaction\\b', re.IGNORECASE),
            
            # Flow analysis requests
            re.compile(r'\\bhow\\s+does\\s+.*\\s+flow\\s+work', re.IGNORECASE),
            re.compile(r'\\bwhat.*\\s+(?:call\\s+)?sequence\\b', re.IGNORECASE),
            re.compile(r'\\bwalk\\s+me\\s+through\\s+the.*flow\\b', re.IGNORECASE),
            
            # Mermaid-specific requests
            re.compile(r'\\bmermaid\\s+(?:code|diagram|syntax)\\b', re.IGNORECASE),
            re.compile(r'\b(?:sequence|flow|interaction)\s+diagram\b', re.IGNORECASE),
            re.compile(r'\bgenerate\s+(?:a\s+)?(?:sequence|flow|mermaid)\b', re.IGNORECASE),
            re.compile(r'\bcreate\s+(?:a\s+)?(?:sequence|flow|diagram)\b', re.IGNORECASE),
            re.compile(r'\bshow\s+(?:me\s+)?(?:a\s+)?(?:sequence|flow|diagram)\b', re.IGNORECASE),
            
            # Visualization requests  
            re.compile(r'\bvisuali[sz]e\s+(?:how|the)\b', re.IGNORECASE),
            re.compile(r'\bmap\s+out\s+the\b', re.IGNORECASE),
            re.compile(r'\bdisplay\s+the\s+interaction\b', re.IGNORECASE),
            
            # Flow analysis requests
            re.compile(r'\bhow\s+does\s+.*\s+flow\s+work', re.IGNORECASE),
            re.compile(r'\bwhat.*\s+(?:call\s+)?sequence\b', re.IGNORECASE),
            re.compile(r'\bwalk\s+me\s+through\s+the.*flow\b', re.IGNORECASE),
            
            # Mermaid-specific requests
            re.compile(r'\bmermaid\s+(?:code|diagram|syntax)\b', re.IGNORECASE),
            re.compile(r'\bgenerate\s+mermaid\b', re.IGNORECASE),
        ]
        return patterns
    
    def _is_diagram_request(self, question: str) -> bool:
        """Enhanced diagram request detection using multiple strategies"""
        
        # Strategy 1: Pre-compiled regex patterns
        for pattern in self._diagram_patterns:
            if pattern.search(question):
                return True
        
        # Strategy 2: Keyword combination analysis
        question_lower = question.lower()
        
        # Direct keywords
        direct_keywords = [
            'sequence diagram', 'flow diagram', 'interaction diagram',
            'mermaid', 'visualize', 'diagram', 'sequence', 'flow'
        ]
        
        # Context keywords that strengthen diagram intent
        context_keywords = [
            'show', 'generate', 'create', 'display', 'map out',
            'walk through', 'interaction', 'call', 'process'
        ]
        
        # Flow-related phrases
        flow_phrases = [
            'how does', 'what happens when', 'walk me through',
            'show me how', 'explain the flow', 'interaction between'
        ]
        
        # Check for direct keywords
        has_direct_keyword = any(keyword in question_lower for keyword in direct_keywords)
        
        # Check for flow phrases
        has_flow_phrase = any(phrase in question_lower for phrase in flow_phrases)
        
        # Check for context + visualization intent
        has_context = any(keyword in question_lower for keyword in context_keywords)
        has_visualization_intent = any(word in question_lower for word in [
            'interaction', 'sequence', 'flow', 'process', 'steps'
        ])
        
        # Decision logic
        if has_direct_keyword:
            return True
        if has_flow_phrase and has_visualization_intent:
            return True
        if has_context and has_visualization_intent and 'flow' in question_lower:
            return True

        logger.debug(f"Request detected in: {question} with context: {has_context}, flow: {has_flow_phrase}, visualization: {has_visualization_intent}")

        return False
    
    def _is_repository_info_request(self, question: str) -> bool:
        """Detect requests for repository information"""
        question_lower = question.lower()
        
        info_patterns = [
            'list repositories', 'available repositories', 'what repositories',
            'which repositories', 'show repositories', 'indexed repositories',
            'repository analysis', 'analyze repository', 'repository content',
            'what repos', 'list repos', 'available repos'
        ]
        
        return any(pattern in question_lower for pattern in info_patterns)
    
    def _generate_repository_info_response(self, query: str) -> Dict[str, Any]:
        """Generate repository information response"""
        try:
            available_repos = self.diagram_handler._get_available_repositories()
            
            if not available_repos:
                return {
                    "answer": "No repositories are currently indexed in the knowledge base. Please index some repositories first using the /index endpoint.",
                    "source_documents": [],
                    "status": "success",
                    "num_sources": 0,
                    "error": None,
                    "mermaid_code": None,
                    "diagram_type": None
                }
            
            # Analyze each repository for diagram suitability
            repo_analysis = {}
            for repo in available_repos:
                analysis = self.diagram_handler.get_repository_analysis(repo)
                repo_analysis[repo] = analysis
            
            # Format response
            response_lines = [f"Found {len(available_repos)} indexed repositories:\n"]
            
            suitable_repos = []
            unsuitable_repos = []
            
            for repo, analysis in repo_analysis.items():
                repo_name = repo.split('/')[-1] if '/' in repo else repo
                total_files = analysis.get('total_files', 0)
                suitable = analysis.get('suitable_for_diagrams', False)
                
                if suitable:
                    suitable_repos.append(f"✅ **{repo_name}** ({total_files} files) - Suitable for sequence diagrams")
                else:
                    unsuitable_repos.append(f"⚠️ **{repo_name}** ({total_files} files) - Limited diagram potential")
            
            if suitable_repos:
                response_lines.append("## Repositories suitable for sequence diagrams:")
                response_lines.extend(suitable_repos)
                response_lines.append("")
            
            if unsuitable_repos:
                response_lines.append("## Repositories with limited sequence diagram potential:")
                response_lines.extend(unsuitable_repos)
                response_lines.append("")
            
            response_lines.append("💡 **Tip**: For best sequence diagrams, ask about repositories that contain business logic, services, or API endpoints.")
            
            return {
                "answer": "\n".join(response_lines),
                "source_documents": [],
                "status": "success",
                "num_sources": len(available_repos),
                "error": None,
                "mermaid_code": None,
                "diagram_type": None
            }
            
        except Exception as e:
            logger.error(f"Repository info generation failed: {str(e)}")
            return {
                "answer": "I encountered an error while retrieving repository information. Please try again.",
                "source_documents": [],
                "status": "error",
                "num_sources": 0,
                "error": str(e),
                "mermaid_code": None,
                "diagram_type": None
            }
    
    def _generate_diagram_response(self, query: str) -> Dict[str, Any]:
        """Generate diagram and format as standard query response"""
        try:
            # Generate diagram using DiagramHandler
            diagram_result = self.diagram_handler.generate_sequence_diagram(query)
            
            # Format as standard QueryResponse with mermaid_code extension
            return {
                "answer": diagram_result.get("analysis_summary", "Generated sequence diagram"),
                "source_documents": diagram_result.get("source_documents", []),
                "status": diagram_result.get("status", "success"),
                "num_sources": len(diagram_result.get("source_documents", [])),
                "mermaid_code": diagram_result.get("mermaid_code"),  # Extended field
                "diagram_type": "sequence"  # Extended field
            }
            
        except Exception as e:
            logger.error(f"Diagram generation failed: {str(e)}")
            return {
                "answer": "I encountered an error while generating the diagram. Please try again or ask about available flows in the codebase.",
                "source_documents": [],
                "status": "error",
                "num_sources": 0,
                "error": str(e),
                "mermaid_code": None,
                "diagram_type": None
            }