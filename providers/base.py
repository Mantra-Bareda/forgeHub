from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx

class AIProvider(ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.status = "AVAILABLE"
        self.client = httpx.Client(timeout=30.0)
        
    @abstractmethod
    def test_key(self) -> bool:
        """Tests if the API key is valid."""
        pass
        
    @abstractmethod
    def discover_models(self) -> List[Dict[str, Any]]:
        """Fetches available models for this provider/key."""
        pass
        
    @abstractmethod
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Returns capabilities and context limits of a specific model."""
        pass
        
    @abstractmethod
    def generate(self, model_id: str, prompt: str, system_prompt: str = "", context: str = "", max_tokens: int = 1024) -> str:
        """Executes an AI generation request."""
        pass
        
    def handle_error(self, error: Exception) -> str:
        """Translates provider-specific errors into standard app states."""
        if isinstance(error, httpx.HTTPStatusError):
            if error.response.status_code == 401:
                self.status = "INVALID_KEY"
            elif error.response.status_code == 429:
                self.status = "LIMITED"
            elif error.response.status_code >= 500:
                self.status = "PROVIDER_ERROR"
            else:
                self.status = "API_ERROR"
        elif isinstance(error, httpx.TimeoutException):
            self.status = "TIMEOUT"
        elif isinstance(error, httpx.RequestError):
            self.status = "NETWORK_ERROR"
        else:
            self.status = "UNKNOWN_ERROR"
            
        return self.status
        
    def get_status(self) -> str:
        return self.status
