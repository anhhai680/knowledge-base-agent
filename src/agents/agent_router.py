"""
AgentRouter - Routes queries to appropriate specialized agents with enhanced pattern detection
"""

import re
from typing import Dict, Any, List
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AgentRouter:
    """Routes queries to appropriate specialized agents with enhanced pattern detection"""
    
    def __init__(self, rag_agent, diagram_handler):
        self.rag_agent = rag_agent
        self.diagram_handler = diagram_handler
        # Pre-compile regex patterns for better performance
        self._diagram_patterns = self._compile_diagram_patterns()
    
    def route_query(self, question: str) -> Dict[str, Any]:
        """Route query to appropriate agent based on content analysis"""
        
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
        return self.rag_agent.query(question)
    
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