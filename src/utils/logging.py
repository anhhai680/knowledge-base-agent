import logging
import sys
from typing import Optional

def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Setup structured logging configuration"""
    
    # Configure root logger to ensure all loggers inherit the correct level
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers from root logger
    root_logger.handlers.clear()
    
    # Create our main logger
    logger = logging.getLogger("knowledge_base_agent")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    
    # Add handler to both root and main logger to ensure coverage
    root_logger.addHandler(console_handler)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        logger.addHandler(file_handler)
    
    # Ensure propagation is enabled for child loggers
    logger.propagate = True
    
    return logger

def get_logger(name: str = "knowledge_base_agent") -> logging.Logger:
    """Get logger instance"""
    logger = logging.getLogger(name)
    # Ensure logger propagates to root logger which has the handlers
    logger.propagate = True
    return logger
