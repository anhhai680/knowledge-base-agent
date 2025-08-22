"""
AgentRouter - Routes queries to appropriate specialized agents with enhanced pattern detection
"""

import re
from typing import Dict, Any, List, Optional
from ..utils.logging import get_logger
from ..config.agent_config import AgentConfig, DEFAULT_AGENT_CONFIG
from .response_models import (
    AgentResponse, ResponseStatus, ResponseType, 
    adapt_agent_response, create_error_response, create_success_response
)

logger = get_logger(__name__)


class AgentRouter:
    """Routes queries to appropriate specialized agents with enhanced pattern detection"""
    
    def __init__(self, rag_agent, diagram_agent, config=None):
        """
        Initialize AgentRouter with enhanced RAG integration
        
        Args:
            rag_agent: RAG agent for general queries
            diagram_agent: DiagramAgent for advanced diagram capabilities
            config: Optional agent configuration for routing behavior
        """
        self.rag_agent = rag_agent
        self.diagram_agent = diagram_agent
        
        # Create a validated copy of the configuration to prevent direct modification
        self.agent_config = (config or DEFAULT_AGENT_CONFIG).copy()
        
        # Pre-compile regex patterns for better performance
        self._diagram_patterns = self._compile_diagram_patterns()
        
        # Add caching for frequent patterns
        self._route_cache = {}
        
        # Log agent configuration
        logger.info(f"AgentRouter initialized with DiagramAgent: "
                   f"{'Yes' if diagram_agent else 'No'}")
        
        if not diagram_agent:
            logger.warning("DiagramAgent not available - diagram functionality will be limited")
    
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
        """Generate repository information response using available vectorstore data"""
        try:
            # Get repository information from the RAG agent's vectorstore
            if hasattr(self.rag_agent, 'vectorstore') and self.rag_agent.vectorstore:
                try:
                    # Get all documents to analyze repositories
                    sample_docs = self.rag_agent.vectorstore.similarity_search("", k=50)
                    
                    # Extract repository information from documents
                    repositories = set()
                    repo_file_counts = {}
                    
                    for doc in sample_docs:
                        metadata = doc.metadata
                        repo = metadata.get('repository', 'unknown')
                        if repo != 'unknown':
                            repositories.add(repo)
                            repo_file_counts[repo] = repo_file_counts.get(repo, 0) + 1
                    
                    available_repos = list(repositories)
                    
                except Exception as e:
                    logger.warning(f"Failed to query vectorstore for repositories: {str(e)}")
                    available_repos = []
            else:
                available_repos = []
            
            if not available_repos:
                return create_success_response(
                    "No repositories are currently indexed in the knowledge base. Please index some repositories first using the /index endpoint.",
                    ResponseType.TEXT
                )
            
            # Format response with basic repository information
            response_lines = [f"Found {len(available_repos)} indexed repositories:\n"]
            
            for repo in sorted(available_repos):
                repo_name = repo.split('/')[-1] if '/' in repo else repo
                file_count = repo_file_counts.get(repo, 0)
                response_lines.append(f"📁 **{repo_name}** ({file_count} indexed chunks)")
            
            response_lines.append("")
            response_lines.append("💡 **Tip**: You can ask questions about any of these repositories or request diagrams showing their architecture and interactions.")
            
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
        """Generate diagram using DiagramAgent with enhanced mermaid support"""
        try:
            # Check if DiagramAgent is available
            if not self.diagram_agent:
                return create_error_response(
                    "Diagram generation not available. DiagramAgent is not initialized.",
                    "diagram_agent_unavailable",
                    "AgentRouter"
                )
            
            logger.info("Using DiagramAgent for diagram generation")
            
            # Check if this is a mermaid-specific request
            is_mermaid_request = self._is_mermaid_specific_request(query)
            
            # Generate diagram using DiagramAgent
            diagram_result = self._generate_with_agent(self.diagram_agent, query)
            
            # Use adapter to standardize the response
            standardized_response = adapt_agent_response(diagram_result, "diagram")
            
            # Enhance response for mermaid requests
            if is_mermaid_request and standardized_response.mermaid_code:
                enhanced_answer = self._enhance_mermaid_response(diagram_result, query)
                standardized_response.answer = enhanced_answer
            
            return standardized_response
            
        except Exception as e:
            logger.error(f"Diagram generation failed: {str(e)}")
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
    
    def _generate_with_agent(self, agent, query: str) -> Dict[str, Any]:
        """
        Generate diagram using DiagramAgent
        
        Args:
            agent: DiagramAgent instance
            query: User query
            
        Returns:
            Diagram generation result
        """
        if hasattr(agent, 'process_query'):
            logger.debug("Using DiagramAgent.process_query()")
            return agent.process_query(query)
        else:
            raise ValueError(f"Agent {type(agent).__name__} does not support process_query method")
    
    def update_configuration(self, new_config: AgentConfig) -> None:
        """
        Safely update the router configuration
        
        Args:
            new_config: New configuration to apply
        """
        # Create a copy of the new configuration
        self.agent_config = new_config.copy()
        
        # Log the configuration update
        logger.info("Configuration updated")
        
        # Re-compile patterns if needed
        self._diagram_patterns = self._compile_diagram_patterns()
    
    def get_current_configuration(self) -> AgentConfig:
        """
        Get a copy of the current configuration
        
        Returns:
            Copy of the current configuration to prevent external modification
        """
        return self.agent_config.copy()