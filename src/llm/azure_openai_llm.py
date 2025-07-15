"""
Azure OpenAI LLM implementation
"""

from typing import Dict, Any, Optional
from langchain_openai import AzureChatOpenAI
from ..utils.logging import get_logger

logger = get_logger(__name__)

class AzureOpenAILLM:
    """Azure OpenAI LLM implementation"""
    
    def __init__(self, 
                 api_key: str,
                 azure_endpoint: str,
                 model: str = "gpt-35-turbo",
                 deployment_name: Optional[str] = None,
                 api_version: str = "2023-12-01-preview",
                 temperature: float = 0.7, 
                 max_tokens: int = 4000):
        """
        Initialize Azure OpenAI LLM
        
        Args:
            api_key: Azure OpenAI API key
            azure_endpoint: Azure OpenAI endpoint
            model: Model name
            deployment_name: Azure deployment name (if different from model)
            api_version: API version
            temperature: Temperature for generation
            max_tokens: Maximum tokens for generation
        """
        self.api_key = api_key
        self.azure_endpoint = azure_endpoint
        self.model = model
        self.deployment_name = deployment_name or model
        self.api_version = api_version
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        try:
            self.llm = AzureChatOpenAI(
                api_key=api_key,
                azure_endpoint=azure_endpoint,
                deployment_name=self.deployment_name,
                api_version=api_version,
                temperature=temperature,
                max_tokens=max_tokens
            )
            logger.info(f"Azure OpenAI LLM initialized with model: {model} (deployment: {self.deployment_name})")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI LLM: {str(e)}")
            raise
    
    def get_llm(self):
        """Get the underlying LangChain LLM object"""
        return self.llm
    
    def invoke(self, prompt: str) -> str:
        """Invoke the LLM with a prompt"""
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"Azure OpenAI LLM invocation failed: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "provider": "azure_openai",
            "model": self.model,
            "deployment_name": self.deployment_name,
            "azure_endpoint": self.azure_endpoint,
            "api_version": self.api_version,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
