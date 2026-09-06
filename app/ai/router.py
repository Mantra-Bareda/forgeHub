import logging
import time
from database.repository import ProviderRepository
from providers import get_provider

logger = logging.getLogger("ForgeHub.ModelRouter")

class RoutingError(Exception):
    pass

class ModelRouter:
    def __init__(self, db_manager):
        self.db_manager = db_manager
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

    def detect_task_category(self, prompt: str) -> str:
        """Classify prompts automatically based on simple keyword matching."""
        prompt_lower = prompt.lower()
        if any(kw in prompt_lower for kw in ["code", "debug", "python", "function", "refactor"]):
            return "Coding"
        if any(kw in prompt_lower for kw in ["write", "essay", "blog", "draft", "summarize"]):
            return "Professional Writing"
        if any(kw in prompt_lower for kw in ["think", "analyze", "explain", "why", "how"]):
            return "Reasoning"
        return "General"

    def route_request(self, prompt: str, category: str = "General", system_prompt: str = "", context: str = "", max_tokens: int = 1024) -> tuple:
        """
        Dynamically routes a prompt to the best available model.
        Returns a tuple: (response_text, metadata_dict)
        metadata_dict contains Phase 21 Transparency data: provider, model, task, reason, fallback
        """
        original_category = category
        if category == "General":
            category = self.detect_task_category(prompt)

        selection_reason = "Best available model for category"
        
        # Fetch ALL models instead of just the category
        all_models = self.repo.get_available_models()
        if not all_models:
            raise RoutingError("No available AI models or valid API keys found. Please configure them in AI Providers.")
            
        # Prioritize matching category first, then fallback to others
        categorized_models = [m for m in all_models if m.get("category") == category]
        other_models = [m for m in all_models if m.get("category") != category]
        
        models = categorized_models + other_models
        
        if not categorized_models:
            logger.warning(f"No models found for category '{category}'. Falling back to any available.")
            selection_reason = "Fallback to generic model (no category match)"
        
        total_input = f"{system_prompt}\n{context}\n{prompt}"
        estimated_tokens = self._estimate_tokens(total_input) + max_tokens
            
        last_error = None
        attempt_count = 0
        
        for m in models:
            # Dynamically update selection reason if we cross from categorized to generic
            if categorized_models and m in other_models and selection_reason == "Best available model for category":
                selection_reason = "Fallback to generic model (Categorized models failed/rate-limited)"
                
            provider_name = m["provider_name"]
            
            if self._is_rate_limited(provider_name):
                continue
            
            model_context = m.get("context_size", 0)
            if model_context > 0 and estimated_tokens > model_context:
                continue
                
            attempt_count += 1
            provider = get_provider(provider_name, m["api_key"])
            start_time = time.time()
            
            try:
                result = provider.generate(
                    model_id=m["model_id"],
                    prompt=prompt,
                    system_prompt=system_prompt,
                    context=context,
                    max_tokens=max_tokens
                )
                
                latency_ms = int((time.time() - start_time) * 1000)
                
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO ai_events (provider, model, task_type, status, latency_ms) VALUES (?, ?, ?, ?, ?)",
                        (provider_name, m["model_id"], category, "Success", latency_ms)
                    )
                    comp_tokens = self._estimate_tokens(result)
                    cursor.execute(
                        "INSERT INTO usage_info (provider, model, prompt_tokens, completion_tokens) VALUES (?, ?, ?, ?)",
                        (provider_name, m["model_id"], self._estimate_tokens(total_input), comp_tokens)
                    )
                    conn.commit()
                
                metadata = {
                    "provider": provider_name,
                    "model": m["model_id"],
                    "task": category,
                    "reason": selection_reason,
                    "fallback_status": "None" if attempt_count == 1 else f"Fell back after {attempt_count - 1} failure(s)"
                }
                
                return (result, metadata)
                
            except Exception as e:
                error_status = provider.get_status()
                latency_ms = int((time.time() - start_time) * 1000)
                
                with self.db_manager.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO ai_events (provider, model, task_type, status, latency_ms) VALUES (?, ?, ?, ?, ?)",
                        (provider_name, m["model_id"], category, "Failed", latency_ms)
                    )
                    conn.commit()
                
                if error_status == "LIMITED":
                    self._set_rate_limit(provider_name)
                    
                last_error = e
                continue
            finally:
                provider.close()
                
        raise RoutingError(f"All routed models failed. Last error: {str(last_error)}")
