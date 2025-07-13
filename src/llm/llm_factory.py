from typing import Dict, Any, Optional, List
from .openai_llm import OpenAILLM
from .gemini_llm import GeminiLLM
from ..utils.logging import get_logger

logger = get_logger(__name__)

class LLMFactory:
    """Factory class to create LLM instances based on provider"""
    
    @staticmethod
    def create_llm(provider: str, config: Dict[str, Any]):
        """Create LLM instance based on provider"""
        
        if provider.lower() == "openai":
            if not config.get("openai_api_key"):
                raise ValueError("OpenAI API key is required")
            
            return OpenAILLM(
                api_key=config.get("openai_api_key"),
                model=config.get("model", "gpt-4o-mini"),
                temperature=config.get("temperature", 0.7),
                max_tokens=config.get("max_tokens", 4000)
            )
        
        elif provider.lower() == "gemini":
            if not config.get("gemini_api_key"):
                raise ValueError("Gemini API key is required")
            
            return GeminiLLM(
                api_key=config.get("gemini_api_key"),
                model_name=config.get("model", "gemini-pro"),
                temperature=config.get("temperature", 0.7)
            )
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    @staticmethod
    def get_supported_providers() -> List[str]:
        """Get list of supported LLM providers"""
        return ["openai", "gemini"]
    
    @staticmethod
    def get_available_provider(config: Dict[str, Any]) -> Optional[str]:
        """Get the first available provider based on API keys"""
        if config.get("openai_api_key"):
            return "openai"
        elif config.get("gemini_api_key"):
            return "gemini"
        else:
            return None
