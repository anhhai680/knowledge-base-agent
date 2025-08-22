"""
AgentRouter - Routes queries to appropriate specialized agents with enhanced pattern detection
"""

from ..utils.logging import get_logger
from ..config.agent_config import AgentConfig, DEFAULT_AGENT_CONFIG
from .response_models import (
    AgentResponse, ResponseType, 
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
        
        # Simple diagram keywords for routing (not processing)
        self._diagram_keywords = [
            'diagram', 'mermaid', 'sequence', 'flow', 'flowchart', 'visualize', 
            'chart', 'visualization', 'interaction', 'architecture'
        ]
        
        # Repository info keywords
        self._repo_info_keywords = [
            'list repositories', 'available repositories', 'what repositories',
            'which repositories', 'show repositories', 'indexed repositories'
        ]
        
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
            
            # Detect diagram requests using simple keyword matching
            if self._is_diagram_request(question):
                logger.info(f"Routing to diagram generation: {question[:100]}...")
                return self._delegate_to_diagram_agent(question)
            
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
    
    def _is_diagram_request(self, question: str) -> bool:
        """Simple diagram request detection using keyword matching and DiagramAgent capability check"""
        # First check simple keywords for fast routing
        question_lower = question.lower()
        if any(keyword in question_lower for keyword in self._diagram_keywords):
            return True
        
        # If DiagramAgent is available, use its enhanced detection
        if self.diagram_agent and hasattr(self.diagram_agent, 'can_handle_request'):
            return self.diagram_agent.can_handle_request(question)
        
        return False
    
    def _is_repository_info_request(self, question: str) -> bool:
        """Detect requests for repository information"""
        question_lower = question.lower()
        return any(pattern in question_lower for pattern in self._repo_info_keywords)
    
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
                    repo_file_counts = {}
            else:
                available_repos = []
                repo_file_counts = {}
            
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
    
    def _delegate_to_diagram_agent(self, query: str) -> AgentResponse:
        """Delegate diagram generation to DiagramAgent with simple response adaptation"""
        try:
            # Check if DiagramAgent is available
            if not self.diagram_agent:
                return create_error_response(
                    "Diagram generation not available. DiagramAgent is not initialized.",
                    "diagram_agent_unavailable",
                    "AgentRouter"
                )
            
            logger.info("Delegating to DiagramAgent for diagram generation")
            
            # Delegate to DiagramAgent - let it handle all the complex logic
            diagram_result = self.diagram_agent.process_query(query)
            
            # Use adapter to standardize the response
            return adapt_agent_response(diagram_result, "diagram")
            
        except Exception as e:
            logger.error(f"Diagram generation failed: {str(e)}")
            return create_error_response(
                f"Diagram generation failed: {str(e)}. Please try again or ask about available flows in the codebase.",
                "diagram_generation_error",
                "AgentRouter"
            )

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
    
    def get_current_configuration(self) -> AgentConfig:
        """
        Get a copy of the current configuration
        
        Returns:
            Copy of the current configuration to prevent external modification
        """
        return self.agent_config.copy()