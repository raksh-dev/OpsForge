from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.language_models.chat_models import BaseChatModel
from ..config.settings import settings
import logging

logger = logging.getLogger(__name__)

def get_llm(
    model: Optional[str] = None,
    temperature: float = 0.3,
    streaming: bool = True,
    provider: Optional[str] = None
) -> BaseChatModel:
    """
    Factory function to get the appropriate LLM based on configuration
    
    Args:
        model: Specific model name (optional, uses default if not provided)
        temperature: Model temperature
        streaming: Whether to enable streaming
        provider: LLM provider ("openai" or "groq", uses settings default if not provided)
    
    Returns:
        Configured LLM instance
    """
    provider = provider or settings.llm_provider
    
    try:
        if provider == "groq":
            model = model or settings.groq_model
            logger.info(f"Initializing Groq LLM with model: {model}")
            return ChatGroq(
                model=model,
                temperature=temperature,
                groq_api_key=settings.groq_api_key,
                streaming=streaming
            )
        
        elif provider == "openai":
            model = model or "gpt-4-turbo-preview"
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            
            logger.info(f"Initializing OpenAI LLM with model: {model}")
            return ChatOpenAI(
                model=model,
                temperature=temperature,
                openai_api_key=settings.openai_api_key,
                streaming=streaming
            )
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
            
    except Exception as e:
        logger.error(f"Error initializing LLM with provider {provider}: {e}")
        # Fallback to Groq if OpenAI fails
        if provider == "openai":
            logger.info("Falling back to Groq LLM")
            return ChatGroq(
                model=settings.groq_model,
                temperature=temperature,
                groq_api_key=settings.groq_api_key,
                streaming=streaming
            )
        raise

def get_available_models(provider: Optional[str] = None) -> dict:
    """Get available models for the specified provider"""
    provider = provider or settings.llm_provider
    
    if provider == "groq":
        return {
            "groq": {
                "llama-3.1-70b-versatile": "Llama 3.1 70B - Most capable",
                "llama-3.1-8b-instant": "Llama 3.1 8B - Fastest",
                "mixtral-8x7b-32768": "Mixtral 8x7B - Good balance",
                "gemma-7b-it": "Gemma 7B - Efficient"
            }
        }
    elif provider == "openai":
        return {
            "openai": {
                "gpt-4-turbo-preview": "GPT-4 Turbo - Most capable",
                "gpt-4": "GPT-4 - Reliable",
                "gpt-3.5-turbo": "GPT-3.5 Turbo - Fast and cheap"
            }
        }
    else:
        return {}