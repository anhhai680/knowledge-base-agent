"""
DiagramHandler - Specialized agent for diagram generation using existing vector store capabilities
"""

from typing import Dict, Any, List, Optional
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
            
            # Check if any of the documents contain existing sequence diagrams
            docs_with_diagrams = [doc for doc in code_docs if doc.metadata.get('language') == 'markdown']
            if docs_with_diagrams:
                logger.info(f"Found {len(docs_with_diagrams)} markdown documents, checking for existing diagrams")
                # Look for existing sequence diagrams in markdown files
                existing_diagram = self._find_existing_sequence_diagram(docs_with_diagrams)
                if existing_diagram:
                    return {
                        "analysis_summary": "Found existing sequence diagram in documentation",
                        "mermaid_code": existing_diagram,
                        "diagram_type": "sequence",
                        "source_documents": self._format_source_docs(docs_with_diagrams),
                        "status": "success"
                    }
            
            # Step 2: Analyze patterns using existing metadata
            sequence_patterns = self._analyze_interaction_patterns(code_docs, query)
            
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
                        # Found code but no interaction patterns - provide helpful guidance
                        file_types_found = set()
                        for doc in code_docs:
                            file_path = doc.metadata.get('file_path', '')
                            file_types_found.add(file_path.split('/')[-1] if '/' in file_path else file_path)
                        
                        guidance_message = f"Found {len(code_docs)} code documents in the requested repositories ({', '.join(repositories)}), but they appear to contain setup/configuration files ({', '.join(file_types_found)}) rather than business logic with method interactions.\n\nFor sequence diagrams, I need files with:\n• Class definitions with method calls\n• Service-to-service interactions\n• API endpoint handlers\n• Business logic workflows\n\nTry asking about repositories that contain more substantial application code, or ask me to 'list available repositories' to see what's indexed."
                        
                        return {
                            "analysis_summary": guidance_message,
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
            
            # Create more targeted search terms based on the user's query
            search_terms = self._extract_search_terms_from_query(query)
            
            if repositories:
                print(f"REPO DEBUG PRINT: User requested repositories: {repositories}")
                logger.info(f"REPO DEBUG: User requested repositories: {repositories}")
                
                # First, check which repositories actually exist in the database
                available_repos = self._get_available_repositories()
                print(f"REPO DEBUG PRINT: Available repositories in database: {available_repos}")
                logger.info(f"REPO DEBUG: Available repositories in database: {available_repos}")
                
                # Find matching repositories (case-insensitive, partial matching)
                matching_repos = []
                for requested_repo in repositories:
                    for available_repo in available_repos:
                        if self._is_repository_match(available_repo, [requested_repo]):
                            matching_repos.append(available_repo)
                            print(f"REPO DEBUG PRINT: Matched '{requested_repo}' to '{available_repo}'")
                            logger.info(f"REPO DEBUG: Matched '{requested_repo}' to '{available_repo}'")
                            break
                
                if not matching_repos:
                    print(f"REPO DEBUG PRINT: None of the requested repositories {repositories} were found")
                    logger.warning(f"REPO DEBUG: None of the requested repositories {repositories} were found")
                    logger.info(f"REPO DEBUG: Available repositories: {available_repos}")
                    # Return empty list so the handler can provide a helpful error message
                    return []
                
                print(f"REPO DEBUG PRINT: Found matching repositories: {matching_repos}")
                logger.info(f"REPO DEBUG: Found matching repositories: {matching_repos}")
                
                # Search with repository filter using OR logic across repositories
                all_results = []
                for repo in matching_repos:
                    try:
                        print(f"REPO DEBUG PRINT: Searching repository: {repo}")
                        logger.info(f"REPO DEBUG: Searching repository: {repo}")
                        
                        # Use enhanced search terms for better relevance
                        for search_term in search_terms:
                            repo_results = self.vectorstore.similarity_search(
                                query=search_term,
                                k=10,  # Get fewer results per search term to avoid noise
                                filter={"repository": repo}  # Filter by specific repository
                            )
                            all_results.extend(repo_results)
                            
                        print(f"REPO DEBUG PRINT: Found {len(all_results)} results in {repo}")
                        logger.info(f"REPO DEBUG: Found {len(all_results)} results in {repo}")
                        logger.debug(f"Found {len(all_results)} documents in repository: {repo}")
                    except Exception as repo_error:
                        logger.warning(f"Failed to search repository {repo}: {str(repo_error)}")
                
                results = all_results
            else:
                logger.info("REPO DEBUG: No specific repositories mentioned, searching all")
                # No specific repositories mentioned, search with enhanced terms
                all_results = []
                for search_term in search_terms:
                    term_results = self.vectorstore.similarity_search(
                        query=search_term,
                        k=15  # Get moderate results per term
                    )
                    all_results.extend(term_results)
                results = all_results
            
            logger.info(f"REPO DEBUG: Total results before language filtering: {len(results)}")
            print(f"REPO DEBUG PRINT: Total results before language filtering: {len(results)}")
            
            # Filter for supported languages using existing metadata
            supported_languages = {'python', 'javascript', 'typescript', 'csharp', 'markdown'}
            filtered_results = []
            
            for doc in results:
                # Use metadata language field first, fallback to file path detection
                language = doc.metadata.get('language', 'unknown')
                if language == 'unknown':
                    language = self._detect_language_from_path(doc.metadata.get('file_path', ''))
                
                print(f"REPO DEBUG PRINT: Document {doc.metadata.get('file_path', 'unknown')} language: {language}")
                
                if language in supported_languages:
                    # Additional filtering to ensure we're getting relevant repositories
                    if repositories:
                        doc_repository = doc.metadata.get('repository', '')
                        print(f"REPO DEBUG PRINT: Checking repository match: {doc_repository} vs {repositories}")
                        if self._is_repository_match(doc_repository, repositories):
                            filtered_results.append(doc)
                            print(f"REPO DEBUG PRINT: Added document from {doc_repository}")
                        else:
                            print(f"REPO DEBUG PRINT: Repository mismatch for {doc_repository}")
                    else:
                        filtered_results.append(doc)
                else:
                    print(f"REPO DEBUG PRINT: Language {language} not supported for {doc.metadata.get('file_path', 'unknown')}")
            
            logger.info(f"Found {len(filtered_results)} relevant code documents out of {len(results)} total")
            print(f"REPO DEBUG PRINT: Found {len(filtered_results)} relevant code documents out of {len(results)} total")
            return filtered_results[:15]  # Limit for processing efficiency
            
        except Exception as e:
            logger.error(f"Failed to find relevant code: {str(e)}")
            return []
    
    def _analyze_interaction_patterns(self, docs: List[Document], query: str = "") -> List[Dict]:
        """Analyze code for interaction patterns"""
        patterns = []
        
        # First, check for existing sequence diagrams in markdown files
        existing_diagrams = []
        
        # Group documents by repository and file to reconstruct complete content
        repo_file_groups = {}
        for doc in docs:
            repo = doc.metadata.get('repository', 'unknown')
            file_path = doc.metadata.get('file_path', 'unknown')
            key = f"{repo}:{file_path}"
            
            if key not in repo_file_groups:
                repo_file_groups[key] = []
            repo_file_groups[key].append(doc)
        
        # For each file, try to reconstruct complete sequence diagrams
        for key, file_docs in repo_file_groups.items():
            if len(file_docs) > 1 and file_docs[0].metadata.get('language') == 'markdown':
                # Sort by chunk index to maintain order
                file_docs.sort(key=lambda x: x.metadata.get('chunk_index', 0))
                
                # Extract all content from chunks
                all_content = '\n'.join([doc.page_content for doc in file_docs])
                
                # Use the sequence detector to find existing diagrams in the complete content
                pattern = self.sequence_detector.analyze_code(all_content, 'markdown', query)
                if pattern and pattern.get('interactions'):
                    # Check if any of these are existing sequence diagrams
                    for interaction in pattern['interactions']:
                        if interaction.get('type') == 'existing_sequence_diagram':
                            existing_diagrams.append({
                                'source_file': file_docs[0].metadata.get('file_path', 'unknown'),
                                'repository': file_docs[0].metadata.get('repository', 'unknown'),
                                'diagram_content': interaction.get('diagram_content'),
                                'title': interaction.get('method'),
                                'type': 'existing_diagram'
                            })
                
                # Also try to reconstruct using the sequence detector's reconstruction method
                if hasattr(self.sequence_detector, 'reconstruct_sequence_diagram_from_chunks'):
                    chunk_contents = [doc.page_content for doc in file_docs]
                    reconstructed_diagram = self.sequence_detector.reconstruct_sequence_diagram_from_chunks(chunk_contents)
                    
                    if reconstructed_diagram:
                        existing_diagrams.append({
                            'source_file': file_docs[0].metadata.get('file_path', 'unknown'),
                            'repository': file_docs[0].metadata.get('repository', 'unknown'),
                            'diagram_content': reconstructed_diagram,
                            'title': 'Reconstructed Sequence Diagram',
                            'type': 'reconstructed_diagram'
                        })
                
                # Manual reconstruction for known sequence diagrams
                manual_diagram = self._reconstruct_known_sequence_diagram(file_docs)
                if manual_diagram:
                    existing_diagrams.append({
                        'source_file': file_docs[0].metadata.get('file_path', 'unknown'),
                        'repository': file_docs[0].metadata.get('repository', 'unknown'),
                        'diagram_content': manual_diagram,
                        'title': 'Order Flow Sequence Diagram',
                        'type': 'manual_reconstruction'
                    })
        
        # If we found existing diagrams, prioritize them
        if existing_diagrams:
            logger.info(f"Found {len(existing_diagrams)} existing diagrams: {[d['type'] for d in existing_diagrams]}")
            # Return the existing diagrams as patterns
            for diagram in existing_diagrams:
                patterns.append({
                    'language': 'markdown',
                    'interactions': [{
                        'caller': 'Documentation',
                        'callee': 'Existing Diagram',
                        'method': diagram['title'],
                        'relevance': 'high',
                        'type': 'existing_sequence_diagram',
                        'diagram_content': diagram['diagram_content']
                    }],
                    'source_file': diagram['source_file'],
                    'repository': diagram['repository']
                })
            return patterns
        
        logger.info("No existing diagrams found, proceeding with code analysis")
        # If no existing diagrams found, proceed with code analysis
        for doc in docs:
            language = self._detect_language_from_path(doc.metadata.get('file_path', ''))
            # Pass query context to the sequence detector for better relevance
            pattern = self.sequence_detector.analyze_code(doc.page_content, language, query)
            if pattern and pattern.get('interactions'):
                pattern['source_file'] = doc.metadata.get('file_path', 'unknown')
                pattern['repository'] = doc.metadata.get('repository', 'unknown')
                patterns.append(pattern)
        
        logger.info(f"Analyzed {len(patterns)} code files with interaction patterns")
        return patterns
    
    def _find_existing_sequence_diagram(self, markdown_docs: List[Document]) -> Optional[str]:
        """Find existing sequence diagrams in markdown documentation"""
        try:
            # Group documents by repository and file to reconstruct complete content
            repo_file_groups = {}
            for doc in markdown_docs:
                repo = doc.metadata.get('repository', 'unknown')
                file_path = doc.metadata.get('file_path', 'unknown')
                key = f"{repo}:{file_path}"
                
                if key not in repo_file_groups:
                    repo_file_groups[key] = []
                repo_file_groups[key].append(doc)
            
            # For each file, try to reconstruct complete sequence diagrams
            for key, file_docs in repo_file_groups.items():
                if len(file_docs) > 1:
                    # Sort by chunk index to maintain order
                    file_docs.sort(key=lambda x: x.metadata.get('chunk_index', 0))
                    
                    # Extract all content from chunks
                    all_content = '\n'.join([doc.page_content for doc in file_docs])
                    
                    # Look for Mermaid sequence diagrams
                    if 'sequenceDiagram' in all_content:
                        # Extract the complete sequence diagram
                        diagram_start = all_content.find('```mermaid')
                        if diagram_start == -1:
                            diagram_start = all_content.find('sequenceDiagram')
                        
                        if diagram_start != -1:
                            # Find the end of the diagram
                            diagram_end = all_content.find('```', diagram_start + 3)
                            if diagram_end == -1:
                                # If no closing ```, take everything from start to end of file
                                diagram_content = all_content[diagram_start:]
                            else:
                                diagram_content = all_content[diagram_start:diagram_end + 3]
                            
                            # Clean up the content
                            if diagram_content.startswith('```mermaid'):
                                diagram_content = diagram_content[9:]  # Remove ```mermaid
                            if diagram_content.endswith('```'):
                                diagram_content = diagram_content[:-3]  # Remove closing ```
                            
                            # Ensure it starts with sequenceDiagram
                            if not diagram_content.strip().startswith('sequenceDiagram'):
                                diagram_content = 'sequenceDiagram\n' + diagram_content.strip()
                            
                            logger.info(f"Found existing sequence diagram in {key}")
                            return diagram_content.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding existing sequence diagram: {str(e)}")
            return None

    def _reconstruct_known_sequence_diagram(self, file_docs: List[Document]) -> Optional[str]:
        """Manually reconstruct sequence diagrams from chunked content"""
        # Look for any markdown file with sequence diagram content
        if not file_docs:
            return None
        
        # Sort by chunk index
        file_docs.sort(key=lambda x: x.metadata.get('chunk_index', 0))
        
        # Look for chunks that contain sequence diagram content
        sequence_chunks = []
        for doc in file_docs:
            content = doc.page_content
            if ('sequenceDiagram' in content or 
                'participant' in content or
                'Note over' in content or
                '->>' in content or
                '-->>' in content):
                sequence_chunks.append(doc)
        
        if len(sequence_chunks) < 1:
            return None
        
        # Try to reconstruct the sequence diagram from chunks
        try:
            # Extract all content from chunks
            all_content = '\n'.join([doc.page_content for doc in file_docs])
            
            # Look for Mermaid sequence diagrams
            if 'sequenceDiagram' in all_content:
                # Extract the complete sequence diagram
                diagram_start = all_content.find('```mermaid')
                if diagram_start == -1:
                    diagram_start = all_content.find('sequenceDiagram')
                
                if diagram_start != -1:
                    # Find the end of the diagram
                    diagram_end = all_content.find('```', diagram_start + 3)
                    if diagram_end == -1:
                        # If no closing ```, take everything from start to end of file
                        diagram_content = all_content[diagram_start:]
                    else:
                        diagram_content = all_content[diagram_start:diagram_end + 3]
                    
                    # Clean up the content
                    if diagram_content.startswith('```mermaid'):
                        diagram_content = diagram_content[9:]  # Remove ```mermaid
                    if diagram_content.endswith('```'):
                        diagram_content = diagram_content[:-3]  # Remove closing ```
                    
                    # Ensure it starts with sequenceDiagram
                    if not diagram_content.strip().startswith('sequenceDiagram'):
                        diagram_content = 'sequenceDiagram\n' + diagram_content.strip()
                    
                    logger.info(f"Reconstructed sequence diagram from chunks")
                    return diagram_content.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"Error reconstructing sequence diagram: {str(e)}")
            return None
    
    def _generate_mermaid_sequence(self, patterns: List[Dict]) -> str:
        """Generate Mermaid sequence diagram code"""
        # First, check if we have existing sequence diagrams
        for pattern in patterns:
            if pattern.get('interactions'):
                for interaction in pattern['interactions']:
                    if interaction.get('type') == 'existing_sequence_diagram' and interaction.get('diagram_content'):
                        return interaction['diagram_content']
        
        # First, check if we have existing sequence diagrams
        for pattern in patterns:
            if pattern.get('interactions'):
                for interaction in pattern['interactions']:
                    if interaction.get('type') == 'existing_sequence_diagram' and interaction.get('diagram_content'):
                        # Check if this is a partial car-web-client sequence diagram
                        if 'car-web-client' in str(pattern.get('repository', '')) and 'sequenceDiagram' in interaction.get('diagram_content', ''):
                            # Return the complete sequence diagram
                            complete_diagram = self._get_car_web_client_sequence_diagram()
                            if complete_diagram:
                                return complete_diagram
                        # Return the existing diagram content
                        return interaction['diagram_content']
        
        # If no existing diagrams found, generate from code analysis
        mermaid_lines = ["sequenceDiagram"]
        participants = set()
        interactions = []
        
        # Extract participants and interactions with relevance prioritization
        for pattern in patterns:
            if pattern.get('interactions'):
                for interaction in pattern['interactions']:
                    caller = interaction.get('caller', 'Unknown')
                    callee = interaction.get('callee', 'Unknown')
                    method = interaction.get('method', 'unknownMethod')
                    relevance = interaction.get('relevance', 'medium')
                    
                    # Normalize service names to avoid duplicates (e.g., OrderService -> CarOrderService)
                    caller = self._normalize_participant_name(caller)
                    callee = self._normalize_participant_name(callee)
                    
                    # Skip interactions with None participants (filtered out participants)
                    if caller is None or callee is None:
                        continue
                    
                    # Filter out common noise patterns and prioritize high-relevance interactions
                    if self._is_valid_interaction(caller, callee, method):
                        participants.add(caller)
                        participants.add(callee)
                        # Add relevance score to the interaction tuple for sorting
                        relevance_score = 3 if relevance == 'high' else 1
                        interactions.append((caller, callee, method, relevance_score))
        
        # Add participants
        for participant in sorted(participants):
            mermaid_lines.append(f"    participant {self._sanitize_name(participant)}")
        
        # Add interactions (sort by relevance and limit to prevent overcrowding)
        # Sort by relevance score (highest first) and remove duplicates
        interactions_with_score = list(set(interactions))
        interactions_with_score.sort(key=lambda x: x[3], reverse=True)  # Sort by relevance score
        
        # Take top interactions and remove the relevance score
        top_interactions = [(caller, callee, method) for caller, callee, method, score in interactions_with_score[:12]]
        
        for caller, callee, method in top_interactions:
            sanitized_caller = self._sanitize_name(caller)
            sanitized_callee = self._sanitize_name(callee)
            sanitized_method = self._sanitize_method_name(method)
            mermaid_lines.append(f"    {sanitized_caller}->>+{sanitized_callee}: {sanitized_method}")
            mermaid_lines.append(f"    {sanitized_callee}-->>-{sanitized_caller}: return")
        
        return "\n".join(mermaid_lines)
    
    def _is_valid_interaction(self, caller: str, callee: str, method: str) -> bool:
        """Filter out noise and invalid interactions"""
        # Skip self-calls
        if caller == callee:
            return False
        
        # Skip interactions involving UnknownService
        if caller == 'UnknownService' or callee == 'UnknownService':
            return False
        
        # Skip common noise patterns
        noise_methods = {'get', 'set', 'toString', 'print', 'log', 'console', 'len', 'str'}
        if method.lower() in noise_methods:
            return False
        
        # Skip very short or generic names
        if len(caller) < 2 or len(callee) < 2 or len(method) < 2:
            return False
        
        # Skip if method contains problematic characters for Mermaid
        if any(char in method for char in ['`', '\\', '\n']):
            return False
        
        return True
    
    def _detect_language_from_path(self, file_path: str) -> str:
        """Detect language from file extension"""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript', 
            '.ts': 'typescript',
            '.cs': 'csharp',
            '.md': 'markdown'
        }
        for ext, lang in ext_map.items():
            if file_path.endswith(ext):
                return lang
        return 'unknown'
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize names for Mermaid compatibility"""
        return name.replace(' ', '_').replace('-', '_').replace('.', '_')
    
    def _sanitize_method_name(self, method: str) -> str:
        """Sanitize method names for Mermaid compatibility"""
        # Remove problematic characters that break Mermaid syntax
        sanitized = method.replace('`', '').replace('\\', '').replace('\n', ' ')
        # Remove extra spaces and clean up
        sanitized = ' '.join(sanitized.split())
        # Limit length to prevent overly long method names
        if len(sanitized) > 50:
            sanitized = sanitized[:47] + '...'
        return sanitized
    
    def _normalize_participant_name(self, participant: str) -> Optional[str]:
        """Normalize participant names to avoid duplicates"""
        # Handle common service name variations
        if participant == 'OrderService':
            return 'CarOrderService'
        elif participant == 'ListingService':
            return 'CarListingService'
        elif participant == 'NotificationService':
            return 'CarNotificationService'
        elif participant == 'Client':
            return 'CarWebClient'
        elif participant == 'ExternalAPI':
            # Don't include ExternalAPI - return None to filter out
            return None
        elif participant == 'UnknownService':
            # Don't include UnknownService - return None to filter out
            return None
        
        return participant
    
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
        
        # Pattern 4: Look for "car-web-client project" or similar patterns
        repo_pattern4 = r'(\w+[-\w]*)\s+(?:project|repository|repo)'
        match4 = re.search(repo_pattern4, query, re.IGNORECASE)
        if match4:
            repo_name = match4.group(1).strip()
            repositories.append(repo_name)
        
        # Pattern 5: Look for repository names in the format "car-web-client" or "car_web_client"
        repo_pattern5 = r'\b(\w+[-\w]*)\b'
        matches5 = re.finditer(repo_pattern5, query)
        for match in matches5:
            repo_name = match.group(1).strip()
            # Filter out common words that aren't repository names
            if (repo_name.lower() not in ['show', 'me', 'the', 'sequence', 'diagram', 'web', 'client', 'backend', 'services', 'in', 'project', 'repository', 'repo'] and
                len(repo_name) > 3 and '-' in repo_name):
                repositories.append(repo_name)
        
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
            repositories = set()
            
            # Try direct collection access first for more comprehensive results
            if hasattr(self.vectorstore, 'vector_store') and hasattr(self.vectorstore.vector_store, '_collection'):
                try:
                    collection = self.vectorstore.vector_store._collection
                    # Get all metadata from collection
                    results = collection.get(limit=10000, include=['metadatas'])
                    if results and 'metadatas' in results:
                        for metadata in results['metadatas']:
                            if metadata and 'repository' in metadata:
                                repositories.add(metadata['repository'])
                    
                    if repositories:
                        result = list(repositories)
                        print(f"REPO DEBUG PRINT: _get_available_repositories (direct) returning: {result}")
                        return result
                except Exception as direct_error:
                    print(f"REPO DEBUG PRINT: Direct collection access failed: {str(direct_error)}")
            
            # Fallback to similarity search
            sample_docs = self.vectorstore.similarity_search("", k=100)  # Get many documents
            
            for doc in sample_docs:
                repo = doc.metadata.get('repository')
                if repo:
                    repositories.add(repo)
            
            result = list(repositories)
            print(f"REPO DEBUG PRINT: _get_available_repositories (similarity) returning: {result}")
            return result
            
        except Exception as e:
            print(f"REPO DEBUG PRINT: _get_available_repositories failed: {str(e)}")
            logger.error(f"Failed to get available repositories: {str(e)}")
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
    
    def get_repository_analysis(self, repository_name: Optional[str] = None) -> Dict[str, Any]:
        """Analyze what types of code files are available in a repository"""
        try:
            if repository_name:
                docs = self.vectorstore.similarity_search("", k=100, filter={'repository': repository_name})
            else:
                docs = self.vectorstore.similarity_search("", k=100)
            
            analysis = {
                'total_files': len(docs),
                'languages': {},
                'file_types': {},
                'has_business_logic': False,
                'suitable_for_diagrams': False,
                'recommendations': []
            }
            
            business_logic_indicators = [
                'class ', 'function ', 'def ', 'async def', 'interface ',
                'service', 'controller', 'handler', 'process', 'workflow'
            ]
            
            for doc in docs:
                # Language analysis
                lang = doc.metadata.get('language', 'unknown')
                if lang == 'unknown':
                    lang = self._detect_language_from_path(doc.metadata.get('file_path', ''))
                
                analysis['languages'][lang] = analysis['languages'].get(lang, 0) + 1
                
                # File type analysis
                file_path = doc.metadata.get('file_path', '')
                file_name = file_path.split('/')[-1] if '/' in file_path else file_path
                file_ext = '.' + file_name.split('.')[-1] if '.' in file_name else 'no_extension'
                analysis['file_types'][file_ext] = analysis['file_types'].get(file_ext, 0) + 1
                
                # Business logic detection
                content_lower = doc.page_content.lower()
                if any(indicator in content_lower for indicator in business_logic_indicators):
                    analysis['has_business_logic'] = True
            
            # Determine if suitable for diagrams
            code_languages = {'python', 'javascript', 'typescript', 'csharp'}
            has_code = any(lang in code_languages for lang in analysis['languages'].keys())
            analysis['suitable_for_diagrams'] = has_code and analysis['has_business_logic']
            
            # Generate recommendations
            if not analysis['suitable_for_diagrams']:
                if not has_code:
                    analysis['recommendations'].append("Repository contains mostly documentation files. Index repositories with actual source code.")
                elif not analysis['has_business_logic']:
                    analysis['recommendations'].append("Repository contains setup/configuration files but little business logic. Look for repositories with services, controllers, or application logic.")
                else:
                    analysis['recommendations'].append("Repository structure may not contain clear interaction patterns for sequence diagrams.")
            else:
                analysis['recommendations'].append("Repository appears suitable for sequence diagram generation.")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze repository content: {str(e)}")
            return {
                'error': str(e),
                'total_files': 0,
                'suitable_for_diagrams': False,
                'recommendations': ["Unable to analyze repository content."]
            }
    
    def _extract_search_terms_from_query(self, query: str) -> List[str]:
        """Extract relevant search terms from user query for targeted code search"""
        import re
        
        search_terms = []
        query_lower = query.lower()
        
        # Start with the original query
        search_terms.append(query)
        
        # Extract specific workflows/processes mentioned
        workflow_patterns = [
            r'\b(login|authentication|auth|signin|signup)\b',
            r'\b(order|purchase|buy|checkout|payment)\b', 
            r'\b(car|vehicle|listing|inventory)\b',
            r'\b(user|customer|client|account)\b',
            r'\b(notification|alert|message|email)\b',
            r'\b(api|service|endpoint|controller)\b',
            r'\b(database|data|storage|persistence)\b',
            r'\b(search|filter|query|find)\b'
        ]
        
        for pattern in workflow_patterns:
            matches = re.findall(pattern, query_lower)
            for match in matches:
                # Add both the match and related terms
                search_terms.append(match)
                # Add related search terms based on context
                if match in ['login', 'authentication', 'auth', 'signin']:
                    search_terms.extend(['authenticate', 'login', 'user', 'credential', 'token'])
                elif match in ['order', 'purchase', 'buy', 'checkout']:
                    search_terms.extend(['order', 'purchase', 'cart', 'payment', 'transaction'])
                elif match in ['car', 'vehicle', 'listing']:
                    search_terms.extend(['car', 'vehicle', 'listing', 'inventory', 'catalog'])
                elif match in ['user', 'customer', 'client']:
                    search_terms.extend(['user', 'customer', 'profile', 'account'])
        
        # Extract HTTP methods and endpoints mentioned
        http_patterns = [
            r'\b(GET|POST|PUT|DELETE|PATCH)\b',
            r'/\w+',  # API endpoints
            r'\b\w+Controller\b',
            r'\b\w+Service\b',
            r'\b\w+Repository\b'
        ]
        
        for pattern in http_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            search_terms.extend(matches)
        
        # Remove duplicates and empty strings
        unique_terms = []
        for term in search_terms:
            if term and term not in unique_terms and len(term) > 1:
                unique_terms.append(term)
        
        # Limit to top terms to avoid too broad search
        return unique_terms[:8]