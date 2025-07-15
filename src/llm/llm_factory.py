from typing import Dict, Any, Optional, List
from .openai_llm import OpenAILLM
from .gemini_llm import GeminiLLM
from .ollama_llm import OllamaLLM
from .azure_openai_llm import AzureOpenAILLM
from ..config.settings import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)

class LLMFactory:
    """Factory class to create LLM instances based on provider and configuration"""
    
    @staticmethod
    def create_llm(provider: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Create LLM instance based on provider and configuration
        
        Args:
            provider: LLM provider (if None, uses settings.llm_provider)
            config: Configuration dictionary (if None, uses settings)
        
        Returns:
            LLM instance
        """
        # Use settings if no explicit provider/config provided
        if provider is None:
            provider = settings.llm_provider
        
        if config is None:
            config = LLMFactory._get_config_from_settings()
        
        provider = provider.lower()
        
        if provider == "openai":
            return LLMFactory._create_openai_llm(config)
        elif provider == "gemini":
            return LLMFactory._create_gemini_llm(config)
        elif provider == "ollama":
            return LLMFactory._create_ollama_llm(config)
        elif provider == "azure_openai":
            return LLMFactory._create_azure_openai_llm(config)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    @staticmethod
    def _get_config_from_settings() -> Dict[str, Any]:
        """Get configuration from settings"""
        return {
            "model": settings.llm_model,
            "api_base_url": settings.llm_api_base_url,
            "openai_api_key": settings.openai_api_key,
            "gemini_api_key": settings.gemini_api_key,
            "azure_openai_api_key": settings.azure_openai_api_key,
            "azure_openai_endpoint": settings.azure_openai_endpoint,
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens
        }
    
    @staticmethod
    def _create_openai_llm(config: Dict[str, Any]):
        """Create OpenAI LLM instance"""
        if not config.get("openai_api_key"):
            raise ValueError("OpenAI API key is required")
        
        llm_wrapper = OpenAILLM(
            api_key=config["openai_api_key"],
            model=config.get("model", "gpt-3.5-turbo"),
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 4000)
        )
        return llm_wrapper.get_llm()
    
    @staticmethod
    def _create_gemini_llm(config: Dict[str, Any]):
        """Create Gemini LLM instance"""
        if not config.get("gemini_api_key"):
            raise ValueError("Gemini API key is required")
        
        llm_wrapper = GeminiLLM(
            api_key=config["gemini_api_key"],
            model_name=config.get("model", "gemini-pro"),
            temperature=config.get("temperature", 0.7)
        )
        return llm_wrapper.get_llm()
    
    @staticmethod
    def _create_ollama_llm(config: Dict[str, Any]):
        """Create Ollama LLM instance"""
        base_url = config.get("api_base_url", "http://localhost:11434")
        model = config.get("model", "llama2")
        
        llm_wrapper = OllamaLLM(
            model=model,
            base_url=base_url,
            temperature=config.get("temperature", 0.7)
        )
        return llm_wrapper.get_llm()
    
    @staticmethod
    def _create_azure_openai_llm(config: Dict[str, Any]):
        """Create Azure OpenAI LLM instance"""
        if not config.get("azure_openai_api_key"):
            raise ValueError("Azure OpenAI API key is required")
        if not config.get("azure_openai_endpoint"):
            raise ValueError("Azure OpenAI endpoint is required")
        
        llm_wrapper = AzureOpenAILLM(
            api_key=config["azure_openai_api_key"],
            azure_endpoint=config["azure_openai_endpoint"],
            model=config.get("model", "gpt-35-turbo"),
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 4000)
        )
        return llm_wrapper.get_llm()
    
    @staticmethod
    def get_supported_providers() -> List[str]:
        """Get list of supported LLM providers"""
        return ["openai", "gemini", "ollama", "azure_openai"]
    
    @staticmethod
    def get_available_provider(config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Get the first available provider based on configuration
        
        Args:
            config: Configuration dictionary (if None, uses settings)
        
        Returns:
            Available provider name or None
        """
        if config is None:
            config = LLMFactory._get_config_from_settings()
        
        # Check configured provider first
        provider = settings.llm_provider.lower()
        
        if provider == "openai" and config.get("openai_api_key"):
            return "openai"
        elif provider == "gemini" and config.get("gemini_api_key"):
            return "gemini"
        elif provider == "azure_openai" and config.get("azure_openai_api_key") and config.get("azure_openai_endpoint"):
            return "azure_openai"
        elif provider == "ollama":
            # Ollama doesn't require API key, just check if base URL is accessible
            return "ollama"
        
        # Fallback to any available provider
        if config.get("openai_api_key"):
            return "openai"
        elif config.get("gemini_api_key"):
            return "gemini"
        elif config.get("azure_openai_api_key") and config.get("azure_openai_endpoint"):
            return "azure_openai"
        else:
            return "ollama"  # Fallback to ollama as it doesn't require API key
