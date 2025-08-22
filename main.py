"""
Knowledge Base Agent - Main Application Entry Point

This is the MVP implementation of the Knowledge Base Agent that can:
1. Index GitHub repositories
2. Answer questions about indexed code
3. Provide a REST API for interactions
4. Generate enhanced diagrams with DiagramAgent
"""

import os
import sys
import asyncio
import time
import uvicorn

# Add the current directory to Python path to ensure imports work in Docker
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.config.settings import settings
from src.utils.logging import setup_logging, get_logger

# Import app at module level for uvicorn
from src.api.routes import app

async def validate_diagram_agent_startup():
    """Validate DiagramAgent initialization and configuration"""
    logger = get_logger(__name__)
    max_retries = 10
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            # Import here to avoid circular imports
            import httpx
            
            # Test health endpoint
            async with httpx.AsyncClient() as client:
                health_url = f"http://{settings.api_host}:{settings.api_port}/health"
                response = await client.get(health_url, timeout=5)
                
                if response.status_code == 200:
                    health_data = response.json()
                    components = health_data.get("components", {})
                    
                    # Check if DiagramAgent-related components are healthy
                    required_components = ["llm", "vector_store", "configuration"]
                    unhealthy_components = []
                    
                    for component in required_components:
                        status = components.get(component, "missing")
                        if status != "healthy":
                            unhealthy_components.append(f"{component}: {status}")
                    
                    if not unhealthy_components:
                        logger.info("✓ DiagramAgent dependencies validated successfully")
                        return True
                    else:
                        logger.warning(f"⚠ Some components not ready: {', '.join(unhealthy_components)}")
                
        except Exception as e:
            logger.debug(f"Health check attempt {attempt + 1} failed: {str(e)}")
        
        if attempt < max_retries - 1:
            logger.info(f"Waiting {retry_delay}s before retry {attempt + 2}/{max_retries}...")
            await asyncio.sleep(retry_delay)
    
    logger.error("💥 Failed to validate DiagramAgent startup after maximum retries")
    return False


async def verify_enhanced_diagram_features():
    """Verify that enhanced diagram features are operational"""
    logger = get_logger(__name__)
    
    try:
        # Import here to avoid circular imports during startup
        import httpx
        
        # Test a simple diagram query to validate the enhanced system
        async with httpx.AsyncClient() as client:
            query_url = f"http://{settings.api_host}:{settings.api_port}/query"
            test_payload = {
                "question": "generate a simple sequence diagram",
                "max_results": 1
            }
            
            response = await client.post(query_url, json=test_payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                # Check if the response has diagram-specific fields
                has_diagram_fields = any(key in result for key in ['mermaid_code', 'diagram_type'])
                
                if has_diagram_fields:
                    logger.info("✓ Enhanced diagram features are operational")
                    return True
                else:
                    logger.warning("⚠ Diagram features available but may not be enhanced")
                    return True  # Still functional, just not enhanced
            else:
                logger.warning(f"⚠ Diagram query test failed with status {response.status_code}")
                
    except Exception as e:
        logger.warning(f"⚠ Enhanced diagram features verification failed: {str(e)}")
        logger.info("Application will continue with basic functionality")
    
    return False
def main():
    """Main application entry point with enhanced DiagramAgent validation"""
    try:
        # Setup logging
        setup_logging(settings.log_level)
        logger = get_logger(__name__)
        
        logger.info("🚀 Starting Knowledge Base Agent...")
        logger.info(f"Environment: {settings.app_env}")
        logger.info(f"API will be available at: http://{settings.api_host}:{settings.api_port}")
        
        # Validate configuration for enhanced diagram features
        logger.info("🔧 Validating configuration for enhanced diagram features...")
        try:
            from src.config.model_config import ModelConfiguration
            
            llm_config = ModelConfiguration.validate_llm_config()
            embedding_config = ModelConfiguration.validate_embedding_config()
            
            if not llm_config["is_valid"]:
                logger.error(f"❌ Invalid LLM configuration: {llm_config.get('error_message', 'Unknown error')}")
                return 1
            
            if not embedding_config["is_valid"]:
                logger.error(f"❌ Invalid embedding configuration: {embedding_config.get('error_message', 'Unknown error')}")
                return 1
                
            logger.info("✓ Configuration validation passed for enhanced features")
            
        except Exception as e:
            logger.error(f"❌ Configuration validation failed: {str(e)}")
            return 1
        
        # Prepare startup validation task
        async def startup_with_validation():
            """Enhanced startup with DiagramAgent validation"""
            logger.info("⚙️ Starting server...")
            
            # Start server in background
            server_config = uvicorn.Config(
                app,
                host=settings.api_host,
                port=settings.api_port,
                reload=False,  # Disable reload for validation
                log_level=settings.log_level.lower()
            )
            server = uvicorn.Server(server_config)
            
            # Start server task
            server_task = asyncio.create_task(server.serve())
            
            # Wait a moment for server to start
            await asyncio.sleep(3)
            
            # Validate DiagramAgent startup
            logger.info("🔍 Validating DiagramAgent initialization...")
            diagram_agent_valid = await validate_diagram_agent_startup()
            
            if diagram_agent_valid:
                logger.info("✓ DiagramAgent validation successful")
                
                # Verify enhanced features
                logger.info("🎯 Verifying enhanced diagram features...")
                features_valid = await verify_enhanced_diagram_features()
                
                if features_valid:
                    logger.info("🎉 Enhanced diagram features are operational!")
                else:
                    logger.warning("⚠️ Enhanced features may have limited functionality")
            else:
                logger.error("❌ DiagramAgent validation failed - continuing with degraded functionality")
            
            logger.info("🌟 Knowledge Base Agent is ready!")
            
            # Wait for server to complete
            await server_task
        
        # Run the application with enhanced validation
        # Disable reload in containerized environments to prevent restart loops
        use_reload = settings.app_env == "development" and not bool(os.getenv("DOCKER_CONTAINER"))
        
        if use_reload:
            # Development mode - use standard uvicorn with reload
            logger.info("🔄 Development mode: using reload without validation")
            uvicorn.run(
                app,
                host=settings.api_host,
                port=settings.api_port,
                reload=True,
                log_level=settings.log_level.lower()
            )
        else:
            # Production mode - use enhanced startup with validation
            logger.info("🚀 Production mode: using enhanced startup validation")
            asyncio.run(startup_with_validation())
        
    except KeyboardInterrupt:
        logger.info("🛑 Application stopped by user")
        return 0
    except Exception as e:
        print(f"💥 Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
