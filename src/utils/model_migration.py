"""
Model migration utilities for handling embedding model changes
"""

from typing import Dict, Any, Optional, List
import json
import os
from datetime import datetime
from ..config.settings import settings
from ..config.model_config import ModelConfiguration
from ..llm.embedding_factory import EmbeddingFactory
from ..vectorstores.chroma_store import ChromaStore
from ..utils.logging import get_logger

logger = get_logger(__name__)

class ModelMigrationManager:
    """Manager for handling model migrations and compatibility checks"""
    
    def __init__(self, migration_log_path: str = "./migration_log.json"):
        self.migration_log_path = migration_log_path
        self.migration_history = self._load_migration_history()
    
    def _load_migration_history(self) -> List[Dict[str, Any]]:
        """Load migration history from file"""
        try:
            if os.path.exists(self.migration_log_path):
                with open(self.migration_log_path, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Failed to load migration history: {str(e)}")
            return []
    
    def _save_migration_history(self):
        """Save migration history to file"""
        try:
            with open(self.migration_log_path, 'w') as f:
                json.dump(self.migration_history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save migration history: {str(e)}")
    
    def _log_migration(self, migration_info: Dict[str, Any]):
        """Log a migration event"""
        migration_info["timestamp"] = datetime.now().isoformat()
        self.migration_history.append(migration_info)
        self._save_migration_history()
    
    def check_migration_needed(self, current_model: str, new_model: str) -> bool:
        """Check if migration is needed for model change"""
        try:
            # Check if models are the same
            if current_model == new_model:
                return False
            
            # Check dimension compatibility
            return not ModelConfiguration.check_dimension_compatibility(current_model, new_model)
            
        except Exception as e:
            logger.error(f"Failed to check migration need: {str(e)}")
            return True  # Err on the side of caution
    
    def migrate_vector_store(self, 
                           vector_store: ChromaStore, 
                           new_embedding_model: str,
                           backup_data: bool = True) -> Dict[str, Any]:
        """
        Migrate vector store to new embedding model
        
        Args:
            vector_store: ChromaStore instance to migrate
            new_embedding_model: New embedding model name
            backup_data: Whether to backup existing data
            
        Returns:
            Migration result dictionary
        """
        migration_start = datetime.now()
        migration_info = {
            "old_model": getattr(settings, 'embedding_model', 'unknown'),
            "new_model": new_embedding_model,
            "status": "started",
            "start_time": migration_start.isoformat(),
            "backup_created": False,
            "documents_migrated": 0,
            "errors": []
        }
        
        try:
            # Get collection info before migration
            collection_info = vector_store.get_collection_info()
            initial_count = collection_info.get("count", 0)
            
            logger.info(f"Starting migration from {migration_info['old_model']} to {new_embedding_model}")
            logger.info(f"Collection has {initial_count} documents")
            
            # Check if migration is actually needed
            if not self.check_migration_needed(migration_info['old_model'], new_embedding_model):
                logger.info("Migration not needed - models are compatible")
                migration_info["status"] = "skipped"
                migration_info["reason"] = "Models are compatible"
                self._log_migration(migration_info)
                return migration_info
            
            # Backup existing documents if requested
            existing_docs = []
            if backup_data and initial_count > 0:
                try:
                    existing_docs = vector_store.similarity_search("", k=min(initial_count, 10000))
                    migration_info["backup_created"] = True
                    migration_info["documents_backed_up"] = len(existing_docs)
                    logger.info(f"Backed up {len(existing_docs)} documents")
                except Exception as e:
                    error_msg = f"Failed to backup documents: {str(e)}"
                    logger.warning(error_msg)
                    migration_info["errors"].append(error_msg)
            
            # Create new embedding function
            new_embedding_function = EmbeddingFactory.create_embedding(
                provider=None,  # Use auto-detection
                model=new_embedding_model
            )
            
            # Migrate the vector store
            migration_success = vector_store.migrate_to_new_embedding_model(
                new_embedding_model, 
                new_embedding_function
            )
            
            if migration_success:
                # Re-add documents if we backed them up
                if existing_docs:
                    try:
                        vector_store.add_documents(existing_docs)
                        migration_info["documents_migrated"] = len(existing_docs)
                        logger.info(f"Successfully migrated {len(existing_docs)} documents")
                    except Exception as e:
                        error_msg = f"Failed to re-add documents: {str(e)}"
                        logger.error(error_msg)
                        migration_info["errors"].append(error_msg)
                        migration_info["status"] = "partial_failure"
                
                # Update settings
                settings.embedding_model = new_embedding_model
                
                migration_info["status"] = "completed" if not migration_info["errors"] else "completed_with_warnings"
                migration_info["end_time"] = datetime.now().isoformat()
                migration_info["duration_seconds"] = (datetime.now() - migration_start).total_seconds()
                
                logger.info(f"Migration completed successfully in {migration_info['duration_seconds']:.2f} seconds")
                
            else:
                migration_info["status"] = "failed"
                migration_info["errors"].append("Vector store migration failed")
                logger.error("Migration failed")
            
        except Exception as e:
            error_msg = f"Migration failed with exception: {str(e)}"
            logger.error(error_msg)
            migration_info["status"] = "failed"
            migration_info["errors"].append(error_msg)
            migration_info["end_time"] = datetime.now().isoformat()
        
        # Log the migration
        self._log_migration(migration_info)
        return migration_info
    
    def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get migration history"""
        return self.migration_history
    
    def get_last_migration(self) -> Optional[Dict[str, Any]]:
        """Get the last migration record"""
        return self.migration_history[-1] if self.migration_history else None
    
    def validate_model_switch(self, new_model: str) -> Dict[str, Any]:
        """
        Validate if switching to a new model is safe
        
        Args:
            new_model: New embedding model name
            
        Returns:
            Validation result dictionary
        """
        current_model = getattr(settings, 'embedding_model', 'unknown')
        
        validation_result = {
            "current_model": current_model,
            "new_model": new_model,
            "is_safe": True,
            "migration_needed": False,
            "warnings": [],
            "recommendations": []
        }
        
        try:
            # Check if models are the same
            if current_model == new_model:
                validation_result["recommendations"].append("No change needed - models are identical")
                return validation_result
            
            # Check dimension compatibility
            migration_needed = self.check_migration_needed(current_model, new_model)
            validation_result["migration_needed"] = migration_needed
            
            if migration_needed:
                validation_result["warnings"].append(
                    f"Dimension mismatch detected between {current_model} and {new_model}"
                )
                validation_result["recommendations"].append(
                    "Collection will need to be recreated. Existing data will be migrated."
                )
            
            # Check if new model is available
            try:
                provider = EmbeddingFactory._detect_provider_from_model(new_model)
                embedding_config = ModelConfiguration.validate_embedding_config()
                
                if provider == "openai" and not settings.openai_api_key:
                    validation_result["is_safe"] = False
                    validation_result["warnings"].append("OpenAI API key not configured")
                elif provider == "gemini" and not settings.gemini_api_key:
                    validation_result["is_safe"] = False
                    validation_result["warnings"].append("Gemini API key not configured")
                
            except Exception as e:
                validation_result["warnings"].append(f"Could not validate model availability: {str(e)}")
            
        except Exception as e:
            validation_result["is_safe"] = False
            validation_result["warnings"].append(f"Validation failed: {str(e)}")
        
        return validation_result

# Global instance
migration_manager = ModelMigrationManager()
