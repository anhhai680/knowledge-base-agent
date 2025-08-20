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
        return self.rag_agent.process_query(question)
    
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
        """Generate diagram with enhanced mermaid support and response quality"""
        try:
            # Check if this is a mermaid-specific request
            is_mermaid_request = self._is_mermaid_specific_request(query)
            
            # Generate diagram using DiagramHandler
            diagram_result = self.diagram_handler.generate_sequence_diagram(query)
            
            # Enhance response for mermaid requests
            if is_mermaid_request and diagram_result.get("mermaid_code"):
                enhanced_answer = self._enhance_mermaid_response(diagram_result, query)
            else:
                enhanced_answer = diagram_result.get("analysis_summary", "Generated sequence diagram")
            
            # Format as standard QueryResponse with mermaid_code extension
            return {
                "answer": enhanced_answer,
                "source_documents": diagram_result.get("source_documents", []),
                "status": diagram_result.get("status", "success"),
                "num_sources": len(diagram_result.get("source_documents", [])),
                "mermaid_code": diagram_result.get("mermaid_code"),
                "diagram_type": "sequence"
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