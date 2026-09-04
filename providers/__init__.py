from providers.base import AIProvider
from providers.gemini_provider import GeminiProvider
from providers.groq_provider import GroqProvider
from providers.mistral_provider import MistralProvider
from providers.cerebras_provider import CerebrasProvider

PROVIDER_MAP = {
    "Gemini": GeminiProvider,
    "Groq": GroqProvider,
    "Mistral": MistralProvider,
    "Cerebras": CerebrasProvider,
}

def get_provider(provider_name: str, api_key: str) -> AIProvider:
    """Factory function to get a provider instance by name."""
    cls = PROVIDER_MAP.get(provider_name)
    if not cls:
        raise ValueError(f"Unknown provider: {provider_name}")
    return cls(api_key)

__all__ = [
    "AIProvider",
    "GeminiProvider",
    "GroqProvider",
    "MistralProvider",
    "CerebrasProvider",
    "get_provider",
    "PROVIDER_MAP",
]
