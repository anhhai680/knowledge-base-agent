"""
Code Analysis Utilities for Enhanced Code Retrieval

This module provides utilities for analyzing code structure, patterns, and relationships
to support enhanced code retrieval in the DiagramAgent. It leverages the existing
SequenceDetector for robust code analysis.
"""

import re
from typing import Dict, Any, List
from dataclasses import dataclass
from langchain.docstore.document import Document
import logging

logger = logging.getLogger(__name__)


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
            'component': ['component', 'architecture', 'system', 'module', 'service', 'microservice', 'architectural', 'system design', 'service architecture']
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
        
        # Check if query already contains very specific, strong diagram terms
        # These are terms that clearly indicate a diagram request and don't need enhancement
        strong_diagram_terms = ['diagram', 'flowchart', 'sequence diagram', 'class diagram', 'er diagram', 'component diagram', 'architecture diagram', 'uml diagram']
        has_strong_diagram_terms = any(term in query_lower for term in strong_diagram_terms)
        
        # If query already contains strong diagram terms, don't modify it
        if has_strong_diagram_terms:
            return query
        
        # Check for specific technical terms that suggest diagram intent
        # Only these specific terms prevent enhancement
        specific_intent_terms = ['api calls', 'sequence', 'interaction', 'class structure', 'entity relationship']
        has_specific_intent = any(term in query_lower for term in specific_intent_terms)
        
        # If query has specific diagram intent, don't enhance it
        if has_specific_intent:
            return query
        
        # For all other queries, enhance them with diagram terms
        # This allows queries like "show me the user flow" to get enhanced
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
        diagram_indicators = ['diagram', 'visualize', 'show', 'draw', 'create', 'generate', 'architecture', 'system design']
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
            intent['preferred_type'] = max(type_scores.items(), key=lambda x: x[1])[0]
            intent['confidence'] += 0.4
        
        # Additional confidence for specific technical terms
        technical_terms = ['api', 'database', 'class', 'function', 'method', 'service', 'component', 'controller', 'repository']
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
        
        # First, check for explicit repository patterns
        for pattern in self.repository_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            repositories.extend(matches)
        
        # If no explicit repository found, try to infer from service names
        if not repositories:
            repositories = self._infer_repository_from_service(query)
        
        # Clean and validate repository names
        cleaned_repos = []
        for repo in repositories:
            repo = repo.strip('.,;:')
            # Filter out common words that shouldn't be repositories
            if repo and len(repo) > 1 and repo.lower() not in ['no', 'mentioned', 'the', 'a', 'an', 'of', 'in', 'at', 'by', 'repo', 'create', 'flowchart']:
                cleaned_repos.append(repo)
        
        return list(set(cleaned_repos))
    
    def _infer_repository_from_service(self, query: str) -> List[str]:
        """
        Infer repository from service names mentioned in the query
        
        Args:
            query: User query
            
        Returns:
            List of inferred repository names
        """
        query_lower = query.lower()
        inferred_repos = []
        
        logger.info(f"Inferring repository from service query: {query}")
        
        # Extract potential repository names from the query
        # Look for patterns like "open swe", "my-project", "service-name"
        words = query_lower.split()
        
        # Look for repository-like patterns (words that could be repo names)
        for word in words:
            # Skip common words and very short terms
            if len(word) < 3 or word in ['the', 'and', 'or', 'for', 'with', 'from', 'to', 'in', 'on', 'at', 'by', 'of', 'a', 'an', 'show', 'me', 'code', 'create', 'generate', 'diagram', 'flowchart', 'sequence']:
                continue
            
            # Clean up the word (remove special characters)
            clean_word = re.sub(r'[^\w\-_]', '', word)
            if len(clean_word) >= 3:
                # Check if this looks like a repository name
                # Only consider words that have repository-like characteristics
                if ('-' in clean_word or '_' in clean_word) and clean_word.islower():
                    logger.info(f"Found potential repository name: '{clean_word}'")
                    inferred_repos.append(clean_word)
        
        # If no specific patterns found, try to extract from context
        if not inferred_repos:
            logger.info("No specific repository patterns found, checking for architecture context...")
            # Look for architecture-related terms that might indicate a specific service
            architecture_terms = ['architecture', 'system design', 'service architecture', 'sequence', 'diagram']
            if any(term in query_lower for term in architecture_terms):
                # Don't default to any specific service - let the search find what's available
                logger.info("Architecture context detected, will search available repositories")
        
        logger.info(f"Repository inference result: {inferred_repos}")
        return inferred_repos
    
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
            if doc_repo:
                # Check if any of the specified repositories match the document repository
                for repo in repositories:
                    # More flexible matching - check if repo name is contained in the full repository URL
                    if repo.lower() in doc_repo.lower() or doc_repo.lower().endswith(f'/{repo.lower()}'):
                        filtered.append(doc)
                        break  # Found a match, no need to check other repos
            else:
                # If no repository metadata, skip the document for strict filtering
                continue
        
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