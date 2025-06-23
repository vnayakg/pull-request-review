import requests
import os


class LLMClient:
    def generate_review(self, prompt):
        raise NotImplementedError

    def generate_description(self, prompt):
        """Generate a PR description. By default, uses the same method as generate_review."""
        return self.generate_review(prompt)


class OllamaClient(LLMClient):
    def __init__(self, endpoint, model, temperature=0.1, max_tokens=2048):
        self.endpoint = endpoint.rstrip("/")
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
            "stream": False,
        }
        resp = requests.post(url, json=payload)
        if not resp.ok:
            raise Exception(f"Ollama API error: {resp.status_code} {resp.text}")
        data = resp.json()
        return data.get("response", "")


class OpenAIClient(LLMClient):
    def __init__(self, api_key, model, temperature=0.1, max_tokens=2048, api_base=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_base = api_base or "https://api.openai.com/v1"

    def generate_review(self, prompt):
        url = f"{self.api_base}/chat/completions"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        resp = requests.post(url, headers=headers, json=payload)
        if not resp.ok:
            raise Exception(f"OpenAI API error: {resp.status_code} {resp.text}")
        data = resp.json()
        return data["choices"][0]["message"]["content"]


class GeminiClient(LLMClient):
    def __init__(self, api_key, model, temperature=0.1, max_tokens=2048, api_base=None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_base = api_base or "https://generativelanguage.googleapis.com/v1beta/models"

    def generate_review(self, prompt):
        url = f"{self.api_base}/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
            },
        }
        resp = requests.post(url, json=payload)
        if not resp.ok:
            raise Exception(f"Gemini API error: {resp.status_code} {resp.text}")
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


def get_llm_client(config):
    llm_type = config.get("llm.type", "ollama")
    if llm_type == "ollama":
        ollama_cfg = config.get("ollama")
        return OllamaClient(
            endpoint=ollama_cfg["endpoint"],
            model=ollama_cfg["model"],
            temperature=ollama_cfg.get("temperature", 0.1),
            max_tokens=ollama_cfg.get("max_tokens", 2048),
        )
    elif llm_type == "openai":
        openai_cfg = config.get("openai", {})
        return OpenAIClient(
            api_key=openai_cfg.get("api_key"),
            model=openai_cfg.get("model", "gpt-3.5-turbo"),
            temperature=openai_cfg.get("temperature", 0.1),
            max_tokens=openai_cfg.get("max_tokens", 2048),
            api_base=openai_cfg.get("api_base"),
        )
    elif llm_type == "gemini":
        gemini_cfg = config.get("gemini", {})
        return GeminiClient(
            api_key=gemini_cfg.get("api_key"),
            model=gemini_cfg.get("model", "gemini-pro"),
            temperature=gemini_cfg.get("temperature", 0.1),
            max_tokens=gemini_cfg.get("max_tokens", 2048),
            api_base=gemini_cfg.get("api_base"),
        )
    else:
        raise ValueError(f"Unknown LLM type: {llm_type}")
