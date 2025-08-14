"""
DiagramHandler - Specialized agent for diagram generation using existing vector store capabilities
"""

from typing import Dict, Any, List
from langchain.docstore.document import Document
from ..processors.sequence_detector import SequenceDetector
from ..utils.logging import get_logger

logger = get_logger(__name__)


class DiagramHandler:
    """Specialized agent for diagram generation using existing vector store capabilities"""
    
    def __init__(self, vectorstore, llm):
        self.vectorstore = vectorstore
        self.llm = llm
        self.sequence_detector = SequenceDetector()
    
    def generate_sequence_diagram(self, query: str) -> Dict[str, Any]:
        """Generate sequence diagram using existing similarity search"""
        
        try:
            # Step 1: Use existing similarity_search to find relevant code
            code_docs = self._find_relevant_code(query)
            
            if not code_docs:
                return {
                    "analysis_summary": "No relevant code found for diagram generation",
                    "mermaid_code": None,
                    "diagram_type": "sequence",
                    "source_documents": [],
                    "status": "error"
                }
            
            # Step 2: Analyze patterns using existing metadata
            sequence_patterns = self._analyze_interaction_patterns(code_docs)
            
            if not sequence_patterns:
                return {
                    "analysis_summary": "No interaction patterns found in the code",
                    "mermaid_code": None,
                    "diagram_type": "sequence",
                    "source_documents": self._format_source_docs(code_docs),
                    "status": "error"
                }
            
            # Step 3: Generate Mermaid diagram
            mermaid_code = self._generate_mermaid_sequence(sequence_patterns)
            
            return {
                "analysis_summary": self._create_analysis_summary(sequence_patterns),
                "mermaid_code": mermaid_code,
                "diagram_type": "sequence",
                "source_documents": self._format_source_docs(code_docs),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Diagram generation failed: {str(e)}")
            return {
                "analysis_summary": "Failed to generate diagram due to processing error",
                "mermaid_code": None,
                "diagram_type": "sequence",
                "source_documents": [],
                "status": "error"
            }
    
    def _find_relevant_code(self, query: str) -> List[Document]:
        """Leverage existing ChromaStore.similarity_search()"""
        try:
            # Use existing vector search - no new implementation needed
            results = self.vectorstore.similarity_search(
                query=query,
                k=20  # Get more results for comprehensive analysis
            )
            
            # Filter for supported languages using existing metadata
            supported_languages = {'python', 'javascript', 'typescript', 'csharp'}
            filtered_results = []
            
            for doc in results:
                file_path = doc.metadata.get('file_path', '')
                language = self._detect_language_from_path(file_path)
                if language in supported_languages:
                    filtered_results.append(doc)
            
            logger.info(f"Found {len(filtered_results)} relevant code documents out of {len(results)} total")
            return filtered_results[:15]  # Limit for processing efficiency
            
        except Exception as e:
            logger.error(f"Failed to find relevant code: {str(e)}")
            return []
    
    def _analyze_interaction_patterns(self, docs: List[Document]) -> List[Dict]:
        """Analyze code for interaction patterns"""
        patterns = []
        
        for doc in docs:
            language = self._detect_language_from_path(doc.metadata.get('file_path', ''))
            pattern = self.sequence_detector.analyze_code(doc.page_content, language)
            if pattern and pattern.get('interactions'):
                pattern['source_file'] = doc.metadata.get('file_path', 'unknown')
                pattern['repository'] = doc.metadata.get('repository', 'unknown')
                patterns.append(pattern)
        
        logger.info(f"Analyzed {len(patterns)} code files with interaction patterns")
        return patterns
    
    def _generate_mermaid_sequence(self, patterns: List[Dict]) -> str:
        """Generate Mermaid sequence diagram code"""
        mermaid_lines = ["sequenceDiagram"]
        participants = set()
        interactions = []
        
        # Extract participants and interactions
        for pattern in patterns:
            if pattern.get('interactions'):
                for interaction in pattern['interactions']:
                    caller = interaction.get('caller', 'Unknown')
                    callee = interaction.get('callee', 'Unknown')
                    method = interaction.get('method', 'unknownMethod')
                    
                    # Filter out common noise patterns
                    if self._is_valid_interaction(caller, callee, method):
                        participants.add(caller)
                        participants.add(callee)
                        interactions.append((caller, callee, method))
        
        # Add participants
        for participant in sorted(participants):
            mermaid_lines.append(f"    participant {self._sanitize_name(participant)}")
        
        # Add interactions (limit to prevent overcrowding)
        unique_interactions = list(set(interactions))[:15]  # Limit interactions
        for caller, callee, method in unique_interactions:
            sanitized_caller = self._sanitize_name(caller)
            sanitized_callee = self._sanitize_name(callee)
            mermaid_lines.append(f"    {sanitized_caller}->>+{sanitized_callee}: {method}")
            mermaid_lines.append(f"    {sanitized_callee}-->>-{sanitized_caller}: return")
        
        return "\\n".join(mermaid_lines)
    
    def _is_valid_interaction(self, caller: str, callee: str, method: str) -> bool:
        """Filter out noise and invalid interactions"""
        # Skip self-calls
        if caller == callee:
            return False
        
        # Skip common noise patterns
        noise_methods = {'get', 'set', 'toString', 'print', 'log', 'console', 'len', 'str'}
        if method.lower() in noise_methods:
            return False
        
        # Skip very short or generic names
        if len(caller) < 2 or len(callee) < 2 or len(method) < 2:
            return False
        
        return True
    
    def _detect_language_from_path(self, file_path: str) -> str:
        """Detect language from file extension"""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript', 
            '.ts': 'typescript',
            '.cs': 'csharp'
        }
        for ext, lang in ext_map.items():
            if file_path.endswith(ext):
                return lang
        return 'unknown'
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize names for Mermaid compatibility"""
        return name.replace(' ', '_').replace('-', '_').replace('.', '_')
    
    def _format_source_docs(self, docs: List[Document]) -> List[Dict]:
        """Format source documents for response"""
        formatted = []
        for doc in docs:
            formatted.append({
                "content": doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
                "metadata": doc.metadata
            })
        return formatted
    
    def _create_analysis_summary(self, patterns: List[Dict]) -> str:
        """Create human-readable analysis summary"""
        file_count = len(patterns)
        repo_count = len(set(p.get('repository', 'unknown') for p in patterns))
        interaction_count = sum(len(p.get('interactions', [])) for p in patterns)
        
        return f"Analyzed {file_count} files across {repo_count} repositories, found {interaction_count} interactions"