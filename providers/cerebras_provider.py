from typing import List, Dict, Any, Optional
from providers.base import AIProvider

class CerebrasProvider(AIProvider):
    BASE_URL = "https://api.cerebras.ai/v1"

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}"}

    def test_key(self) -> bool:
        try:
            response = self.client.get(f"{self.BASE_URL}/models", headers=self._headers())
            response.raise_for_status()
            self.status = "AVAILABLE"
            return True
        except Exception as e:
            self.handle_error(e)
            return False

    def discover_models(self) -> List[Dict[str, Any]]:
        try:
            response = self.client.get(f"{self.BASE_URL}/models", headers=self._headers())
            response.raise_for_status()
            data = response.json()
            models = []
            for m in data.get("data", []):
                name = m.get("id", "")
                cat = "General"
                if "8b" in name.lower():
                    cat = "Lightweight"
                elif "70b" in name.lower():
                    cat = "Reasoning"

                models.append({
                    "model_id": name,
                    "name": name,
                    "context_size": m.get("context_window", 8192),
                    "category": cat,
                    "availability": "AVAILABLE"
                })
            self.status = "AVAILABLE"
            return models
        except Exception as e:
            self.handle_error(e)
            return []

    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.client.get(f"{self.BASE_URL}/models/{model_id}", headers=self._headers())
            response.raise_for_status()
            m = response.json()
            return {
                "model_id": m.get("id"),
                "name": m.get("id"),
                "context_size": m.get("context_window", 8192)
            }
        except Exception as e:
            self.handle_error(e)
            return None

    def generate(self, model_id: str, prompt: str, system_prompt: str = "", context: str = "", max_tokens: int = 1024) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        user_content = prompt
        if context:
            user_content = f"Context:\n{context}\n\nUser Request:\n{prompt}"
            
        messages.append({"role": "user", "content": user_content})
        
        payload = {
            "model": model_id,
            "messages": messages,
            "max_tokens": max_tokens
        }
        
        try:
            response = self.client.post(f"{self.BASE_URL}/chat/completions", headers=self._headers(), json=payload)
            response.raise_for_status()
            data = response.json()
            
            choices = data.get("choices", [])
            if not choices:
                return ""
                
            text = choices[0].get("message", {}).get("content") or ""
            self.status = "AVAILABLE"
            return text
        except Exception as e:
            self.handle_error(e)
            raise e
