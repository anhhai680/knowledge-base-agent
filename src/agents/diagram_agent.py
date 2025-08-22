"""
DiagramAgent - Specialized agent for diagram generation with enhanced capabilities

This agent provides specialized diagram generation capabilities including:
- Multiple diagram types (sequence, flowchart, class, ER, component)
- Enhanced code retrieval with semantic analysis
- Integration with query optimizer and response enhancer
- Repository-specific filtering and code pattern detection
"""

from typing import Dict, Any, List
from langchain.docstore.document import Document
from ..processors.sequence_detector import SequenceDetector
from ..utils.logging import get_logger
from ..utils.code_pattern_detector import CodePatternDetector, QueryOptimizer, RepositoryFilter
from ..utils.diagram_generators import DiagramPatternExtractor, MermaidGenerator
from ..retrieval import EnhancedCodeRetriever

logger = get_logger(__name__)


class DiagramAgent:
    """Specialized agent for diagram generation with enhanced capabilities"""
    
    def __init__(self, vectorstore, llm, query_optimizer=None, response_enhancer=None):
        """
        Initialize DiagramAgent with required dependencies
        
        Args:
            vectorstore: Vector store for code retrieval
            llm: Language model for diagram generation
            query_optimizer: Optional query optimization component
            response_enhancer: Optional response quality enhancement component
        """
        self.vectorstore = vectorstore
        self.llm = llm
        self.query_optimizer = query_optimizer
        self.response_enhancer = response_enhancer
        self.sequence_detector = SequenceDetector()
        
        # Initialize enhanced code analysis components
        self.pattern_detector = CodePatternDetector()
        self.diagram_query_optimizer = QueryOptimizer()
        self.repository_filter = RepositoryFilter()
        
        # Initialize enhanced code retriever
        self.code_retriever = EnhancedCodeRetriever(
            vectorstore=vectorstore,
            repository_filter=self.repository_filter,
            diagram_query_optimizer=self.diagram_query_optimizer,
            diagram_type_keywords=self.diagram_type_keywords
        )
        
        # Initialize diagram pattern extraction and generation utilities
        self.pattern_extractor = DiagramPatternExtractor()
        self.mermaid_generator = MermaidGenerator()
        
        # Initialize diagram generators for different types
        self.diagram_generators = {
            'sequence': self._generate_sequence_diagram,
            'flowchart': self._generate_flowchart,
            'class': self._generate_class_diagram,
            'er': self._generate_er_diagram,
            'component': self._generate_component_diagram,
            'architecture': self._generate_architecture_diagram
        }
        
        # Supported diagram types and their detection keywords (order matters - more specific first)
        self.diagram_type_keywords = {
            'architecture': ['architecture', 'architecture diagram', 'system architecture', 'system design', 'architectural', 'service architecture'],
            'flowchart': ['flowchart', 'flow chart', 'process flow', 'workflow', 'decision tree', 'control flow'],
            'sequence': ['sequence', 'interaction', 'method call', 'interaction diagram', 'sequence diagram'],
            'class': ['class diagram', 'class structure', 'object model', 'inheritance', 'composition', 'uml class'],
            'er': ['entity relationship', 'er diagram', 'database schema', 'data model', 'entity model'],
            'component': ['component diagram', 'module diagram', 'service diagram']
        }
    
    def can_handle_request(self, query: str) -> bool:
        """
        Enhanced method to determine if this agent can handle the request.
        Used by AgentRouter for better routing decisions.
        
        Args:
            query: User query to analyze
            
        Returns:
            Boolean indicating if this agent can handle the request
        """
        query_lower = query.lower()
        
        # Check for any diagram-related keywords
        diagram_keywords = ['diagram', 'mermaid', 'sequence', 'flow', 'flowchart', 'visualize', 
                           'chart', 'visualization', 'interaction', 'architecture']
        
        if any(keyword in query_lower for keyword in diagram_keywords):
            return True
        
        # Check for more specific diagram type keywords
        for diagram_type, keywords in self.diagram_type_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return True
        
        # Check for visualization intent phrases
        visualization_phrases = ['show me how', 'walk me through', 'explain the flow',
                               'map out', 'display the interaction', 'draw', 'generate']
        
        if any(phrase in query_lower for phrase in visualization_phrases):
            # Check if combined with flow/sequence/interaction terms
            flow_terms = ['flow', 'sequence', 'interaction', 'process', 'steps']
            if any(term in query_lower for term in flow_terms):
                return True
        
        return False
    
    def _detect_language_from_path(self, file_path: str) -> str:
        """Detect programming language from file path"""
        if not file_path:
            return 'unknown'
        fp = file_path.lower()
        if fp.endswith('.py'):
            return 'python'
        if fp.endswith(('.js', '.jsx')):
            return 'javascript'
        if fp.endswith(('.ts', '.tsx')):
            return 'typescript'
        if fp.endswith('.cs'):
            return 'csharp'
        if fp.endswith('.md'):
            return 'markdown'
        return 'unknown'
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Process diagram request with enhanced capabilities
        
        Args:
            query: User query requesting diagram generation
            
        Returns:
            Dictionary containing diagram result and metadata
        """
        try:
            logger.info(f"Processing diagram query: {query[:100]}...")
            
            # Step 1: Enhanced query optimization for diagrams
            optimized_query = self._enhanced_query_optimization(query)
            
            # Step 2: Enhanced code retrieval using dedicated retriever
            code_docs = self.code_retriever.retrieve_code_documents(optimized_query)
            
            if not code_docs:
                return self._create_no_results_response(query)
            
            # Step 3: Enhanced diagram type detection
            diagram_type = self._enhanced_diagram_type_detection(query, code_docs)
            logger.info(f"Detected diagram type: {diagram_type}")
            
            # Step 4: Generate appropriate diagram
            diagram_result = self.diagram_generators[diagram_type](code_docs, optimized_query)
            
            # Step 5: Response quality enhancement (if available)
            if self.response_enhancer:
                try:
                    enhanced_response = self.response_enhancer.enhance_diagram_response(
                        diagram_result, query, diagram_type
                    )
                    diagram_result["answer"] = enhanced_response
                except Exception as e:
                    logger.warning(f"Response enhancement failed: {str(e)}")
            
            # Ensure consistent response format
            return self._format_response(diagram_result, query, diagram_type)
            
        except Exception as e:
            logger.error(f"Diagram generation failed: {str(e)}")
            return self._create_error_response(str(e))
    
    def _enhanced_query_optimization(self, query: str) -> str:
        """
        Enhanced query optimization specifically for diagram generation
        
        Args:
            query: Original user query
            
        Returns:
            Optimized query string
        """
        # Use the new diagram-specific query optimizer
        optimized_query = self.diagram_query_optimizer.optimize_for_diagrams(query)
        
        # If external query optimizer is available, use it as well
        if self.query_optimizer:
            try:
                external_optimized = self.query_optimizer.optimize_for_diagrams(query)
                if external_optimized != query:
                    # Combine both optimizations
                    optimized_query = f"{optimized_query} {external_optimized}"
                    logger.debug(f"Combined query optimization: {optimized_query[:100]}")
            except Exception as e:
                logger.warning(f"External query optimization failed: {str(e)}")
        
        logger.debug(f"Query optimized: {query[:50]} -> {optimized_query[:50]}")
        return optimized_query
    
    def _enhanced_diagram_type_detection(self, query: str, code_docs: List[Document]) -> str:
        """
        Enhanced diagram type detection using code analysis and intent
        
        Args:
            query: User query
            code_docs: Retrieved code documents
            
        Returns:
            String indicating diagram type
        """
        # Extract diagram intent from query
        intent = self.diagram_query_optimizer.extract_diagram_intent(query)
        
        # Use preferred type if available
        if intent.get('preferred_type'):
            logger.info(f"Using preferred diagram type from intent: {intent['preferred_type']}")
            return intent['preferred_type']
        
        # Fallback to code analysis
        return self._suggest_diagram_type_from_code(code_docs)
        # First, check for direct type specification in query
        query_lower = query.lower()
        for diagram_type, keywords in self.diagram_type_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return diagram_type
        
        # Use intent analysis for better detection
        intent = self.diagram_query_optimizer.extract_diagram_intent(query)
        if intent.get('preferred_type') and intent.get('confidence', 0) > 0.5:
            return intent['preferred_type']
        
        # Analyze code content to suggest type
        return self._suggest_diagram_type_from_code(code_docs)
    
    def _suggest_diagram_type_from_code(self, code_docs: List[Document]) -> str:
        """Suggest diagram type based on code content analysis using existing SequenceDetector"""
        # Use the existing SequenceDetector for code analysis
        type_scores = {'sequence': 0, 'flowchart': 0, 'class': 0, 'component': 0}
        
        for doc in code_docs:
            language = self._detect_language_from_path(doc.metadata.get('file_path', ''))
            
            # Use existing SequenceDetector to analyze the code
            analysis = self.sequence_detector.analyze_code(doc.page_content, language)
            
            if analysis and analysis.get('interactions'):
                # Analyze the patterns found by SequenceDetector
                interactions = analysis['interactions']
                
                # Score based on interaction patterns
                type_scores['sequence'] += len(interactions)
                
                # Look for specific patterns in the interactions
                for interaction in interactions:
                    method = interaction.get('method', '').lower()
                    caller = interaction.get('caller', '').lower()
                    
                    # Class-related patterns
                    if any(keyword in method for keyword in ['class', 'extends', 'implements']):
                        type_scores['class'] += 2
                    
                    # Component-related patterns
                    if any(keyword in caller for keyword in ['service', 'controller', 'component']):
                        type_scores['component'] += 2
                    
                    # Flow control patterns
                    if any(keyword in method for keyword in ['if', 'while', 'for', 'switch']):
                        type_scores['flowchart'] += 2
        
        # Return the type with highest score, default to sequence
        if max(type_scores.values()) > 0:
            return max(type_scores.items(), key=lambda x: x[1])[0]
        
        # Fallback to simple heuristic
        return self._simple_pattern_heuristic(code_docs)
    
    def _simple_pattern_heuristic(self, code_docs: List[Document]) -> str:
        """Simple heuristic-based pattern detection as fallback"""
        sequence_indicators = ['def ', 'class ', 'function ', 'method ', 'call', 'invoke']
        flowchart_indicators = ['if ', 'else', 'for ', 'while ', 'switch ', 'case ']
        class_indicators = ['class ', 'extends ', 'implements ', 'interface ']
        
        sequence_score = 0
        flowchart_score = 0
        class_score = 0
        
        for doc in code_docs:
            content = doc.page_content.lower()
            
            for indicator in sequence_indicators:
                sequence_score += content.count(indicator)
            
            for indicator in flowchart_indicators:
                flowchart_score += content.count(indicator)
            
            for indicator in class_indicators:
                class_score += content.count(indicator)
        
        # Return the type with highest score, default to sequence
        scores = {
            'sequence': sequence_score,
            'flowchart': flowchart_score,
            'class': class_score
        }
        
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def _deduplicate_and_rank_results(self, results: List[Document], query: str, intent: Dict[str, Any]) -> List[Document]:
        """Remove duplicates and rank results by relevance with intent awareness"""
        # Simple deduplication by content hash
        seen_content = set()
        unique_results = []
        
        for doc in results:
            content_hash = hash(doc.page_content[:100])  # Hash first 100 chars
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(doc)
        
        # Enhanced ranking with intent awareness
        def relevance_score(doc):
            score = 0
            query_lower = query.lower()
            content_lower = doc.page_content.lower()
            
            # Basic term frequency scoring
            for term in query_lower.split():
                if len(term) > 2:  # Skip short words
                    score += content_lower.count(term)
            
            # Intent-based scoring
            if intent.get('preferred_type'):
                diagram_type = intent['preferred_type']
                # Simple pattern matching for relevance (inline)
                patterns = {
                    'sequence': ['def ', 'function ', 'method ', 'call', 'invoke'],
                    'flowchart': ['if ', 'else', 'for ', 'while ', 'switch ', 'case '],
                    'class': ['class ', 'extends ', 'implements ', 'interface '],
                    'er': ['@entity', '@table', 'create table', 'foreign key'],
                    'component': ['@component', '@service', '@controller', '@repository']
                }
                relevant_patterns = patterns.get(diagram_type, [])
                if any(pattern in content_lower for pattern in relevant_patterns):
                    score += 5  # Bonus for relevant patterns
            
            # Repository relevance scoring
            if intent.get('keywords'):
                for keyword in intent['keywords']:
                    if keyword in content_lower:
                        score += 3
            
            # File type relevance scoring
            file_type = doc.metadata.get('file_type', '')
            if intent.get('preferred_type'):
                # Inline file type mapping
                type_mapping = {
                    'sequence': ['py', 'js', 'ts', 'cs'],
                    'flowchart': ['py', 'js', 'ts', 'cs'],
                    'class': ['py', 'js', 'ts', 'cs'],
                    'er': ['cs', 'sql', 'py'],
                    'component': ['cs', 'js', 'ts', 'py']
                }
                preferred_types = type_mapping.get(intent['preferred_type'], [])
                if any(ft in file_type for ft in preferred_types):
                    score += 2
            
            return score
        
        # Sort by relevance score (descending)
        unique_results.sort(key=relevance_score, reverse=True)
        
        return unique_results
    
    def _filter_code_documents(self, documents: List[Document]) -> List[Document]:
        """Filter documents by code quality and relevance"""
        filtered = []
        
        for doc in documents:
            # Check if document contains actual code
            content = doc.page_content.strip()
            
            # Skip empty or very short documents
            if len(content) < 10:  # Reduced threshold for better coverage
                continue
            
            # Check for code indicators (expanded list)
            code_indicators = [
                'def ', 'class ', 'function ', 'public ', 'private ', 'var ', 'const ', 'let ',
                'if ', 'for ', 'while ', 'return', 'import ', 'from ', '@', '{', '}', ';',
                'namespace', 'using', 'interface', 'enum', 'struct', 'async', 'await',
                'controller', 'service', 'repository', 'component', 'module', 'export'
            ]
            has_code = any(indicator in content for indicator in code_indicators)
            
            # Check for markdown or documentation - allow documentation for architecture diagrams
            is_pure_documentation = (
                content.startswith('#') and 
                not any(indicator in content for indicator in code_indicators) and
                len(content.split('\n')) < 5  # Very short pure documentation
            )
            
            # Include document if it has code OR if it's not pure documentation
            # For architecture diagrams, we want to be more inclusive
            if has_code or not is_pure_documentation:
                filtered.append(doc)
        
        return filtered
    
    def _generate_sequence_diagram(self, code_docs: List[Document], query: str) -> Dict[str, Any]:
        """Generate sequence diagram using existing sequence detector"""
        try:
            # Use existing sequence detector logic - analyze each document individually
            sequence_patterns = []
            for doc in code_docs:
                language = self._detect_language_from_path(doc.metadata.get('file_path', ''))
                pattern = self.sequence_detector.analyze_code(doc.page_content, language, query)
                if pattern and pattern.get('interactions'):
                    pattern['source_file'] = doc.metadata.get('file_path', 'unknown')
                    pattern['repository'] = doc.metadata.get('repository', 'unknown')
                    sequence_patterns.append(pattern)
            
            if not sequence_patterns:
                return {
                    "analysis_summary": "No sequence patterns found in the code. The code may not contain clear interaction flows or may be too simple for sequence diagram generation.",
                    "mermaid_code": None,
                    "diagram_type": "sequence",
                    "source_documents": self._format_source_docs(code_docs),
                    "status": "warning"
                }
            
            # Generate mermaid sequence diagram
            mermaid_code = self._create_sequence_mermaid(sequence_patterns)
            
            return {
                "analysis_summary": f"Generated sequence diagram showing {len(sequence_patterns)} interaction patterns found in the code.",
                "mermaid_code": mermaid_code,
                "diagram_type": "sequence",
                "source_documents": self._format_source_docs(code_docs),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Sequence diagram generation failed: {str(e)}")
            return {
                "analysis_summary": f"Error generating sequence diagram: {str(e)}",
                "mermaid_code": None,
                "diagram_type": "sequence",
                "source_documents": self._format_source_docs(code_docs),
                "status": "error"
            }
    
    def _generate_flowchart(self, code_docs: List[Document], query: str) -> Dict[str, Any]:
        """Generate flowchart diagram"""
        try:
            # Extract process flows and decision points
            flow_patterns = self._extract_flow_patterns(code_docs)
            
            if not flow_patterns:
                # Generate a simple default flowchart even when no patterns are found
                default_mermaid = self._create_flowchart_mermaid([])
                return {
                    "analysis_summary": "No flow patterns found in the code. The code may not contain clear decision points or process flows.",
                    "mermaid_code": default_mermaid,
                    "diagram_type": "flowchart",
                    "source_documents": self._format_source_docs(code_docs),
                    "status": "warning"
                }
            
            # Generate mermaid flowchart
            mermaid_code = self._create_flowchart_mermaid(flow_patterns)
            
            return {
                "analysis_summary": f"Generated flowchart showing {len(flow_patterns)} flow patterns found in the code.",
                "mermaid_code": mermaid_code,
                "diagram_type": "flowchart",
                "source_documents": self._format_source_docs(code_docs),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Flowchart generation failed: {str(e)}")
            return {
                "analysis_summary": f"Error generating flowchart: {str(e)}",
                "mermaid_code": None,
                "diagram_type": "flowchart",
                "source_documents": self._format_source_docs(code_docs),
                "status": "error"
            }
    
    def _generate_class_diagram(self, code_docs: List[Document], query: str) -> Dict[str, Any]:
        """Generate class diagram"""
        try:
            # Extract class structures and relationships
            class_patterns = self._extract_class_patterns(code_docs)
            
            if not class_patterns:
                # Generate a simple default class diagram even when no patterns are found
                default_mermaid = self._create_class_diagram_mermaid([])
                return {
                    "analysis_summary": "No class patterns found in the code. The code may not contain object-oriented structures.",
                    "mermaid_code": default_mermaid,
                    "diagram_type": "class",
                    "source_documents": self._format_source_docs(code_docs),
                    "status": "warning"
                }
            
            # Generate mermaid class diagram
            mermaid_code = self._create_class_diagram_mermaid(class_patterns)
            
            return {
                "analysis_summary": f"Generated class diagram showing {len(class_patterns)} class structures found in the code.",
                "mermaid_code": mermaid_code,
                "diagram_type": "class",
                "source_documents": self._format_source_docs(code_docs),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Class diagram generation failed: {str(e)}")
            return {
                "analysis_summary": f"Error generating class diagram: {str(e)}",
                "mermaid_code": None,
                "diagram_type": "class",
                "source_documents": self._format_source_docs(code_docs),
                "status": "error"
            }
    
    def _generate_er_diagram(self, code_docs: List[Document], query: str) -> Dict[str, Any]:
        """Generate Entity-Relationship diagram"""
        try:
            # Extract entity and relationship patterns
            er_patterns = self._extract_er_patterns(code_docs)
            
            if not er_patterns:
                # Generate a simple default ER diagram even when no patterns are found
                default_mermaid = self._create_er_diagram_mermaid([])
                return {
                    "analysis_summary": "No entity-relationship patterns found in the code. The code may not contain database or data modeling structures.",
                    "mermaid_code": default_mermaid,
                    "diagram_type": "er",
                    "source_documents": self._format_source_docs(code_docs),
                    "status": "warning"
                }
            
            # Generate mermaid ER diagram
            mermaid_code = self._create_er_diagram_mermaid(er_patterns)
            
            return {
                "analysis_summary": f"Generated ER diagram showing {len(er_patterns)} entity-relationship patterns found in the code.",
                "mermaid_code": mermaid_code,
                "diagram_type": "er",
                "source_documents": self._format_source_docs(code_docs),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"ER diagram generation failed: {str(e)}")
            return {
                "analysis_summary": f"Error generating ER diagram: {str(e)}",
                "mermaid_code": None,
                "diagram_type": "er",
                "source_documents": self._format_source_docs(code_docs),
                "status": "error"
            }
    
    def _generate_component_diagram(self, code_docs: List[Document], query: str) -> Dict[str, Any]:
        """Generate component diagram"""
        try:
            # Extract component and architecture patterns
            component_patterns = self._extract_component_patterns(code_docs)
            
            if not component_patterns:
                # Generate a simple default component diagram even when no patterns are found
                default_mermaid = self._create_component_diagram_mermaid([])
                return {
                    "analysis_summary": "No component patterns found in the code. The code may not contain clear architectural components.",
                    "mermaid_code": default_mermaid,
                    "diagram_type": "component",
                    "source_documents": self._format_source_docs(code_docs),
                    "status": "warning"
                }
            
            # Generate mermaid component diagram
            mermaid_code = self._create_component_diagram_mermaid(component_patterns)
            
            return {
                "analysis_summary": f"Generated component diagram showing {len(component_patterns)} architectural components found in the code.",
                "mermaid_code": mermaid_code,
                "diagram_type": "component",
                "source_documents": self._format_source_docs(code_docs),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Component diagram generation failed: {str(e)}")
            return {
                "analysis_summary": f"Error generating component diagram: {str(e)}",
                "mermaid_code": None,
                "diagram_type": "component",
                "source_documents": self._format_source_docs(code_docs),
                "status": "error"
            }
    
    def _generate_architecture_diagram(self, code_docs: List[Document], query: str) -> Dict[str, Any]:
        """Generate architecture diagram (alias of component diagram with proper labeling)"""
        try:
            # 1) Build from metadata only (no content parsing) for correctness
            meta_patterns = self.pattern_extractor.extract_architecture_from_metadata(code_docs)
            patterns = meta_patterns
            
            # 2) If metadata yields nothing, fall back to code-based extraction
            if not patterns:
                component_patterns = self._extract_component_patterns(code_docs)
                patterns = component_patterns
            
            if not patterns:
                default_mermaid = self._create_component_diagram_mermaid([])
                return {
                    "analysis_summary": "No architecture components found in the code. The code may not contain clear architectural components.",
                    "mermaid_code": default_mermaid,
                    "diagram_type": "architecture",
                    "source_documents": self._format_source_docs(code_docs),
                    "status": "warning"
                }
            
            mermaid_code = self._create_component_diagram_mermaid(patterns)
            
            return {
                "analysis_summary": f"Generated architecture diagram showing {len(patterns)} components and dependencies found in the code.",
                "mermaid_code": mermaid_code,
                "diagram_type": "architecture",
                "source_documents": self._format_source_docs(code_docs),
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Architecture diagram generation failed: {str(e)}")
            return {
                "analysis_summary": f"Error generating architecture diagram: {str(e)}",
                "mermaid_code": None,
                "diagram_type": "architecture",
                "source_documents": self._format_source_docs(code_docs),
                "status": "error"
            }
    
    # Placeholder methods for pattern extraction and mermaid generation
    # These will be implemented in future tasks
    
    def _extract_flow_patterns(self, code_docs: List[Document]) -> List[Dict[str, Any]]:
        """Extract flow patterns from code documents"""
        return self.pattern_extractor.extract_flow_patterns(code_docs)
    
    def _extract_class_patterns(self, code_docs: List[Document]) -> List[Dict[str, Any]]:
        """Extract class patterns from code documents"""
        return self.pattern_extractor.extract_class_patterns(code_docs)
    
    def _extract_er_patterns(self, code_docs: List[Document]) -> List[Dict[str, Any]]:
        """Extract entity-relationship patterns from code documents"""
        return self.pattern_extractor.extract_er_patterns(code_docs)
    
    def _extract_component_patterns(self, code_docs: List[Document]) -> List[Dict[str, Any]]:
        """Extract component patterns from code documents"""
        return self.pattern_extractor.extract_component_patterns(code_docs)
    
    def _create_sequence_mermaid(self, patterns: List[Dict[str, Any]]) -> str:
        """Create mermaid sequence diagram code"""
        return self.mermaid_generator.create_enhanced_sequence_mermaid(patterns)
    
    def _create_flowchart_mermaid(self, patterns: List[Dict[str, Any]]) -> str:
        """Create mermaid flowchart code"""
        return self.mermaid_generator.create_flowchart_mermaid(patterns)
    
    def _create_class_diagram_mermaid(self, patterns: List[Dict[str, Any]]) -> str:
        """Create mermaid class diagram code"""
        return self.mermaid_generator.create_class_diagram_mermaid(patterns)
    
    def _create_er_diagram_mermaid(self, patterns: List[Dict[str, Any]]) -> str:
        """Create mermaid ER diagram code"""
        return self.mermaid_generator.create_er_diagram_mermaid(patterns)
    
    def _create_component_diagram_mermaid(self, patterns: List[Dict[str, Any]]) -> str:
        """Create mermaid component diagram code"""
        return self.mermaid_generator.create_component_diagram_mermaid(patterns)
    
    def _format_source_docs(self, docs: List[Document]) -> List[Dict[str, Any]]:
        """Format source documents for response"""
        formatted = []
        for doc in docs:
            formatted.append({
                "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                "metadata": doc.metadata,
                "source": doc.metadata.get('file_path', 'Unknown')
            })
        return formatted
    
    def _format_response(self, diagram_result: Dict[str, Any], query: str, diagram_type: str) -> Dict[str, Any]:
        """Format response to match expected structure"""
        return {
            "answer": diagram_result.get("analysis_summary", "Diagram generated successfully"),
            "source_documents": diagram_result.get("source_documents", []),
            "status": diagram_result.get("status", "success"),
            "num_sources": len(diagram_result.get("source_documents", [])),
            "mermaid_code": diagram_result.get("mermaid_code"),
            "diagram_type": diagram_type,
            "error": diagram_result.get("error")
        }
    
    def _create_no_results_response(self, query: str) -> Dict[str, Any]:
        """Create response when no relevant code is found"""
        return {
            "answer": f"No relevant code found for generating a diagram based on your query: '{query}'. Please try:\n\n1. Specifying a particular repository or code area\n2. Using more specific terms about the code you want to visualize\n3. Checking if the relevant code has been indexed in the knowledge base",
            "source_documents": [],
            "status": "no_results",
            "num_sources": 0,
            "mermaid_code": None,
            "diagram_type": None,
            "error": None
        }
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            "answer": f"I encountered an error while generating the diagram: {error_message}. Please try again or contact support if the issue persists.",
            "source_documents": [],
            "status": "error",
            "num_sources": 0,
            "mermaid_code": None,
            "diagram_type": None,
            "error": error_message
        }
    
    def get_supported_diagram_types(self) -> List[str]:
        """Get list of supported diagram types"""
        return list(self.diagram_generators.keys())
    
    def get_diagram_type_description(self, diagram_type: str) -> str:
        """Get description of a specific diagram type"""
        descriptions = {
            'sequence': 'Shows interactions between components over time',
            'flowchart': 'Represents process flows and decision points',
            'class': 'Displays class structures and relationships',
            'er': 'Shows entity-relationship data models',
            'component': 'Illustrates system architecture and components',
            'architecture': 'High-level system architecture and component dependencies'
        }
        return descriptions.get(diagram_type, 'Unknown diagram type')



