import logging
import time
from database.repository import ProviderRepository
from providers import get_provider

logger = logging.getLogger("ForgeHub.ModelRouter")

class RoutingError(Exception):
    pass

class ModelRouter:
    def __init__(self, db_manager):
        self.repo = ProviderRepository(db_manager)
        
        # Tracks temporarily rate-limited providers: {"provider_name": cooldown_until_timestamp}
        self.rate_limit_cooldowns = {}

    def _is_rate_limited(self, provider_name: str) -> bool:
        """Check if a provider is in rate-limit cooldown."""
        cooldown_until = self.rate_limit_cooldowns.get(provider_name, 0)
        if time.time() < cooldown_until:
            return True
        # Cooldown expired, remove it
        self.rate_limit_cooldowns.pop(provider_name, None)
        return False

    def _set_rate_limit(self, provider_name: str, cooldown_seconds: int = 60):
        """Mark a provider as rate-limited for a cooldown period."""
        self.rate_limit_cooldowns[provider_name] = time.time() + cooldown_seconds
        logger.warning(f"Rate-limited {provider_name} for {cooldown_seconds}s")

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation: ~4 chars per token for English text."""
        return len(text) // 4

    def route_request(self, prompt: str, category: str = "General", system_prompt: str = "", context: str = "", max_tokens: int = 1024) -> str:
        """
        Dynamically routes a prompt to the best available model.
        Falls back to other providers if a rate limit or API error occurs.
        """
        # First, try to get models specifically in the category
        models = self.repo.get_available_models(category=category)
        
        # Fallback to any model if category is empty
        if not models:
            logger.warning(f"No models found for category '{category}'. Falling back to any available.")
            models = self.repo.get_available_models()
            
        if not models:
            raise RoutingError("No available AI models or valid API keys found. Please configure them in AI Providers.")
        
        # Estimate input size for context compatibility check
        total_input = f"{system_prompt}\n{context}\n{prompt}"
        estimated_tokens = self._estimate_tokens(total_input) + max_tokens
            
        last_error = None
        for m in models:
            provider_name = m["provider_name"]
            
            # Skip rate-limited providers
            if self._is_rate_limited(provider_name):
                logger.info(f"Skipping {provider_name} — currently rate-limited")
                continue
            
            # Context size check — skip models that are too small
            model_context = m.get("context_size", 0)
            if model_context > 0 and estimated_tokens > model_context:
                logger.info(f"Skipping {provider_name}/{m['model_id']} — context too small ({model_context} < {estimated_tokens})")
                continue
            
            provider = get_provider(provider_name, m["api_key"])
                
            try:
                logger.info(f"Routing request to {provider_name} ({m['model_id']})")
                result = provider.generate(
                    model_id=m["model_id"],
                    prompt=prompt,
                    system_prompt=system_prompt,
                    context=context,
                    max_tokens=max_tokens
                )
                return result
                
            except Exception as e:
                error_status = provider.get_status()
                logger.error(f"Failed routing to {provider_name} ({m['model_id']}): {error_status} — {str(e)}")
                
                # If rate-limited, set cooldown so we don't retry this provider
                if error_status == "LIMITED":
                    self._set_rate_limit(provider_name)
                    
                last_error = e
                continue
            finally:
                provider.close()
                
        raise RoutingError(f"All routed models failed. Last error: {str(last_error)}")
