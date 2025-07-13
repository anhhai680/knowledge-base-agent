"""
Knowledge Base Agent - Main Application Entry Point

This is the MVP implementation of the Knowledge Base Agent that can:
1. Index GitHub repositories
2. Answer questions about indexed code
3. Provide a REST API for interactions
"""

import uvicorn
from src.api.routes import app
from src.config.settings import settings
from src.utils.logging import setup_logging, get_logger

def main():
    """Main application entry point"""
    # Setup logging
    setup_logging(settings.log_level)
    logger = get_logger(__name__)
    
    logger.info("Starting Knowledge Base Agent...")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"API will be available at: http://{settings.api_host}:{settings.api_port}")
    
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower()
    )

if __name__ == "__main__":
    main()
