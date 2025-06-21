import requests

class OllamaClient:
    def __init__(self, endpoint, model, temperature=0.1, max_tokens=2048):
        self.endpoint = endpoint.rstrip('/')
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate_review(self, prompt):
        url = f"{self.endpoint}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": False
        }
        resp = requests.post(url, json=payload)
        if not resp.ok:
            raise Exception(f"Ollama API error: {resp.status_code} {resp.text}")
        data = resp.json()
        return data.get('response', '') 