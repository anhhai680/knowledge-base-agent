from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from ..utils.logging import get_logger

logger = get_logger(__name__)

class OpenAILLM:
    """OpenAI LLM implementation"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", temperature: float = 0.7, max_tokens: int = 4000):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        try:
            self.llm = ChatOpenAI(
                openai_api_key=api_key,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            logger.info(f"OpenAI LLM initialized with model: {model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI LLM: {str(e)}")
            raise
    
    def invoke(self, prompt: str) -> str:
        """Invoke the LLM with a prompt"""
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error(f"OpenAI LLM invocation failed: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "provider": "openai",
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
