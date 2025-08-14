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
                # Check if user specified repositories that don't exist
                repositories = self._extract_repositories_from_query(query)
                if repositories:
                    available_repos = self._get_available_repositories()
                    return {
                        "analysis_summary": f"The requested repositories ({', '.join(repositories)}) were not found in the knowledge base. Available repositories: {', '.join(available_repos) if available_repos else 'None indexed yet'}. Please index these repositories first or choose from the available ones.",
                        "mermaid_code": None,
                        "diagram_type": "sequence",
                        "source_documents": [],
                        "status": "error"
                    }
                else:
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
                # Check if we found documents but no code patterns
                repositories = self._extract_repositories_from_query(query)
                if repositories and code_docs:
                    # We found documents in the requested repositories but no interaction patterns
                    languages_found = set()
                    doc_types = set()
                    for doc in code_docs:
                        # Use metadata language field first, fallback to file path detection
                        lang = doc.metadata.get('language', 'unknown')
                        if lang == 'unknown':
                            lang = self._detect_language_from_path(doc.metadata.get('file_path', ''))
                        
                        file_path = doc.metadata.get('file_path', '')
                        file_type = file_path.split('.')[-1] if '.' in file_path else 'unknown'
                        languages_found.add(lang)
                        doc_types.add(file_type)
                    
                    if 'unknown' in languages_found and len(languages_found) == 1:
                        # Only found unsupported file types
                        available_repos_with_code = self._get_repositories_with_code()
                        return {
                            "analysis_summary": f"Found {len(code_docs)} documents in the requested repositories ({', '.join(repositories)}), but they contain documentation files ({', '.join(doc_types)}) rather than analyzable code. For sequence diagrams, I need actual code files (Python, JavaScript, TypeScript, C#). Repositories with code available: {', '.join(available_repos_with_code) if available_repos_with_code else 'None found'}.",
                            "mermaid_code": None,
                            "diagram_type": "sequence",
                            "source_documents": self._format_source_docs(code_docs),
                            "status": "error"
                        }
                    else:
                        # Found code but no interaction patterns
                        return {
                            "analysis_summary": f"Found {len(code_docs)} code documents in the requested repositories, but no clear interaction patterns for sequence diagram generation. The code may not contain the type of method calls and class interactions needed for sequence diagrams.",
                            "mermaid_code": None,
                            "diagram_type": "sequence",
                            "source_documents": self._format_source_docs(code_docs),
                            "status": "error"
                        }
                else:
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
        """Leverage existing ChromaStore.similarity_search() with repository filtering"""
        try:
            # Extract repository names from query if specified
            repositories = self._extract_repositories_from_query(query)
            
            if repositories:
                logger.info(f"User requested repositories: {repositories}")
                
                # First, check which repositories actually exist in the database
                available_repos = self._get_available_repositories()
                logger.info(f"Available repositories in database: {available_repos}")
                
                # Find matching repositories (case-insensitive, partial matching)
                matching_repos = []
                for requested_repo in repositories:
                    for available_repo in available_repos:
                        if self._is_repository_match(available_repo, [requested_repo]):
                            matching_repos.append(available_repo)
                            break
                
                if not matching_repos:
                    logger.warning(f"None of the requested repositories {repositories} were found in the database")
                    logger.info(f"Available repositories: {available_repos}")
                    # Return empty list so the handler can provide a helpful error message
                    return []
                
                logger.info(f"Found matching repositories: {matching_repos}")
                
                # Search with repository filter using OR logic across repositories
                all_results = []
                for repo in matching_repos:
                    try:
                        repo_results = self.vectorstore.similarity_search(
                            query=query,
                            k=20,  # Get more results per repository
                            filter={"repository": repo}  # Filter by specific repository
                        )
                        all_results.extend(repo_results)
                        logger.debug(f"Found {len(repo_results)} documents in repository: {repo}")
                    except Exception as repo_error:
                        logger.warning(f"Failed to search repository {repo}: {str(repo_error)}")
                
                results = all_results
            else:
                # No specific repositories mentioned, search all
                results = self.vectorstore.similarity_search(
                    query=query,
                    k=20  # Get more results for comprehensive analysis
                )
            
            # Filter for supported languages using existing metadata
            supported_languages = {'python', 'javascript', 'typescript', 'csharp'}
            filtered_results = []
            
            for doc in results:
                # Use metadata language field first, fallback to file path detection
                language = doc.metadata.get('language', 'unknown')
                if language == 'unknown':
                    language = self._detect_language_from_path(doc.metadata.get('file_path', ''))
                
                if language in supported_languages:
                    # Additional filtering to ensure we're getting relevant repositories
                    if repositories:
                        doc_repository = doc.metadata.get('repository', '')
                        if self._is_repository_match(doc_repository, repositories):
                            filtered_results.append(doc)
                    else:
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
    
    def _extract_repositories_from_query(self, query: str) -> List[str]:
        """Extract repository names from user query"""
        import re
        
        repositories = []
        
        # Pattern 1: Look for "for these repositories:" followed by comma-separated list
        repo_pattern1 = r'for these repositories:\s*([^?.\n]*)'
        match1 = re.search(repo_pattern1, query, re.IGNORECASE)
        if match1:
            repo_list = match1.group(1).strip()
            # Split by commas and clean up
            repos = [repo.strip() for repo in repo_list.split(',')]
            repositories.extend(repos)
        
        # Pattern 2: Look for "repositories: repo1, repo2, repo3"
        repo_pattern2 = r'repositories:\s*([^?.\n]*)'
        match2 = re.search(repo_pattern2, query, re.IGNORECASE)
        if match2:
            repo_list = match2.group(1).strip()
            repos = [repo.strip() for repo in repo_list.split(',')]
            repositories.extend(repos)
        
        # Pattern 3: Look for "in repo1, repo2, and repo3"
        repo_pattern3 = r'in\s+((?:\w+[-\w]*,?\s*(?:and\s+)?)+)'
        match3 = re.search(repo_pattern3, query, re.IGNORECASE)
        if match3:
            repo_list = match3.group(1).strip()
            # Split by commas and "and"
            repos = re.split(r',\s*(?:and\s+)?|\s+and\s+', repo_list)
            repos = [repo.strip() for repo in repos if repo.strip()]
            repositories.extend(repos)
        
        # Remove duplicates and clean up
        unique_repos = []
        for repo in repositories:
            repo = repo.strip()
            if repo and repo not in unique_repos:
                unique_repos.append(repo)
        
        logger.debug(f"Extracted repositories from query: {unique_repos}")
        return unique_repos
    
    def _extract_repo_name_from_url_or_name(self, repo_identifier: str) -> str:
        """Extract repository name from URL or return as is if already a name"""
        import re
        
        # If it's a GitHub URL, extract the repo name
        github_pattern = r'github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?/?$'
        match = re.search(github_pattern, repo_identifier)
        if match:
            return match.group(2)  # Return repository name
        
        # If it contains slashes, take the last part
        if '/' in repo_identifier:
            return repo_identifier.split('/')[-1]
        
        # Otherwise return as is
        return repo_identifier
    
    def _is_repository_match(self, doc_repository: str, target_repositories: List[str]) -> bool:
        """Check if document repository matches any of the target repositories"""
        if not doc_repository or not target_repositories:
            return False
        
        # Extract repository name from document metadata
        doc_repo_name = self._extract_repo_name_from_url_or_name(doc_repository)
        
        # Check against all target repositories
        for target_repo in target_repositories:
            target_repo_name = self._extract_repo_name_from_url_or_name(target_repo)
            
            # Case-insensitive comparison
            if doc_repo_name.lower() == target_repo_name.lower():
                return True
            
            # Also check if target repo is contained in doc repo (for partial matches)
            if target_repo_name.lower() in doc_repo_name.lower():
                return True
        
        return False
    
    def _get_available_repositories(self) -> List[str]:
        """Get list of all available repositories in the vector database"""
        try:
            # Get a sample of documents to extract repository information
            sample_docs = self.vectorstore.similarity_search("", k=100)  # Get many documents
            repositories = set()
            
            for doc in sample_docs:
                repo = doc.metadata.get('repository')
                if repo:
                    repositories.add(repo)
            
            return list(repositories)
            
        except Exception as e:
            logger.error(f"Failed to get available repositories: {str(e)}")
            # Fallback: try to query the collection directly if possible
            try:
                if hasattr(self.vectorstore, 'vector_store') and hasattr(self.vectorstore.vector_store, '_collection'):
                    collection = self.vectorstore.vector_store._collection
                    # Get metadata from a larger sample
                    results = collection.get(limit=500, include=['metadatas'])
                    repositories = set()
                    for metadata in results['metadatas']:
                        repo = metadata.get('repository')
                        if repo:
                            repositories.add(repo)
                    return list(repositories)
            except Exception as fallback_error:
                logger.error(f"Fallback repository query also failed: {str(fallback_error)}")
            
            return []
    
    def _get_repositories_with_code(self) -> List[str]:
        """Get list of repositories that contain actual code files"""
        try:
            available_repos = self._get_available_repositories()
            repos_with_code = []
            
            supported_languages = {'python', 'javascript', 'typescript', 'csharp'}
            
            for repo in available_repos:
                # Search for code-like terms in this repository
                docs = self.vectorstore.similarity_search("function class method", k=5, filter={'repository': repo})
                
                # Check if any documents are actual code files
                code_docs = []
                for doc in docs:
                    # Use metadata language field first, fallback to file path detection
                    lang = doc.metadata.get('language', 'unknown')
                    if lang == 'unknown':
                        lang = self._detect_language_from_path(doc.metadata.get('file_path', ''))
                    
                    if lang in supported_languages:
                        code_docs.append(doc)
                
                if code_docs:
                    repos_with_code.append(repo)
            
            return repos_with_code
            
        except Exception as e:
            logger.error(f"Failed to get repositories with code: {str(e)}")
            return []