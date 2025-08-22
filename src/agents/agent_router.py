"""
AgentRouter - Routes queries to appropriate specialized agents with enhanced pattern detection
"""

import re
from typing import Dict, Any, List, Optional
from ..utils.logging import get_logger
from ..config.agent_config import AgentConfig, DiagramAgentType, DEFAULT_AGENT_CONFIG
from .response_models import (
    AgentResponse, ResponseStatus, ResponseType, 
    adapt_agent_response, create_error_response, create_success_response
)

logger = get_logger(__name__)


class AgentRouter:
    """Routes queries to appropriate specialized agents with enhanced pattern detection"""
    
    def __init__(self, rag_agent, diagram_handler, diagram_agent=None, agent_config=None):
        """
        Initialize AgentRouter with dual diagram agent support
        
        Args:
            rag_agent: RAG agent for general queries
            diagram_handler: Legacy DiagramHandler for backward compatibility
            diagram_agent: Optional enhanced DiagramAgent for advanced capabilities
            agent_config: Optional agent configuration for routing behavior
        """
        self.rag_agent = rag_agent
        self.diagram_handler = diagram_handler
        self.diagram_agent = diagram_agent
        self.agent_config = agent_config or DEFAULT_AGENT_CONFIG
        
        # Pre-compile regex patterns for better performance
        self._diagram_patterns = self._compile_diagram_patterns()
        
        # Log agent configuration
        logger.info(f"AgentRouter initialized with diagram agents: "
                   f"handler={'Yes'}, agent={'Yes' if diagram_agent else 'No'}, "
                   f"preferred={self.agent_config.routing.preferred_diagram_agent}")
        
        # Validate configuration
        if (self.agent_config.routing.preferred_diagram_agent == DiagramAgentType.DIAGRAM_AGENT 
            and not self.diagram_agent):
            logger.warning("DiagramAgent preferred but not provided, falling back to DiagramHandler")
            self.agent_config.routing.preferred_diagram_agent = DiagramAgentType.DIAGRAM_HANDLER
    
    def route_query(self, question: str) -> AgentResponse:
        """Route query to appropriate agent based on content analysis"""
        
        try:
            # Check for repository information requests
            if self._is_repository_info_request(question):
                logger.info(f"Routing to repository information: {question[:100]}...")
                return self._generate_repository_info_response(question)
            
            # Detect diagram requests using enhanced pattern matching
            if self._is_diagram_request(question):
                logger.info(f"Routing to diagram generation: {question[:100]}...")
                return self._generate_diagram_response(question)
            
            # Default to RAG agent for regular queries
            logger.info(f"Routing to RAG agent: {question[:100]}...")
            raw_response = self.rag_agent.process_query(question)
            return adapt_agent_response(raw_response, "rag")
            
        except Exception as e:
            logger.error(f"Query routing failed: {str(e)}")
            return create_error_response(
                f"Failed to route query: {str(e)}", 
                "routing_error", 
                "AgentRouter"
            )
    
    def _compile_diagram_patterns(self) -> List[re.Pattern]:
        """Pre-compile regex patterns for diagram detection with improved mermaid support"""
        patterns = [
            # Direct diagram requests
            re.compile(r'\b(?:sequence|flow|interaction)\s+diagram\b', re.IGNORECASE),
            re.compile(r'\bgenerate\s+(?:a\s+)?(?:sequence|flow|mermaid|diagram)\b', re.IGNORECASE),
            re.compile(r'\bcreate\s+(?:a\s+)?(?:sequence|flow|diagram|mermaid)\b', re.IGNORECASE),
            re.compile(r'\bshow\s+(?:me\s+)?(?:a\s+)?(?:sequence|flow|diagram)\b', re.IGNORECASE),
            
            # Enhanced mermaid-specific requests
            re.compile(r'\bmermaid\s+(?:code|diagram|syntax|sequence|flow)\b', re.IGNORECASE),
            re.compile(r'\b(?:sequence|flow)\s+in\s+mermaid\b', re.IGNORECASE),
            re.compile(r'\bdraw\s+(?:a\s+)?(?:sequence|flow)\s+(?:with\s+)?mermaid\b', re.IGNORECASE),
            
            # Visualization requests  
            re.compile(r'\bvisuali[sz]e\s+(?:how|the|as)\b', re.IGNORECASE),
            re.compile(r'\bmap\s+out\s+the\b', re.IGNORECASE),
            re.compile(r'\bdisplay\s+the\s+interaction\b', re.IGNORECASE),
            
            # Flow analysis requests
            re.compile(r'\bhow\s+does\s+.*\s+flow\s+work', re.IGNORECASE),
            re.compile(r'\bwhat.*\s+(?:call\s+)?sequence\b', re.IGNORECASE),
            re.compile(r'\bwalk\s+me\s+through\s+the.*flow\b', re.IGNORECASE),
            
            # Code structure visualization
            re.compile(r'\b(?:class|method|function)\s+interaction\b', re.IGNORECASE),
            re.compile(r'\b(?:service|api|endpoint)\s+flow\b', re.IGNORECASE),
            re.compile(r'\b(?:data|request)\s+flow\b', re.IGNORECASE),
        ]
        return patterns
    
    def _is_diagram_request(self, question: str) -> bool:
        """Enhanced diagram request detection with improved mermaid support"""
        
        # Strategy 1: Pre-compiled regex patterns
        for pattern in self._diagram_patterns:
            if pattern.search(question):
                return True
        
        # Strategy 2: Enhanced keyword combination analysis
        question_lower = question.lower()
        
        # Direct keywords with mermaid emphasis
        direct_keywords = [
            'sequence diagram', 'flow diagram', 'interaction diagram',
            'mermaid', 'visualize', 'diagram', 'sequence', 'flow'
        ]
        
        # Mermaid-specific indicators
        mermaid_indicators = [
            'mermaid code', 'mermaid syntax', 'mermaid diagram',
            'sequence in mermaid', 'flow in mermaid'
        ]
        
        # Context keywords that strengthen diagram intent
        context_keywords = [
            'show', 'generate', 'create', 'display', 'map out',
            'walk through', 'interaction', 'call', 'process', 'draw'
        ]
        
        # Flow-related phrases
        flow_phrases = [
            'how does', 'what happens when', 'walk me through',
            'show me how', 'explain the flow', 'interaction between',
            'step by step', 'workflow', 'process flow'
        ]
        
        # Check for direct keywords
        has_direct_keyword = any(keyword in question_lower for keyword in direct_keywords)
        
        # Check for mermaid-specific requests
        has_mermaid_request = any(indicator in question_lower for indicator in mermaid_indicators)
        
        # Check for flow phrases
        has_flow_phrase = any(phrase in question_lower for phrase in flow_phrases)
        
        # Check for context + visualization intent
        has_context = any(keyword in question_lower for keyword in context_keywords)
        has_visualization_intent = any(word in question_lower for word in [
            'interaction', 'sequence', 'flow', 'process', 'steps', 'workflow'
        ])
        
        # Decision logic with mermaid priority
        if has_mermaid_request:
            return True
        if has_direct_keyword:
            return True
        if has_flow_phrase and has_visualization_intent:
            return True
        if has_context and has_visualization_intent and ('flow' in question_lower or 'sequence' in question_lower):
            return True

        logger.debug(f"Request analysis: {question} | mermaid: {has_mermaid_request}, direct: {has_direct_keyword}, flow: {has_flow_phrase}, context: {has_context}, visualization: {has_visualization_intent}")

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
    
    def _generate_repository_info_response(self, query: str) -> AgentResponse:
        """Generate repository information response"""
        try:
            available_repos = self.diagram_handler._get_available_repositories()
            
            if not available_repos:
                return create_success_response(
                    "No repositories are currently indexed in the knowledge base. Please index some repositories first using the /index endpoint.",
                    ResponseType.TEXT
                )
            
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
            
            return create_success_response(
                "\n".join(response_lines),
                ResponseType.ANALYSIS,
                num_sources=len(available_repos),
                metadata={"repositories_analyzed": len(available_repos)}
            )
            
        except Exception as e:
            logger.error(f"Repository info generation failed: {str(e)}")
            return create_error_response(
                f"Repository info generation failed: {str(e)}",
                "repo_info_error",
                "AgentRouter"
            )
    
    def _generate_diagram_response(self, query: str) -> AgentResponse:
        """Generate diagram with enhanced mermaid support and intelligent agent selection"""
        try:
            # Select appropriate diagram agent
            selected_agent = self._select_diagram_agent(query)
            agent_name = "DiagramAgent" if selected_agent == self.diagram_agent else "DiagramHandler"
            
            logger.info(f"Selected {agent_name} for diagram generation")
            
            # Check if this is a mermaid-specific request
            is_mermaid_request = self._is_mermaid_specific_request(query)
            
            # Generate diagram using selected agent
            diagram_result = self._generate_with_agent(selected_agent, query)
            
            # Use adapter to standardize the response
            standardized_response = adapt_agent_response(diagram_result, "diagram")
            
            # Enhance response for mermaid requests
            if is_mermaid_request and standardized_response.mermaid_code:
                enhanced_answer = self._enhance_mermaid_response(diagram_result, query)
                standardized_response.answer = enhanced_answer
            
            return standardized_response
            
        except Exception as e:
            logger.error(f"Diagram generation failed: {str(e)}")
            
            # Attempt fallback if enabled and primary agent failed
            if self.agent_config.routing.enable_agent_fallback:
                try:
                    fallback_result = self._attempt_fallback_diagram_generation(query, str(e))
                    return adapt_agent_response(fallback_result, "diagram")
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {str(fallback_error)}")
            
            return create_error_response(
                f"Diagram generation failed: {str(e)}. Please try again or ask about available flows in the codebase.",
                "diagram_generation_error",
                "AgentRouter"
            )

    def _is_mermaid_specific_request(self, query: str) -> bool:
        """Detect if the request specifically asks for mermaid format"""
        mermaid_patterns = [
            r'\bmermaid\b',
            r'\b(?:sequence|flow)\s+in\s+mermaid\b',
            r'\b(?:generate|create|show)\s+.*\s+mermaid\b'
        ]
        
        query_lower = query.lower()
        return any(re.search(pattern, query_lower, re.IGNORECASE) for pattern in mermaid_patterns)

    def _enhance_mermaid_response(self, diagram_result: Dict[str, Any], query: str) -> str:
        """Enhance response for mermaid-specific requests"""
        mermaid_code = diagram_result.get("mermaid_code", "")
        analysis_summary = diagram_result.get("analysis_summary", "")
        
        if not mermaid_code:
            return analysis_summary
        
        enhanced_response = f"""## Mermaid Sequence Diagram Generated

{analysis_summary}

### Mermaid Code
```mermaid
{mermaid_code}
```

### Usage Instructions
1. **Copy the mermaid code** above
2. **Paste into any mermaid-compatible editor** (GitHub, GitLab, Mermaid Live Editor)
3. **Customize** the diagram as needed
4. **Export** to PNG, SVG, or other formats

💡 **Tip**: You can also use this in documentation, README files, or technical specifications."""
        
        return enhanced_response
    
    def _select_diagram_agent(self, query: str):
        """
        Select appropriate diagram agent based on configuration and query complexity
        
        Returns:
            Selected agent instance (DiagramAgent or DiagramHandler)
        """
        # If DiagramAgent not available, use DiagramHandler
        if not self.diagram_agent:
            logger.debug("DiagramAgent not available, using DiagramHandler")
            return self.diagram_handler
        
        preference = self.agent_config.routing.preferred_diagram_agent
        
        # Handle explicit preferences
        if preference == DiagramAgentType.DIAGRAM_HANDLER:
            logger.debug("Using DiagramHandler per configuration")
            return self.diagram_handler
        elif preference == DiagramAgentType.DIAGRAM_AGENT:
            logger.debug("Using DiagramAgent per configuration")
            return self.diagram_agent
        
        # Handle auto-selection
        if preference == DiagramAgentType.AUTO and self.agent_config.routing.auto_selection_enabled:
            if self._is_complex_diagram_request(query):
                logger.debug("Complex query detected, using DiagramAgent")
                return self.diagram_agent
            else:
                logger.debug("Simple query detected, using DiagramHandler")
                return self.diagram_handler
        
        # Default fallback
        logger.debug("Using default DiagramHandler")
        return self.diagram_handler
    
    def _is_complex_diagram_request(self, query: str) -> bool:
        """
        Determine if query requires enhanced DiagramAgent capabilities
        
        Args:
            query: User query
            
        Returns:
            True if query is complex and should use DiagramAgent
        """
        query_lower = query.lower()
        
        # Check for complex diagram keywords
        complex_keywords = self.agent_config.routing.complex_query_keywords
        has_complex_keywords = any(keyword in query_lower for keyword in complex_keywords)
        
        # Check for multi-diagram type indicators
        diagram_type_count = 0
        for keywords in [
            ['sequence', 'interaction'],
            ['flowchart', 'flow', 'workflow'], 
            ['class', 'inheritance', 'composition'],
            ['component', 'architecture', 'system'],
            ['entity', 'relationship', 'database']
        ]:
            if any(keyword in query_lower for keyword in keywords):
                diagram_type_count += 1
        
        # Check for enhanced analysis keywords
        enhanced_keywords = [
            'analyze', 'pattern', 'relationship', 'dependency',
            'architecture', 'design', 'structure', 'optimization'
        ]
        has_enhanced_keywords = any(keyword in query_lower for keyword in enhanced_keywords)
        
        # Complex if: multiple diagram types, complex keywords, or enhanced analysis
        is_complex = (
            diagram_type_count > 1 or 
            has_complex_keywords or 
            has_enhanced_keywords
        )
        
        logger.debug(f"Query complexity analysis: types={diagram_type_count}, "
                    f"complex_kw={has_complex_keywords}, enhanced_kw={has_enhanced_keywords}, "
                    f"complex={is_complex}")
        
        return is_complex
    
    def _generate_with_agent(self, agent, query: str) -> Dict[str, Any]:
        """
        Generate diagram using the specified agent with unified interface
        
        Args:
            agent: Agent instance (DiagramHandler or DiagramAgent)
            query: User query
            
        Returns:
            Diagram generation result
        """
        # Use DiagramAgent's enhanced interface
        if hasattr(agent, 'process_query'):
            logger.debug("Using DiagramAgent.process_query()")
            return agent.process_query(query)
        
        # Use DiagramHandler's legacy interface  
        elif hasattr(agent, 'generate_sequence_diagram'):
            logger.debug("Using DiagramHandler.generate_sequence_diagram()")
            return agent.generate_sequence_diagram(query)
        
        else:
            raise ValueError(f"Agent {type(agent).__name__} has no supported interface")
    
    def _attempt_fallback_diagram_generation(self, query: str, original_error: str) -> AgentResponse:
        """
        Attempt fallback diagram generation with alternative agent
        
        Args:
            query: Original query
            original_error: Error from primary agent
            
        Returns:
            Fallback diagram result or error response
        """
        logger.info("Attempting fallback diagram generation")
        
        # Determine fallback agent
        if self.diagram_agent and self.diagram_handler:
            # Try the other agent
            primary_was_advanced = hasattr(self._select_diagram_agent(query), 'process_query')
            fallback_agent = self.diagram_handler if primary_was_advanced else self.diagram_agent
            fallback_name = "DiagramHandler" if primary_was_advanced else "DiagramAgent"
        else:
            # Only one agent available, can't fallback
            raise Exception(f"Fallback not possible: {original_error}")
        
        logger.info(f"Falling back to {fallback_name}")
        
        try:
            result = self._generate_with_agent(fallback_agent, query)
            
            # Use adapter to standardize the response
            standardized_response = adapt_agent_response(result, "diagram")
            
            # Add fallback notice to answer
            if standardized_response.answer:
                standardized_response.answer = f"⚠️ **Fallback Response**: Generated using {fallback_name} due to primary agent error.\n\n{standardized_response.answer}"
            
            # Mark as fallback in metadata
            standardized_response.metadata["fallback_used"] = True
            standardized_response.metadata["original_error"] = original_error
            standardized_response.metadata["fallback_agent"] = fallback_name
            
            return standardized_response
            
        except Exception as e:
            raise Exception(f"Both agents failed - Primary: {original_error}, Fallback: {str(e)}")