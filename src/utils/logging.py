import logging
import sys
from typing import Optional

def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """Setup structured logging configuration"""
    
    # Create logger
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
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str = "knowledge_base_agent") -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)
