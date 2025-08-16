import os
import tempfile
import shutil
from typing import List, Optional
from pathlib import Path
import git
from langchain.docstore.document import Document

from src.config import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)

class GitHubLoader:
    """GitHub repository loader"""
    
    def __init__(self, github_token: str = None):
        self.github_token = github_token
        self.supported_extensions = settings.settings.github_supported_file_extensions
    
    def load_repository(self, repo_url: str, branch: str = "main", file_patterns: Optional[List[str]] = None) -> List[Document]:
        """Load documents from GitHub repository"""
        logger.info(f"Loading repository: {repo_url}")
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Clone repository
            repo_name = repo_url.split('/')[-1].replace('.git', '')
            clone_path = os.path.join(temp_dir, repo_name)
            
            # Prepare URL with token if available
            if self.github_token and not repo_url.startswith('https://'):
                clone_url = f"https://{self.github_token}@github.com/{repo_url.split('github.com/')[-1]}"
            else:
                clone_url = repo_url
            
            logger.info(f"Cloning repository to: {clone_path}")
            repo = git.Repo.clone_from(clone_url, clone_path)
            
            # Checkout specific branch if specified
            if branch != "main":
                try:
                    repo.git.checkout(branch)
                except Exception as e:
                    logger.warning(f"Could not checkout branch {branch}, using default: {str(e)}")
            
            # Load documents
            documents = self._load_files_from_directory(clone_path, repo_url, file_patterns)
            
            logger.info(f"Loaded {len(documents)} documents from repository")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to load repository {repo_url}: {str(e)}")
            raise Exception(f"Failed to load repository: {str(e)}")
        
        finally:
            # Clean up temporary directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def _load_files_from_directory(self, directory_path: str, repo_url: str, file_patterns: Optional[List[str]] = None) -> List[Document]:
        """Load files from directory"""
        import fnmatch
        
        documents = []
        
        # If file_patterns provided, use them; otherwise use supported extensions
        if file_patterns:
            # For file_patterns, we'll use fnmatch directly, no need to convert to extensions
            pattern_extensions = None
        else:
            pattern_extensions = self.supported_extensions
        
        total_files_found = 0
        matched_files = 0
        
        for root, dirs, files in os.walk(directory_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {
                'node_modules', '__pycache__', 'venv', 'env', 'build', 'dist', 'target'
            }]
            
            for file in files:
                total_files_found += 1
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, directory_path)
                
                # Check if file matches patterns
                file_ext = Path(file).suffix.lower()
                matches_pattern = False
                
                if file_patterns:
                    # Check against provided patterns
                    for pattern in file_patterns:
                        if fnmatch.fnmatch(file, pattern) or fnmatch.fnmatch(relative_path, pattern):
                            matches_pattern = True
                            break
                else:
                    # Check against supported extensions
                    matches_pattern = file_ext in self.supported_extensions
                
                if not matches_pattern:
                    continue
                
                matched_files += 1
                
                # Skip files that are too large (> 1MB)
                if os.path.getsize(file_path) > 1024 * 1024:
                    logger.warning(f"Skipping large file: {relative_path}")
                    continue
                
                try:
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Create document with metadata
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": "github",
                            "repository": repo_url,
                            "file_path": relative_path,
                            "file_name": file,
                            "file_type": file_ext,
                            "file_size": os.path.getsize(file_path)
                        }
                    )
                    documents.append(doc)
                    
                except Exception as e:
                    logger.warning(f"Could not read file {relative_path}: {str(e)}")
                    continue
        
        logger.info(f"File scanning complete: {total_files_found} total files found, {matched_files} matched patterns, {len(documents)} successfully loaded")
        return documents
