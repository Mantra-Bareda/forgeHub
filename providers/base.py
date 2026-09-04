from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx

class AIProvider(ABC):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.status = "AVAILABLE"
        self.client = httpx.Client(timeout=30.0)

    def authenticate(self) -> bool:
        """Validates the API key. Alias for test_key."""
        return self.test_key()
        
    @abstractmethod
    def test_key(self) -> bool:
        pass
        
    @abstractmethod
    def discover_models(self) -> List[Dict[str, Any]]:
        pass
        
    @abstractmethod
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        pass
        
    @abstractmethod
    def generate(self, model_id: str, prompt: str, system_prompt: str = "", context: str = "", max_tokens: int = 1024) -> str:
        pass
        
    def handle_error(self, error: Exception) -> str:
        if isinstance(error, httpx.HTTPStatusError):
            code = error.response.status_code
            if code in (401, 403):
                self.status = "INVALID_KEY"
            elif code == 400:
                # Many providers return 400 for invalid API keys
                body = error.response.text.lower()
                if "api_key" in body or "invalid" in body or "unauthorized" in body:
                    self.status = "INVALID_KEY"
                else:
                    self.status = "API_ERROR"
            elif code == 429:
                self.status = "LIMITED"
            elif code >= 500:
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

    def close(self):
        """Closes the underlying HTTP client."""
        if self.client:
            self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
