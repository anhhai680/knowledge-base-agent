"""
Enhanced Code Retrieval Module

This module provides sophisticated code retrieval functionality extracted from DiagramAgent.
It implements multi-strategy search, repository filtering, and semantic analysis for 
improved diagram generation.
"""

import logging
from typing import List, Dict, Any

from langchain.schema import Document

logger = logging.getLogger(__name__)


class EnhancedCodeRetriever:
    """
    Enhanced code retrieval with semantic analysis, repository filtering, and pattern detection.
    
    This class was extracted from DiagramAgent to follow Single Responsibility Principle
    and improve code maintainability.
    """
    
    def __init__(self, vectorstore, repository_filter, diagram_query_optimizer, diagram_type_keywords):
        """
        Initialize the Enhanced Code Retriever
        
        Args:
            vectorstore: Vector database for similarity search
            repository_filter: Component for filtering by repository
            diagram_query_optimizer: Component for optimizing queries
            diagram_type_keywords: Keywords mapping for diagram types
        """
        self.vectorstore = vectorstore
        self.repository_filter = repository_filter
        self.diagram_query_optimizer = diagram_query_optimizer
        self.diagram_type_keywords = diagram_type_keywords
    
    def retrieve_code_documents(self, query: str) -> List[Document]:
        """
        Enhanced code retrieval with semantic analysis, repository filtering, and pattern detection
        
        Args:
            query: Optimized query for diagram generation
            
        Returns:
            List of relevant code documents
        """
        try:
            # Extract repository information from query
            repositories = self.repository_filter.extract_repositories(query)
            
            # Extract diagram intent and optimize search terms
            intent = self.diagram_query_optimizer.extract_diagram_intent(query)
            search_terms = self._extract_semantic_search_terms(query, intent)
            
            # If specific repository is mentioned, prioritize it heavily
            if repositories:
                logger.info(f"Repository-specific query detected: {repositories}")
                # Use strict repository filtering
                all_results = self._strict_repository_search(search_terms, repositories, intent)
            else:
                # Fall back to multi-strategy search
                all_results = self._multi_strategy_search(search_terms, repositories, intent)
            
            if not all_results:
                logger.warning("No results found in enhanced code retrieval")
                return []
            
            # Enhanced result processing with strict repository filtering
            processed_results = self._enhanced_result_processing(all_results, query, intent)
            
            logger.info(f"Enhanced retrieval: {len(processed_results)} relevant documents found")
            return processed_results[:25]  # Increased limit for better coverage
            
        except Exception as e:
            logger.error(f"Enhanced code retrieval failed: {str(e)}")
            # Return empty results instead of re-raising the exception
            return []
    
    def _multi_strategy_search(self, search_terms: List[str], repositories: List[str], intent: Dict[str, Any]) -> List[Document]:
        """
        Perform multi-strategy search with enhanced filtering
        
        Args:
            search_terms: List of search terms
            repositories: List of repository names to filter by
            intent: Diagram generation intent
            
        Returns:
            List of search results
        """
        all_results = []
        all_errors = []
        
        # Strategy 1: Repository-specific search
        if repositories:
            for repo in repositories:
                try:
                    repo_results = self._search_repository_with_context(repo, search_terms, intent)
                    all_results.extend(repo_results)
                except Exception as e:
                    all_errors.append(f"Repository search for {repo}: {str(e)}")
                    logger.warning(f"Repository search failed for {repo}: {str(e)}")
        
        # Strategy 2: Intent-based search
        if intent.get('preferred_type'):
            try:
                intent_results = self._search_by_diagram_intent(search_terms, intent)
                all_results.extend(intent_results)
            except Exception as e:
                all_errors.append(f"Intent-based search: {str(e)}")
                logger.warning(f"Intent-based search failed: {str(e)}")
        
        # Strategy 3: General semantic search
        for term in search_terms:
            try:
                results = self.vectorstore.similarity_search(term, k=20)
                all_results.extend(results)
            except Exception as e:
                all_errors.append(f"Semantic search for '{term}': {str(e)}")
                logger.warning(f"Search failed for term '{term}': {str(e)}")
        
        # Strategy 4: Pattern-based search for diagram types
        try:
            pattern_results = self._search_by_code_patterns(intent)
            all_results.extend(pattern_results)
        except Exception as e:
            all_errors.append(f"Pattern search: {str(e)}")
            logger.warning(f"Pattern search failed: {str(e)}")
        
        # Log errors but don't fail completely - return whatever results we have
        if all_errors:
            logger.warning(f"Some search strategies failed: {'; '.join(all_errors[:3])}")
        
        return all_results
    
    def _strict_repository_search(self, search_terms: List[str], repositories: List[str], intent: Dict[str, Any]) -> List[Document]:
        """
        Perform a strict repository-specific search.
        This method prioritizes results from the specified repositories and filters out others.
        """
        results = []
        all_errors = []
        
        logger.info(f"Performing strict repository search for repositories: {repositories}")
        logger.info(f"Search terms: {search_terms}")
        
        for repo in repositories:
            try:
                # Search without filtering first, then filter results
                search_query = search_terms[0] if search_terms else "service"
                
                logger.info(f"Searching with query: '{search_query}' for repository: {repo}")
                # Search with a larger k to get more candidates, then filter
                repo_results = self.vectorstore.similarity_search(search_query, k=50)
                
                # Filter results by repository
                filtered_results = []
                for result in repo_results:
                    result_repo = result.metadata.get('repository', '')
                    # Check if the repository name is contained in the result repository
                    repo_name = repo.split('/')[-1] if '/' in repo else repo
                    if repo_name.lower() in result_repo.lower():
                        filtered_results.append(result)
                
                logger.info(f"Found {len(repo_results)} total results, {len(filtered_results)} from repository {repo}")
                
                # Log some sample results for debugging
                for i, result in enumerate(filtered_results[:3]):
                    result_repo = result.metadata.get('repository', 'unknown')
                    logger.debug(f"Result {i+1}: {result_repo} - {result.metadata.get('file_path', 'unknown')}")
                
                # Filter by diagram intent if available
                if intent.get('preferred_type'):
                    intent_filtered = self._filter_by_diagram_intent(filtered_results, intent)
                    results.extend(intent_filtered)
                    logger.info(f"After intent filtering: {len(intent_filtered)} results")
                else:
                    results.extend(filtered_results)
                    
            except Exception as e:
                all_errors.append(f"Strict repository search for {repo}: {str(e)}")
                logger.warning(f"Strict repository search failed for {repo}: {str(e)}")
        
        logger.info(f"Total results from strict repository search: {len(results)}")
        
        # If no results from strict search, try a more lenient approach
        if not results and repositories:
            logger.warning(f"Strict repository search failed for all repositories. Trying lenient search...")
            try:
                # Try to search with just the repository name as a search term
                for repo in repositories:
                    repo_name = repo.split('/')[-1] if '/' in repo else repo
                    logger.info(f"Trying lenient search for repository: {repo_name}")
                    
                    # Search with repository name as part of the query
                    lenient_query = f"{repo_name} service architecture"
                    lenient_results = self.vectorstore.similarity_search(lenient_query, k=30)
                    
                    # Filter by repository (more lenient)
                    for result in lenient_results:
                        result_repo = result.metadata.get('repository', '')
                        if repo_name.lower() in result_repo.lower():
                            results.append(result)
                    
                    if results:
                        logger.info(f"Lenient search found {len(results)} results for {repo_name}")
                        break
                        
            except Exception as e:
                logger.warning(f"Lenient search also failed: {str(e)}")
        
        # If still no results, fall back to multi-strategy search
        if not results and repositories:
            logger.warning(f"All repository search strategies failed. Falling back to multi-strategy search for terms: {search_terms}")
            return self._multi_strategy_search(search_terms, repositories, intent)
        
        return results
    
    def _search_repository_with_context(self, repository: str, search_terms: List[str], intent: Dict[str, Any]) -> List[Document]:
        """Search within specific repository with context awareness"""
        results = []
        
        # Create repository-specific search query
        if search_terms:
            main_term = search_terms[0]
            search_query = f"{main_term} repository:{repository}"
        else:
            search_query = f"repository:{repository}"
        
        try:
            # Search with repository context
            repo_results = self.vectorstore.similarity_search(search_query, k=15)
            
            # Process results outside of the search exception handling
            if repo_results:
                try:
                    # Filter results by repository
                    filtered_results = []
                    for result in repo_results:
                        result_repo = result.metadata.get('repository', '')
                        if repository.lower() in result_repo.lower():
                            filtered_results.append(result)
                    
                    # Filter by diagram intent if available
                    if intent.get('preferred_type'):
                        results = self._filter_by_diagram_intent(filtered_results, intent)
                    else:
                        results = filtered_results
                        
                except Exception as e:
                    logger.warning(f"Result processing failed for {repository}: {str(e)}")
                    # Fallback: use original results if processing fails
                    results.extend(repo_results)
                    
        except Exception as e:
            logger.warning(f"Repository search failed for {repository}: {str(e)}")
        
        return results
    
    def _search_by_diagram_intent(self, search_terms: List[str], intent: Dict[str, Any]) -> List[Document]:
        """Search based on diagram generation intent"""
        results = []
        diagram_type = intent.get('preferred_type')
        
        if not diagram_type:
            return results
        
        # Create a combined search query that includes both search terms and diagram type
        if search_terms:
            # Use the first search term as the main query and add diagram context
            main_term = search_terms[0]
            search_query = f"{main_term} {diagram_type} diagram"
        else:
            # Fallback if no search terms
            search_query = f"{diagram_type} diagram"
        
        try:
            intent_results = self.vectorstore.similarity_search(search_query, k=10)
            results.extend(intent_results)
        except Exception as e:
            logger.warning(f"Intent-based search failed: {str(e)}")
        
        return results
    
    def _search_by_code_patterns(self, intent: Dict[str, Any]) -> List[Document]:
        """Search for documents containing specific code patterns"""
        results = []
        diagram_type = intent.get('preferred_type')
        
        if not diagram_type:
            return results
        
        # Define pattern-specific search terms that align with our keywords
        pattern_terms = {
            'flowchart': ['function', 'method', 'if', 'else', 'for', 'while', 'decision'],
            'sequence': ['function', 'method', 'call', 'invoke', 'api', 'interaction'],
            'class': ['class', 'extends', 'implements', 'interface', 'inheritance'],
            'er': ['entity', 'table', 'column', 'foreign key', 'primary key', 'relationship'],
            'component': ['component', 'service', 'module', 'controller', 'repository', 'import']
        }
        
        terms = pattern_terms.get(diagram_type, [])
        for term in terms:
            try:
                pattern_results = self.vectorstore.similarity_search(term, k=8)
                results.extend(pattern_results)
            except Exception as e:
                logger.warning(f"Pattern search failed for {term}: {str(e)}")
        
        return results
    
    def _filter_by_diagram_intent(self, documents: List[Document], intent: Dict[str, Any]) -> List[Document]:
        """Filter documents based on diagram generation intent"""
        if not intent.get('preferred_type'):
            return documents
        
        diagram_type = intent['preferred_type']
        filtered = []
        
        for doc in documents:
            content = doc.page_content.lower()
            file_type = doc.metadata.get('file_type', '')
            
            # Check if document contains relevant patterns for the diagram type
            if self._has_relevant_patterns(content, file_type, diagram_type):
                filtered.append(doc)
        
        return filtered
    
    def _has_relevant_patterns(self, content: str, file_type: str, diagram_type: str) -> bool:
        """Check if content has relevant patterns for diagram type"""
        # Simple pattern matching for quick filtering
        patterns = {
            'sequence': ['def ', 'function ', 'method ', 'call', 'invoke'],
            'flowchart': ['if ', 'else', 'for ', 'while ', 'switch ', 'case '],
            'class': ['class ', 'extends ', 'implements ', 'interface '],
            'er': ['@entity', '@table', 'create table', 'foreign key'],
            'component': ['@component', '@service', '@controller', '@repository']
        }
        
        relevant_patterns = patterns.get(diagram_type, [])
        return any(pattern in content for pattern in relevant_patterns)
    
    def _enhanced_result_processing(self, results: List[Document], query: str, intent: Dict[str, Any]) -> List[Document]:
        """
        Enhanced processing of search results
        
        Args:
            results: Raw search results
            query: Original query
            intent: Diagram generation intent
            
        Returns:
            Processed and ranked results
        """
        # Remove duplicates and rank by relevance
        unique_results = self._deduplicate_and_rank_results(results, query, intent)
        
        # Filter by code quality and relevance
        filtered_results = self._filter_code_documents(unique_results)
        
        # Apply repository filtering if specified
        repositories = self.repository_filter.extract_repositories(query)
        if repositories:
            logger.info(f"Applying repository filtering for: {repositories}")
            filtered_results = self.repository_filter.filter_by_repository(filtered_results, repositories)
            logger.info(f"After repository filtering: {len(filtered_results)} documents")
            
            # If no results after repository filtering, try to be more lenient
            if not filtered_results:
                logger.warning("No results after strict repository filtering, trying lenient filtering")
                # Try to find documents that might be from the same service family
                filtered_results = self._lenient_repository_filtering(unique_results, repositories)
        
        # Apply file type filtering based on diagram intent
        if intent.get('preferred_type'):
            preferred_file_types = self._get_preferred_file_types(intent['preferred_type'])
            filtered_results = self.repository_filter.filter_by_file_type(filtered_results, preferred_file_types)
        
        return filtered_results
    
    def _lenient_repository_filtering(self, documents: List[Document], repositories: List[str]) -> List[Document]:
        """
        More lenient repository filtering that looks for related services
        """
        filtered = []
        
        # Dynamic service family detection based on repository names
        # Instead of hardcoding specific service families, analyze repository names dynamically
        service_families = {}
        
        for repo in repositories:
            # Extract meaningful terms from repository name
            repo_terms = repo.lower().replace('-', ' ').replace('_', ' ').split()
            # Filter out common words and keep meaningful terms
            meaningful_terms = [term for term in repo_terms if len(term) > 2 and term not in ['the', 'and', 'for', 'with', 'from']]
            if meaningful_terms:
                service_families[repo] = meaningful_terms
        
        for doc in documents:
            doc_repo = doc.metadata.get('repository', '')
            if doc_repo:
                # Check if document is from a related service
                for repo, family_keywords in service_families.items():
                    if any(keyword in doc_repo.lower() for keyword in family_keywords):
                        filtered.append(doc)
                        break
        
        return filtered
    
    def _get_preferred_file_types(self, diagram_type: str) -> List[str]:
        """Get preferred file types for specific diagram types"""
        type_mapping = {
            'sequence': ['py', 'js', 'ts', 'cs'],
            'flowchart': ['py', 'js', 'ts', 'cs'],
            'class': ['py', 'js', 'ts', 'cs'],
            'er': ['cs', 'sql', 'py'],
            'component': ['cs', 'js', 'ts', 'py']
        }
        return type_mapping.get(diagram_type, [])
    
    def _extract_semantic_search_terms(self, query: str, intent: Dict[str, Any]) -> List[str]:
        """Extract semantic search terms from query with intent awareness"""
        # Remove common words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        
        # Split query and filter out stop words
        words = query.lower().split()
        meaningful_terms = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Add diagram-specific terms based on intent
        if intent.get('preferred_type'):
            diagram_terms = self.diagram_type_keywords.get(intent['preferred_type'], [])
            meaningful_terms.extend([term for term in diagram_terms if term not in meaningful_terms])
        
        # Add technical terms that are commonly useful for diagrams
        technical_terms = ['api', 'database', 'class', 'function', 'method', 'service', 'component', 'system', 'controller', 'repository', 'architecture', 'design']
        meaningful_terms.extend([term for term in technical_terms if term in query.lower() and term not in meaningful_terms])
        
        # Special handling for architecture requests
        if 'architecture' in query.lower() or 'system design' in query.lower():
            architecture_terms = ['service', 'controller', 'repository', 'component', 'module', 'interface', 'class', 'method', 'api', 'endpoint']
            meaningful_terms.extend([term for term in architecture_terms if term not in meaningful_terms])
        
        # Dynamic domain-specific term extraction based on query content
        # Instead of hardcoding specific domains, extract terms dynamically from the query
        domain_indicators = {
            'listing': ['service', 'controller', 'repository', 'model', 'entity', 'data', 'crud'],
            'order': ['service', 'controller', 'repository', 'model', 'entity', 'data', 'crud'],
            'user': ['service', 'controller', 'repository', 'model', 'entity', 'data', 'crud'],
            'product': ['service', 'controller', 'repository', 'model', 'entity', 'data', 'crud'],
            'payment': ['service', 'controller', 'repository', 'model', 'entity', 'data', 'crud'],
            'auth': ['service', 'controller', 'repository', 'model', 'entity', 'data', 'crud'],
            'notification': ['service', 'controller', 'repository', 'model', 'entity', 'data', 'crud']
        }
        
        # Add domain-specific terms based on what's actually in the query
        for domain, terms in domain_indicators.items():
            if domain in query.lower():
                meaningful_terms.extend([term for term in terms if term not in meaningful_terms])
        
        # Prioritize domain-specific terms that appear in the query
        # This makes the prioritization dynamic rather than hardcoded
        prioritized_terms = []
        for term in meaningful_terms[:]:
            # Prioritize terms that are likely to be domain-specific based on context
            if term in ['service', 'controller', 'repository', 'model', 'entity']:
                prioritized_terms.append(term)
                meaningful_terms.remove(term)
        
        # Combine prioritized terms with other meaningful terms
        final_terms = prioritized_terms + meaningful_terms
        
        return list(set(final_terms))  # Remove duplicates
    
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
        """Filter documents to keep only code-related content"""
        filtered = []
        
        for doc in documents:
            # Check if document has code-like content
            content = doc.page_content.lower()
            file_type = doc.metadata.get('file_type', '')
            
            # File type based filtering
            if file_type in ['py', 'js', 'ts', 'cs', 'java', 'cpp', 'sql']:
                filtered.append(doc)
                continue
            
            # Content pattern based filtering
            code_indicators = [
                'def ', 'function ', 'class ', 'interface ', 'public ', 'private ',
                'import ', 'from ', 'using ', 'namespace ', 'package ',
                '== ', '!= ', 'return ', 'if (', 'for (', 'while (',
                '{', '}', 'void ', 'string ', 'int ', 'bool ',
                '@', 'const ', 'var ', 'let ', 'async ', 'await '
            ]
            
            if any(indicator in content for indicator in code_indicators):
                filtered.append(doc)
                continue
            
            # Length filter - very short content is less useful
            if len(content) > 50:
                # Generic content that might still be useful
                filtered.append(doc)
        
        return filtered
