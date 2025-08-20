"""
Code Analysis Utilities for Enhanced Code Retrieval

This module provides utilities for analyzing code structure, patterns, and relationships
to support enhanced code retrieval in the DiagramAgent. It leverages the existing
SequenceDetector for robust code analysis.
"""

import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from langchain.docstore.document import Document


@dataclass
class CodePattern:
    """Represents a detected code pattern"""
    pattern_type: str
    confidence: float
    metadata: Dict[str, Any]
    source_document: Document


@dataclass
class CodeStructure:
    """Represents code structure analysis"""
    classes: List[Dict[str, Any]]
    functions: List[Dict[str, Any]]
    imports: List[str]
    dependencies: List[str]
    patterns: List[CodePattern]


class CodePatternDetector:
    """Detects code patterns using simple keywords for enhanced retrieval"""
    
    def __init__(self):
        # Simple pattern keywords for basic analysis
        self.pattern_keywords = {
            'sequence': ['def ', 'function ', 'method ', 'call', 'invoke', '()'],
            'flowchart': ['if ', 'else', 'for ', 'while ', 'switch ', 'case '],
            'class': ['class ', 'extends ', 'implements ', 'interface '],
            'er': ['@entity', '@table', 'create table', 'foreign key'],
            'component': ['@component', '@service', '@controller', '@repository']
        }
    
    def detect_patterns(self, documents: List[Document]) -> CodeStructure:
        """
        Detect code patterns across multiple documents using simple keywords
        
        Args:
            documents: List of code documents to analyze
            
        Returns:
            CodeStructure containing detected patterns
        """
        classes = []
        functions = []
        imports = []
        dependencies = []
        patterns = []
        
        for doc in documents:
            content = doc.page_content
            file_type = doc.metadata.get('file_type', 'unknown')
            
            # Simple pattern detection based on keywords
            for pattern_type, keywords in self.pattern_keywords.items():
                for keyword in keywords:
                    if keyword in content.lower():
                        pattern = CodePattern(
                            pattern_type=pattern_type,
                            confidence=0.7,
                            metadata={'keyword': keyword, 'count': content.lower().count(keyword)},
                            source_document=doc
                        )
                        patterns.append(pattern)
            
            # Simple class and function detection
            if 'class ' in content:
                classes.append({'name': 'DetectedClass', 'type': file_type})
            if any(keyword in content for keyword in ['def ', 'function ', 'method ']):
                functions.append({'name': 'DetectedFunction', 'type': file_type})
        
        return CodeStructure(
            classes=classes,
            functions=functions,
            imports=imports,
            dependencies=dependencies,
            patterns=patterns
        )


class QueryOptimizer:
    """Optimizes queries for diagram generation"""
    
    def __init__(self):
        self.diagram_keywords = {
            'sequence': ['sequence', 'interaction', 'call', 'flow', 'interaction diagram', 'method call'],
            'flowchart': ['flowchart', 'flow', 'process', 'workflow', 'decision', 'steps', 'control flow'],
            'class': ['class', 'structure', 'object', 'inheritance', 'composition', 'uml class'],
            'er': ['entity', 'relationship', 'database', 'schema', 'table', 'data model'],
            'component': ['component', 'architecture', 'system', 'module', 'service', 'microservice']
        }
    
    def optimize_for_diagrams(self, query: str) -> str:
        """
        Optimize query for diagram generation
        
        Args:
            query: Original user query
            
        Returns:
            Optimized query string
        """
        query_lower = query.lower()
        
        # Add diagram-specific terms if not present
        for diagram_type, keywords in self.diagram_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                # Query already contains diagram-specific terms
                return query
        
        # Add general diagram terms if none detected
        enhanced_query = query + " diagram visualization code structure"
        return enhanced_query
    
    def extract_diagram_intent(self, query: str) -> Dict[str, Any]:
        """
        Extract diagram generation intent from query
        
        Args:
            query: User query
            
        Returns:
            Dictionary containing intent analysis
        """
        query_lower = query.lower()
        intent = {
            'is_diagram_request': False,
            'preferred_type': None,
            'confidence': 0.0,
            'keywords': []
        }
        
        # Check if this is a diagram request
        diagram_indicators = ['diagram', 'visualize', 'show', 'draw', 'create', 'generate']
        if any(indicator in query_lower for indicator in diagram_indicators):
            intent['is_diagram_request'] = True
            intent['confidence'] += 0.3
        
        # Detect preferred diagram type
        type_scores = {}
        for diagram_type, keywords in self.diagram_keywords.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                type_scores[diagram_type] = score
                intent['keywords'].extend([k for k in keywords if k in query_lower])
        
        if type_scores:
            intent['preferred_type'] = max(type_scores, key=type_scores.get)
            intent['confidence'] += 0.4
        
        # Additional confidence for specific technical terms
        technical_terms = ['api', 'database', 'class', 'function', 'method', 'service', 'component']
        tech_score = sum(1 for term in technical_terms if term in query_lower)
        intent['confidence'] += min(tech_score * 0.1, 0.3)
        
        return intent


class RepositoryFilter:
    """Filters code by repository and context"""
    
    def __init__(self):
        self.repository_patterns = [
            r'repository[:\s]+([a-zA-Z][\w\-]+)',       # repository: name or repository name
            r'repo[:\s]+([a-zA-Z][\w\-]+)',             # repo: name or repo name  
            r'in\s+([a-zA-Z][\w\-]+)\s+repository',     # in name repository
            r'from\s+([a-zA-Z][\w\-]+)\s+repository',   # from name repository
            # Removed the problematic patterns that match "word repository" as they're too generic
        ]
    
    def extract_repositories(self, query: str) -> List[str]:
        """
        Extract repository names from query
        
        Args:
            query: User query
            
        Returns:
            List of repository names
        """
        repositories = []
        
        for pattern in self.repository_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            repositories.extend(matches)
        
        # Clean and validate repository names
        cleaned_repos = []
        for repo in repositories:
            repo = repo.strip('.,;:')
            # Filter out common words that shouldn't be repositories
            if repo and len(repo) > 1 and repo.lower() not in ['no', 'mentioned', 'the', 'a', 'an', 'of', 'in', 'at', 'by']:
                cleaned_repos.append(repo)
        
        return list(set(cleaned_repos))
    
    def filter_by_repository(self, documents: List[Document], repositories: List[str]) -> List[Document]:
        """
        Filter documents by repository
        
        Args:
            documents: List of documents to filter
            repositories: List of repository names to include
            
        Returns:
            Filtered list of documents
        """
        if not repositories:
            return documents
        
        filtered = []
        for doc in documents:
            doc_repo = doc.metadata.get('repository', '')
            if any(repo.lower() in doc_repo.lower() for repo in repositories):
                filtered.append(doc)
        
        return filtered
    
    def filter_by_file_type(self, documents: List[Document], file_types: List[str]) -> List[Document]:
        """
        Filter documents by file type
        
        Args:
            documents: List of documents to filter
            file_types: List of file types to include
            
        Returns:
            Filtered list of documents
        """
        if not file_types:
            return documents
        
        filtered = []
        for doc in documents:
            doc_type = doc.metadata.get('file_type', '')
            if any(ft.lower() in doc_type.lower() for ft in file_types):
                filtered.append(doc)
        
        return filtered