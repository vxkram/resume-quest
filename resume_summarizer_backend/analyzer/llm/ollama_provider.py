import httpx
from django.conf import settings

from .base import Provider, ProviderError, ProviderInfo, parse_json


class OllamaProvider(Provider):
    """A local Ollama server. The URL comes from settings, never from the request."""

    info = ProviderInfo("ollama", "Ollama (local)", False, "qwen3.5:4b")

    def complete_json(self, *, system, prompt, schema, schema_name, api_key, model):
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "format": schema,
            "stream": False,
            "think": False,
            "options": {"temperature": 0.2, "num_ctx": 16384},
        }
        try:
            response = httpx.post(f"{settings.OLLAMA_URL}/api/chat", json=body, timeout=900)
        except httpx.HTTPError:
            raise ProviderError("unreachable") from None
        if response.status_code == 404:
            raise ProviderError("model_not_found")
        if response.status_code == 400 and "think" in response.text:
            # Model without a thinking switch: ask again without it.
            body.pop("think")
            try:
                response = httpx.post(f"{settings.OLLAMA_URL}/api/chat", json=body, timeout=900)
            except httpx.HTTPError:
                raise ProviderError("unreachable") from None
        if response.status_code != 200:
            raise ProviderError("provider_error")
        return parse_json(response.json().get("message", {}).get("content", ""))

    def list_models(self, *, api_key):
        try:
            response = httpx.get(f"{settings.OLLAMA_URL}/api/tags", timeout=5)
            response.raise_for_status()
        except httpx.HTTPError:
            raise ProviderError("unreachable") from None
        names = [m["name"] for m in response.json().get("models", [])]
        # Skip image-generation and embedding models; they can't answer a chat prompt.
        return sorted(n for n in names if not any(s in n for s in ("flux", "embed", "diffusion")))
