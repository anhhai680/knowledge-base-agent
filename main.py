"""
Knowledge Base Agent - Main Application Entry Point

This is the MVP implementation of the Knowledge Base Agent that can:
1. Index GitHub repositories
2. Answer questions about indexed code
3. Provide a REST API for interactions
"""

import os
import uvicorn
from src.config.settings import settings
from src.utils.logging import setup_logging, get_logger

def main():
    """Main application entry point"""
    try:
        # Setup logging
        setup_logging(settings.log_level)
        logger = get_logger(__name__)
        
        logger.info("Starting Knowledge Base Agent...")
        logger.info(f"Environment: {settings.app_env}")
        logger.info(f"API will be available at: http://{settings.api_host}:{settings.api_port}")
        
        # Import app after settings are loaded
        from src.api.routes import app
        
        # Run the application
        # Disable reload in containerized environments to prevent restart loops
        use_reload = settings.app_env == "development" and not os.getenv("DOCKER_CONTAINER", False)
        
        uvicorn.run(
            app,
            host=settings.api_host,
            port=settings.api_port,
            reload=use_reload,
            log_level=settings.log_level.lower()
        )
        
    except Exception as e:
        print(f"💥 Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
