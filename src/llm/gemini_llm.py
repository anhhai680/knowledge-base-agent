import google.generativeai as genai
from typing import Dict, Any, Optional, List
from ..utils.logging import get_logger

logger = get_logger(__name__)

class GeminiLLM:
    """Gemini LLM implementation"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-pro", temperature: float = 0.7):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            logger.info(f"Gemini LLM initialized with model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini LLM: {str(e)}")
            raise
    
    def invoke(self, prompt: str) -> str:
        """Invoke the LLM with a prompt"""
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=4000,
                top_p=0.9,
                top_k=40
            )
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini LLM invocation failed: {str(e)}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "provider": "gemini",
            "model": self.model_name,
            "temperature": self.temperature
        }
