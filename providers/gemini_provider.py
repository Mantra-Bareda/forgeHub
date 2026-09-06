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
                    ctx = m.get("inputTokenLimit")
                    if ctx is None:
                        ctx = 32768
                    else:
                        ctx = int(ctx)
                        
                    if ctx >= 128000:
                        cat = "Large Context"
                    elif "ultra" in name.lower() or "pro" in name.lower():
                        cat = "Professional Writing"
                    elif "flash" in name.lower():
                        cat = "Lightweight"
                    else:
                        cat = "Reasoning"
                    
                    models.append({
                        "model_id": name,
                        "name": m.get("displayName", name),
                        "context_size": ctx,
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
            if "1.5" in model_id.lower() or "gemini-2" in model_id.lower() or "exp" in model_id.lower():
                payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
            else:
                # Fallback for Gemini 1.0 Pro which does not support systemInstruction
                full_prompt = f"System Instructions:\n{system_prompt}\n\n{full_prompt}"
                payload["contents"][0]["parts"][0]["text"] = full_prompt
            
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
