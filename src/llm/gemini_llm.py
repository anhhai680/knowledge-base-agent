import google.generativeai as genai
from typing import Dict, Any, Optional, List
from langchain_google_genai import ChatGoogleGenerativeAI
from ..utils.logging import get_logger

logger = get_logger(__name__)

class GeminiLLM:
    """Gemini LLM implementation"""
    
    def __init__(self, api_key: str, model_name: str = "gemini-pro", temperature: float = 0.7):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        
        try:
            # Initialize the LangChain Gemini LLM
            self.llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=api_key,
                temperature=temperature,
                max_output_tokens=4000,
                top_p=0.9,
                top_k=40
            )
            
            # Also configure the direct API for fallback
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            logger.info(f"Gemini LLM initialized with model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini LLM: {str(e)}")
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
            logger.error(f"Gemini LLM invocation failed: {str(e)}")
            # Fallback to direct API
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
            except Exception as fallback_e:
                logger.error(f"Fallback Gemini invocation also failed: {str(fallback_e)}")
                raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "provider": "gemini",
            "model": self.model_name,
            "temperature": self.temperature
        }
