import httpx

class LLMModelWrapper:
    def __init__(self, model: str, base_url: str):
        self.model = model
        self.base_url = base_url

    def generate(self, prompt: str) -> str:
        """Non-streaming LLM call returning full text"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        try:
            response = httpx.post(self.base_url, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        except Exception as e:
            return f"[LLMModelWrapper ERROR] {str(e)}"
