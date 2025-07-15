"""
Ollama LLM implementation for local/remote Ollama models
"""

from typing import Dict, Any, Optional
try:
    from langchain_ollama import OllamaLLM as LangChainOllama, ChatOllama
except ImportError:
    from langchain_community.llms import Ollama as LangChainOllama
    from langchain_community.chat_models import ChatOllama
from ..utils.logging import get_logger

logger = get_logger(__name__)

class OllamaLLM:
    """Ollama LLM implementation"""
    
    def __init__(self, 
                 model: str = "llama2", 
                 base_url: str = "http://localhost:11434",
                 temperature: float = 0.7,
                 use_chat_model: bool = True):
        """
        Initialize Ollama LLM
        
        Args:
            model: Model name (e.g., "llama2", "mistral", "codellama")
            base_url: Base URL for Ollama API
            temperature: Temperature for generation
            use_chat_model: Whether to use chat model (recommended for conversational tasks)
        """
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.use_chat_model = use_chat_model
        
        try:
            if use_chat_model:
                self.llm = ChatOllama(
                    model=model,
                    base_url=base_url,
                    temperature=temperature
                )
            else:
                self.llm = LangChainOllama(
                    model=model,
                    base_url=base_url,
                    temperature=temperature
                )
            logger.info(f"Ollama LLM initialized with model: {model} at {base_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Ollama LLM: {str(e)}")
            raise
    
    def get_llm(self):
        """Get the underlying LangChain LLM object"""
        return self.llm
    
    def invoke(self, prompt: str) -> str:
        """Invoke the LLM with a prompt"""
        try:
            if self.use_chat_model:
                response = self.llm.invoke(prompt)
                return response.content if hasattr(response, 'content') else str(response)
            else:
                response = self.llm.invoke(prompt)
                return response
        except Exception as e:
            logger.error(f"Ollama LLM invocation failed: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "provider": "ollama",
            "model": self.model,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "use_chat_model": self.use_chat_model
        }
