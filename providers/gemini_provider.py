from typing import List, Dict, Any, Optional
from providers.base import AIProvider

class GeminiProvider(AIProvider):
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def test_key(self) -> bool:
        try:
            response = self.client.get(f"{self.BASE_URL}?key={self.api_key}")
            response.raise_for_status()
            self.status = "AVAILABLE"
            return True
        except Exception as e:
            self.handle_error(e)
            return False

    def discover_models(self) -> List[Dict[str, Any]]:
        try:
            response = self.client.get(f"{self.BASE_URL}?key={self.api_key}")
            response.raise_for_status()
            data = response.json()
            models = []
            for m in data.get("models", []):
                if "generateContent" in m.get("supportedGenerationMethods", []):
                    name = m.get("name", "").split("/")[-1]
                    cat = "General"
                    if "flash" in name.lower():
                        cat = "Lightweight"
                    elif "pro" in name.lower():
                        cat = "Reasoning"
                    
                    models.append({
                        "model_id": name,
                        "name": m.get("displayName", name),
                        "context_size": m.get("inputTokenLimit", 32768),
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
            response = self.client.get(f"{self.BASE_URL}/{model_id}?key={self.api_key}")
            response.raise_for_status()
            m = response.json()
            return {
                "model_id": model_id,
                "name": m.get("displayName", model_id),
                "context_size": m.get("inputTokenLimit", 32768)
            }
        except Exception as e:
            self.handle_error(e)
            return None

    def generate(self, model_id: str, prompt: str, system_prompt: str = "", context: str = "", max_tokens: int = 1024) -> str:
        url = f"{self.BASE_URL}/{model_id}:generateContent?key={self.api_key}"
        
        full_prompt = prompt
        if context:
            full_prompt = f"Context:\n{context}\n\nUser Request:\n{prompt}"
            
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens}
        }
        
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
            
        try:
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            candidates = data.get("candidates", [])
            if not candidates:
                return ""
            
            content = candidates[0].get("content")
            if not content:
                return ""
            
            parts = content.get("parts", [])
            text = "".join([p.get("text", "") for p in parts])
            self.status = "AVAILABLE"
            return text
        except Exception as e:
            self.handle_error(e)
            raise e
