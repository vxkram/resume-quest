"""Free-tier providers that speak OpenAI's chat-completions API: Groq and OpenRouter.

They reuse the OpenAI SDK pointed at another base URL. Only the URL and the
model list come from here; the key is the user's, sent per request as always.
"""

import json

import openai

from .base import Provider, ProviderError, ProviderInfo, parse_json
from .openai_provider import translate_openai_error


class ChatCompletionsProvider(Provider):
    base_url = ""
    extra_body = None

    def strict_schema(self, model):
        """Whether this model enforces a JSON schema. Others get plain JSON mode."""
        return True

    def _client(self, api_key):
        return openai.OpenAI(api_key=api_key, base_url=self.base_url, max_retries=1, timeout=300)

    def complete_json(self, *, system, prompt, schema, schema_name, api_key, model):
        if self.strict_schema(model):
            response_format = {"type": "json_schema",
                               "json_schema": {"name": schema_name, "schema": schema, "strict": True}}
        else:
            # JSON mode guarantees valid JSON but not its shape, so spell the schema out.
            response_format = {"type": "json_object"}
            system = f"{system}\n\nReturn one JSON object that follows this JSON Schema:\n{json.dumps(schema)}"
        try:
            with self._client(api_key) as client:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                    response_format=response_format,
                    extra_body=self.extra_body,
                )
        except openai.OpenAIError as exc:
            raise translate_openai_error(exc) from None
        if not response.choices:
            raise ProviderError("provider_error")
        choice = response.choices[0]
        if choice.finish_reason == "length":
            raise ProviderError("bad_output")
        return parse_json(choice.message.content)

    def list_models(self, *, api_key):
        try:
            with self._client(api_key) as client:
                ids = [m.id for m in client.models.list()]
        except openai.OpenAIError as exc:
            raise translate_openai_error(exc) from None
        return sorted(i for i in ids if self.usable(i))

    def usable(self, model_id):
        return True


class GroqProvider(ChatCompletionsProvider):
    info = ProviderInfo("groq", "Groq", True, "openai/gpt-oss-120b", "gsk_…",
                        free_tier=True, key_url="https://console.groq.com/keys")
    base_url = "https://api.groq.com/openai/v1"

    def strict_schema(self, model):
        # Groq enforces schemas (strict mode) on its gpt-oss models; see
        # https://console.groq.com/docs/structured-outputs
        return model.startswith("openai/gpt-oss")

    def usable(self, model_id):
        return not any(s in model_id for s in ("whisper", "tts", "guard", "orpheus", "playai", "safeguard"))


class OpenRouterProvider(ChatCompletionsProvider):
    # "openrouter/free" routes to a free model that supports the features the
    # request needs, structured outputs included.
    info = ProviderInfo("openrouter", "OpenRouter", True, "openrouter/free", "sk-or-…",
                        free_tier=True, key_url="https://openrouter.ai/keys")
    base_url = "https://openrouter.ai/api/v1"
    # Only route to upstream providers that honour response_format.
    extra_body = {"provider": {"require_parameters": True}}

    def usable(self, model_id):
        free = model_id.endswith(":free") or model_id == "openrouter/free"
        return free and "safety" not in model_id  # classifiers can't write JSON answers
