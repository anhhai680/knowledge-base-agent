#!/usr/bin/env python3
"""
Model switching utility for Knowledge Base Agent
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.config.model_config import ModelConfiguration

def update_env_file(env_file: str, updates: dict):
    """Update environment file with new values"""
    env_path = Path(env_file)
    
    if not env_path.exists():
        print(f"Environment file {env_file} does not exist!")
        return False
    
    # Read existing content
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    # Update lines
    updated_lines = []
    updated_keys = set()
    
    for line in lines:
        if '=' in line and not line.strip().startswith('#'):
            key = line.split('=')[0].strip()
            if key in updates:
                updated_lines.append(f"{key}={updates[key]}\n")
                updated_keys.add(key)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)
    
    # Add any new keys that weren't in the file
    for key, value in updates.items():
        if key not in updated_keys:
            updated_lines.append(f"{key}={value}\n")
    
    # Write updated content
    with open(env_path, 'w') as f:
        f.writelines(updated_lines)
    
    print(f"Updated {env_file} with new configuration")
    return True

def switch_to_openai(args):
    """Switch to OpenAI configuration"""
    updates = {
        'LLM_PROVIDER': 'openai',
        'LLM_MODEL': args.llm_model or 'gpt-4o-mini',
        'EMBEDDING_MODEL': args.embedding_model or 'text-embedding-3-small'
    }
    
    if args.llm_api_key:
        updates['OPENAI_API_KEY'] = args.llm_api_key
    
    # Remove base URLs for OpenAI
    if 'LLM_API_BASE_URL' in updates:
        del updates['LLM_API_BASE_URL']
    if 'EMBEDDING_API_BASE_URL' in updates:
        del updates['EMBEDDING_API_BASE_URL']
    
    return updates

def switch_to_gemini(args):
    """Switch to Gemini configuration"""
    updates = {
        'LLM_PROVIDER': 'gemini',
        'LLM_MODEL': args.llm_model or 'gemini-1.5-flash',
        'EMBEDDING_MODEL': args.embedding_model or 'models/embedding-001'
    }
    
    if args.llm_api_key:
        updates['GEMINI_API_KEY'] = args.llm_api_key
    
    # Remove base URLs for Gemini
    if 'LLM_API_BASE_URL' in updates:
        del updates['LLM_API_BASE_URL']
    if 'EMBEDDING_API_BASE_URL' in updates:
        del updates['EMBEDDING_API_BASE_URL']
    
    return updates

def switch_to_ollama(args):
    """Switch to Ollama configuration"""
    updates = {
        'LLM_PROVIDER': 'ollama',
        'LLM_MODEL': args.llm_model or 'llama3.1:8b',
        'EMBEDDING_MODEL': args.embedding_model or 'nomic-embed-text',
        'LLM_API_BASE_URL': args.llm_base_url or 'http://localhost:11434/v1',
        'EMBEDDING_API_BASE_URL': args.embedding_base_url or 'http://localhost:11434/v1/embeddings'
    }
    
    return updates

def switch_to_azure_openai(args):
    """Switch to Azure OpenAI configuration"""
    updates = {
        'LLM_PROVIDER': 'azure_openai',
        'LLM_MODEL': args.llm_model or 'gpt-4o',
        'EMBEDDING_MODEL': args.embedding_model or 'text-embedding-3-large'
    }
    
    if args.llm_api_key:
        updates['AZURE_OPENAI_API_KEY'] = args.llm_api_key
    
    if args.azure_endpoint:
        updates['AZURE_OPENAI_ENDPOINT'] = args.azure_endpoint
    
    return updates

def show_current_config():
    """Show current configuration"""
    print("Current Configuration:")
    print("=" * 50)
    
    try:
        config = ModelConfiguration.get_configuration_summary()
        
        print(f"Environment: {config['environment']}")
        print(f"Overall Status: {config['overall_status']}")
        
        # LLM Config
        llm_config = config['llm']
        print(f"\nLLM Configuration:")
        print(f"  Provider: {llm_config['provider']}")
        print(f"  Model: {llm_config['model']}")
        print(f"  Valid: {llm_config['is_valid']}")
        if llm_config['error_message']:
            print(f"  Error: {llm_config['error_message']}")
        
        # Embedding Config
        embedding_config = config['embedding']
        print(f"\nEmbedding Configuration:")
        print(f"  Model: {embedding_config['model']}")
        print(f"  Detected Provider: {embedding_config['detected_provider']}")
        print(f"  Valid: {embedding_config['is_valid']}")
        if embedding_config['error_message']:
            print(f"  Error: {embedding_config['error_message']}")
        
    except Exception as e:
        print(f"Error reading configuration: {e}")

def show_recommendations():
    """Show model recommendations"""
    print("Model Recommendations:")
    print("=" * 50)
    
    try:
        llm_recs = ModelConfiguration.get_llm_recommendations()
        embedding_recs = ModelConfiguration.get_model_recommendations()
        
        print("LLM Models:")
        for provider, models in llm_recs.items():
            print(f"  {provider}: {', '.join(models)}")
        
        print("\nEmbedding Models:")
        for provider, models in embedding_recs.items():
            print(f"  {provider}: {', '.join(models)}")
            
    except Exception as e:
        print(f"Error getting recommendations: {e}")

def main():
    parser = argparse.ArgumentParser(description='Switch between LLM and embedding models')
    parser.add_argument('--env-file', default='.env', help='Path to environment file')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Switch command
    switch_parser = subparsers.add_parser('switch', help='Switch to a different provider')
    switch_parser.add_argument('provider', choices=['openai', 'gemini', 'ollama', 'azure_openai'],
                              help='Provider to switch to')
    switch_parser.add_argument('--llm-model', help='LLM model to use')
    switch_parser.add_argument('--embedding-model', help='Embedding model to use')
    switch_parser.add_argument('--llm-api-key', help='API key for LLM provider')
    switch_parser.add_argument('--llm-base-url', help='Base URL for LLM API (ollama only)')
    switch_parser.add_argument('--embedding-base-url', help='Base URL for embedding API (ollama only)')
    switch_parser.add_argument('--azure-endpoint', help='Azure OpenAI endpoint')
    
    # Show command
    subparsers.add_parser('show', help='Show current configuration')
    
    # Recommendations command
    subparsers.add_parser('recommendations', help='Show model recommendations')
    
    args = parser.parse_args()
    
    if args.command == 'switch':
        # Get updates based on provider
        updates = {}
        if args.provider == 'openai':
            updates = switch_to_openai(args)
        elif args.provider == 'gemini':
            updates = switch_to_gemini(args)
        elif args.provider == 'ollama':
            updates = switch_to_ollama(args)
        elif args.provider == 'azure_openai':
            updates = switch_to_azure_openai(args)
        
        # Update environment file
        if updates and update_env_file(args.env_file, updates):
            print(f"Successfully switched to {args.provider}")
            print("Please restart the application for changes to take effect.")
        
    elif args.command == 'show':
        show_current_config()
    
    elif args.command == 'recommendations':
        show_recommendations()
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
