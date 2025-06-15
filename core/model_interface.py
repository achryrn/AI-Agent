import requests
import json

class OllamaModel:
    def __init__(self, model_name="llama3:latest", base_url="http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")

    def generate(self, prompt: str, max_tokens: int = 512):
        url = f"{self.base_url}/api/generate"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.model_name,
            "max_tokens": max_tokens,
            "prompt": prompt,
            "stream": True  # Streaming enabled
        }

        try:
            with requests.post(url, headers=headers, json=payload, stream=True) as response:
                response.raise_for_status()
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode("utf-8"))
                            full_response += data.get("response", "")
                        except json.JSONDecodeError:
                            pass
                return full_response.strip()
        except requests.exceptions.RequestException as e:
            return f"[Error contacting Ollama API: {e}]"
