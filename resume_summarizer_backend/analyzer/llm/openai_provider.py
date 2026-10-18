import openai

from .base import Provider, ProviderError, ProviderInfo, parse_json

# Model families that can't answer a JSON chat prompt.
_SKIP = ("embedding", "tts", "whisper", "dall-e", "image", "audio", "realtime",
         "transcribe", "moderation", "search", "computer-use", "codex")


def _translate(exc):
    if isinstance(exc, (openai.AuthenticationError, openai.PermissionDeniedError)):
        return ProviderError("invalid_key")
    if isinstance(exc, openai.RateLimitError):
        return ProviderError("rate_limited")
    if isinstance(exc, openai.NotFoundError):
        return ProviderError("model_not_found")
    if isinstance(exc, (openai.APIConnectionError, openai.APITimeoutError)):
        return ProviderError("unreachable")
    return ProviderError("provider_error")


class OpenAIProvider(Provider):
    info = ProviderInfo("openai", "OpenAI", True, "gpt-5-mini", "sk-…")

    def _client(self, api_key):
        return openai.OpenAI(api_key=api_key, max_retries=1, timeout=180)

    def complete_json(self, *, system, prompt, schema, schema_name, api_key, model):
        try:
            with self._client(api_key) as client:
                response = client.responses.create(
                    model=model,
                    instructions=system,
                    input=prompt,
                    text={"format": {"type": "json_schema", "name": schema_name,
                                     "schema": schema, "strict": True}},
                )
        except openai.OpenAIError as exc:
            raise _translate(exc) from None
        return parse_json(response.output_text)

    def list_models(self, *, api_key):
        try:
            with self._client(api_key) as client:
                ids = [m.id for m in client.models.list()]
        except openai.OpenAIError as exc:
            raise _translate(exc) from None
        return sorted(i for i in ids if i.startswith(("gpt", "o")) and not any(s in i for s in _SKIP))
