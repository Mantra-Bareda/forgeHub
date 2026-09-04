import logging
from typing import Optional
from database.repository import ProviderRepository
from providers.gemini_provider import GeminiProvider
from providers.groq_provider import GroqProvider
from providers.mistral_provider import MistralProvider
from providers.cerebras_provider import CerebrasProvider

logger = logging.getLogger("ForgeHub.ModelRouter")

class RoutingError(Exception):
    pass

class ModelRouter:
    def __init__(self, db_manager):
        self.repo = ProviderRepository(db_manager)
        
        # Tracks temporary rate limits in memory to avoid hammering limited APIs
        # Dictionary format could be: {"provider_name": timestamp_until_clear}
        # For MVP, we handle fallbacks dynamically on exception.
        self.rate_limits = {}

    def _get_provider_instance(self, provider_name: str, api_key: str):
        if provider_name == "Gemini":
            return GeminiProvider(api_key)
        elif provider_name == "Groq":
            return GroqProvider(api_key)
        elif provider_name == "Mistral":
            return MistralProvider(api_key)
        elif provider_name == "Cerebras":
            return CerebrasProvider(api_key)
        return None

    def route_request(self, prompt: str, category: str = "General", system_prompt: str = "", context: str = "", max_tokens: int = 1024) -> str:
        """
        Dynamically routes a prompt to the best available model.
        Falls back to other providers if a rate limit or API error occurs.
        """
        # First, try to get models specifically in the category
        models = self.repo.get_available_models(category=category)
        
        # Fallback to any model if category is empty
        if not models:
            logger.warning(f"No models found for category '{category}'. Falling back to General/Any.")
            models = self.repo.get_available_models()
            
        if not models:
            raise RoutingError("No available AI models or valid API keys found. Please configure them in AI Providers.")
            
        last_error = None
        for m in models:
            provider_name = m["provider_name"]
            
            provider = self._get_provider_instance(provider_name, m["api_key"])
            if not provider:
                continue
                
            try:
                logger.info(f"Routing request to {provider_name} ({m['model_id']})")
                result = provider.generate(
                    model_id=m["model_id"],
                    prompt=prompt,
                    system_prompt=system_prompt,
                    context=context,
                    max_tokens=max_tokens
                )
                
                # Check if provider set status to LIMITED internally without throwing
                if provider.get_status() == "LIMITED":
                    raise Exception("Rate limit hit during generation (429).")
                    
                return result
                
            except Exception as e:
                logger.error(f"Failed routing to {provider_name} ({m['model_id']}): {str(e)}. Falling back...")
                last_error = e
                # We continue to the next model in the list as a fallback!
                continue
                
        raise RoutingError(f"All routed models failed. Last error: {str(last_error)}")
