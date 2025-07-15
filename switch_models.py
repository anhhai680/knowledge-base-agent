#!/usr/bin/env python3
"""
Model switching utility with automatic migration support
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from typing import Dict, Any
from src.config.settings import settings
from src.config.model_config import ModelConfiguration
from src.llm.embedding_factory import EmbeddingFactory
from src.vectorstores.chroma_store import ChromaStore
from src.utils.model_migration import migration_manager
from src.utils.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)

def print_current_config():
    """Print current configuration"""
    print("\n🔧 Current Configuration:")
    print(f"   LLM Provider: {settings.llm_provider}")
    print(f"   LLM Model: {settings.llm_model}")
    print(f"   Embedding Model: {settings.embedding_model}")
    
    # Get configuration summary
    config_summary = ModelConfiguration.get_configuration_summary()
    print(f"   Overall Status: {config_summary['overall_status']}")
    
    if config_summary['embedding']['dimension']:
        print(f"   Embedding Dimension: {config_summary['embedding']['dimension']}")

def validate_model_switch(new_embedding_model: str) -> Dict[str, Any]:
    """Validate model switch before proceeding"""
    print(f"\n🔍 Validating switch to {new_embedding_model}...")
    
    validation_result = migration_manager.validate_model_switch(new_embedding_model)
    
    print(f"   Current Model: {validation_result['current_model']}")
    print(f"   New Model: {validation_result['new_model']}")
    print(f"   Migration Needed: {validation_result['migration_needed']}")
    print(f"   Is Safe: {validation_result['is_safe']}")
    
    if validation_result['warnings']:
        print("\n   ⚠️  Warnings:")
        for warning in validation_result['warnings']:
            print(f"      - {warning}")
    
    if validation_result['recommendations']:
        print("\n   💡 Recommendations:")
        for rec in validation_result['recommendations']:
            print(f"      - {rec}")
    
    return validation_result

def switch_embedding_model(new_model: str, force: bool = False) -> bool:
    """Switch to a new embedding model with automatic migration"""
    try:
        # Validate the switch
        validation_result = validate_model_switch(new_model)
        
        if not validation_result['is_safe'] and not force:
            print("\n❌ Model switch validation failed. Use --force to proceed anyway.")
            return False
        
        if not validation_result['migration_needed']:
            print(f"\n✅ Model switch to {new_model} is compatible. No migration needed.")
            settings.embedding_model = new_model
            return True
        
        # Initialize vector store
        print(f"\n🔄 Initializing vector store for migration...")
        vector_store = ChromaStore(
            collection_name=settings.chroma_collection_name,
            host=settings.chroma_host,
            port=settings.chroma_port
        )
        
        # Get collection info before migration
        collection_info = vector_store.get_collection_info()
        doc_count = collection_info.get("count", 0)
        
        print(f"   Current collection has {doc_count} documents")
        
        # Confirm migration if there are documents
        if doc_count > 0 and not force:
            response = input(f"\n   This will recreate the collection and migrate {doc_count} documents. Continue? (y/N): ")
            if response.lower() != 'y':
                print("Migration cancelled.")
                return False
        
        # Perform migration
        print(f"\n🚀 Starting migration to {new_model}...")
        migration_result = migration_manager.migrate_vector_store(
            vector_store=vector_store,
            new_embedding_model=new_model,
            backup_data=True
        )
        
        # Display migration results
        print(f"\n📊 Migration Results:")
        print(f"   Status: {migration_result['status']}")
        print(f"   Documents Migrated: {migration_result.get('documents_migrated', 0)}")
        
        if migration_result.get('duration_seconds'):
            print(f"   Duration: {migration_result['duration_seconds']:.2f} seconds")
        
        if migration_result.get('errors'):
            print(f"   Errors: {len(migration_result['errors'])}")
            for error in migration_result['errors']:
                print(f"      - {error}")
        
        if migration_result['status'] in ['completed', 'completed_with_warnings']:
            print(f"\n✅ Successfully switched to {new_model}")
            return True
        else:
            print(f"\n❌ Migration failed")
            return False
            
    except Exception as e:
        logger.error(f"Failed to switch embedding model: {str(e)}")
        print(f"\n❌ Failed to switch embedding model: {str(e)}")
        return False

def switch_llm_model(new_provider: str, new_model: str) -> bool:
    """Switch LLM provider and model"""
    try:
        print(f"\n🔄 Switching LLM to {new_provider}:{new_model}...")
        
        # Update settings
        settings.llm_provider = new_provider
        settings.llm_model = new_model
        
        # Validate new configuration
        llm_config = ModelConfiguration.validate_llm_config()
        
        if llm_config['is_valid']:
            print(f"✅ Successfully switched to {new_provider}:{new_model}")
            return True
        else:
            print(f"❌ LLM configuration validation failed: {llm_config['error_message']}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to switch LLM model: {str(e)}")
        print(f"❌ Failed to switch LLM model: {str(e)}")
        return False

def show_available_models():
    """Show available models for different providers"""
    print("\n📚 Available Models:")
    
    # Show embedding models
    embedding_recs = ModelConfiguration.get_model_recommendations()
    print("\n   🔤 Embedding Models:")
    for provider, models in embedding_recs.items():
        print(f"      {provider.upper()}:")
        for model in models:
            dimension = ModelConfiguration.get_embedding_dimension(model)
            dim_str = f" ({dimension}D)" if dimension else ""
            print(f"         - {model}{dim_str}")
    
    # Show LLM models
    llm_recs = ModelConfiguration.get_llm_recommendations()
    print("\n   🤖 LLM Models:")
    for provider, models in llm_recs.items():
        print(f"      {provider.upper()}:")
        for model in models:
            print(f"         - {model}")

def show_migration_history():
    """Show migration history"""
    print("\n📜 Migration History:")
    
    history = migration_manager.get_migration_history()
    if not history:
        print("   No migrations found.")
        return
    
    for i, migration in enumerate(history, 1):
        print(f"\n   {i}. {migration.get('start_time', 'Unknown time')}")
        print(f"      {migration.get('old_model', 'Unknown')} -> {migration.get('new_model', 'Unknown')}")
        print(f"      Status: {migration.get('status', 'Unknown')}")
        if migration.get('documents_migrated'):
            print(f"      Documents: {migration['documents_migrated']}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Switch between different LLM and embedding models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python switch_models.py --show-config
    python switch_models.py --embedding-model text-embedding-3-small
    python switch_models.py --llm-provider openai --llm-model gpt-4o
    python switch_models.py --embedding-model nomic-embed-text --force
    python switch_models.py --show-models
    python switch_models.py --show-history
        """
    )
    
    parser.add_argument('--show-config', action='store_true',
                      help='Show current configuration')
    parser.add_argument('--embedding-model', type=str,
                      help='Switch to a new embedding model')
    parser.add_argument('--llm-provider', type=str,
                      help='Switch to a new LLM provider')
    parser.add_argument('--llm-model', type=str,
                      help='Switch to a new LLM model')
    parser.add_argument('--force', action='store_true',
                      help='Force the switch even if validation fails')
    parser.add_argument('--show-models', action='store_true',
                      help='Show available models')
    parser.add_argument('--show-history', action='store_true',
                      help='Show migration history')
    
    args = parser.parse_args()
    
    print("🔄 Model Switching Utility")
    print("=" * 50)
    
    # Always show current config first
    print_current_config()
    
    # Handle different commands
    if args.show_models:
        show_available_models()
    elif args.show_history:
        show_migration_history()
    elif args.show_config:
        # Already shown above
        pass
    elif args.embedding_model:
        success = switch_embedding_model(args.embedding_model, args.force)
        if success:
            print_current_config()
        sys.exit(0 if success else 1)
    elif args.llm_provider or args.llm_model:
        if args.llm_provider and args.llm_model:
            success = switch_llm_model(args.llm_provider, args.llm_model)
            if success:
                print_current_config()
            sys.exit(0 if success else 1)
        else:
            print("❌ Both --llm-provider and --llm-model must be specified together")
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
