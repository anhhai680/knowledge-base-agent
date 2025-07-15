#!/usr/bin/env python3
"""
Test script to verify LLM and embedding model switching functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import settings
from src.config.model_config import ModelConfiguration
from src.llm.llm_factory import LLMFactory
from src.llm.embedding_factory import EmbeddingFactory
from src.utils.logging import setup_logging, get_logger

def test_configuration():
    """Test the configuration system"""
    setup_logging("INFO")
    logger = get_logger(__name__)
    
    logger.info("Testing Knowledge Base Agent Model Configuration")
    logger.info("=" * 50)
    
    # Test configuration summary
    logger.info("\n1. Configuration Summary:")
    config_summary = ModelConfiguration.get_configuration_summary()
    
    logger.info(f"Environment: {config_summary['environment']}")
    logger.info(f"Overall Status: {config_summary['overall_status']}")
    
    # LLM Configuration
    llm_config = config_summary['llm']
    logger.info(f"\nLLM Configuration:")
    logger.info(f"  Provider: {llm_config['provider']}")
    logger.info(f"  Model: {llm_config['model']}")
    logger.info(f"  Valid: {llm_config['is_valid']}")
    if llm_config['error_message']:
        logger.info(f"  Error: {llm_config['error_message']}")
    
    # Embedding Configuration
    embedding_config = config_summary['embedding']
    logger.info(f"\nEmbedding Configuration:")
    logger.info(f"  Model: {embedding_config['model']}")
    logger.info(f"  Detected Provider: {embedding_config['detected_provider']}")
    logger.info(f"  Valid: {embedding_config['is_valid']}")
    if embedding_config['error_message']:
        logger.info(f"  Error: {embedding_config['error_message']}")
    
    # Test LLM Factory
    logger.info("\n2. Testing LLM Factory:")
    try:
        llm = LLMFactory.create_llm()
        logger.info(f"✓ LLM created successfully: {type(llm)}")
        
        # Test a simple invoke
        try:
            response = llm.invoke("Hello, how are you?")
            logger.info(f"✓ LLM invocation successful: {response[:100]}...")
        except Exception as e:
            logger.warning(f"⚠ LLM invocation failed: {e}")
            
    except Exception as e:
        logger.error(f"✗ LLM creation failed: {e}")
    
    # Test Embedding Factory
    logger.info("\n3. Testing Embedding Factory:")
    try:
        embedding = EmbeddingFactory.create_embedding()
        logger.info(f"✓ Embedding function created successfully: {type(embedding)}")
        
        # Test embedding generation
        try:
            test_text = "This is a test document for embedding generation."
            embeddings = embedding.embed_documents([test_text])
            logger.info(f"✓ Embedding generation successful: {len(embeddings)} embeddings, dimension: {len(embeddings[0])}")
        except Exception as e:
            logger.warning(f"⚠ Embedding generation failed: {e}")
            
    except Exception as e:
        logger.error(f"✗ Embedding creation failed: {e}")
    
    # Test model recommendations
    logger.info("\n4. Model Recommendations:")
    llm_recommendations = ModelConfiguration.get_llm_recommendations()
    embedding_recommendations = ModelConfiguration.get_model_recommendations()
    
    logger.info("LLM Models:")
    for provider, models in llm_recommendations.items():
        logger.info(f"  {provider}: {', '.join(models[:3])}...")
    
    logger.info("Embedding Models:")
    for provider, models in embedding_recommendations.items():
        logger.info(f"  {provider}: {', '.join(models[:3])}...")
    
    logger.info("\n" + "=" * 50)
    logger.info("Configuration test completed!")

if __name__ == "__main__":
    test_configuration()
