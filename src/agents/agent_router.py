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
            re.compile(r'\\bgenerate\\s+mermaid\\b', re.IGNORECASE),
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