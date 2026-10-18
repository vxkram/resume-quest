import anthropic

from .base import Provider, ProviderError, ProviderInfo, parse_json

# Models that accept the server-side refusal fallback (`fallbacks: "default"`).
_FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-fable-5-1", "claude-sonnet-5-5"}


def _translate(exc):
    if isinstance(exc, (anthropic.AuthenticationError, anthropic.PermissionDeniedError)):
        return ProviderError("invalid_key")
    if isinstance(exc, anthropic.RateLimitError):
        return ProviderError("rate_limited")
    if isinstance(exc, anthropic.NotFoundError):
        return ProviderError("model_not_found")
    if isinstance(exc, (anthropic.APIConnectionError, anthropic.APITimeoutError)):
        return ProviderError("unreachable")
    return ProviderError("provider_error")


class AnthropicProvider(Provider):
    info = ProviderInfo("anthropic", "Anthropic", True, "claude-opus-5-5", "sk-ant-…")

    def _client(self, api_key):
        return anthropic.Anthropic(api_key=api_key, max_retries=1, timeout=300)

    def complete_json(self, *, system, prompt, schema, schema_name, api_key, model):
        params = dict(
            model=model,
            max_tokens=16000,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )
        try:
            with self._client(api_key) as client:
                if model in _FALLBACK_MODELS:
                    response = client.beta.messages.create(
                        betas=["server-side-fallback-2026-07-01"], fallbacks="default", **params
                    )
                else:
                    response = client.messages.create(**params)
        except anthropic.AnthropicError as exc:
            raise _translate(exc) from None
        if response.stop_reason == "refusal":
            raise ProviderError("refused")
        if response.stop_reason == "max_tokens":
            raise ProviderError("bad_output")
        text = next((b.text for b in response.content if b.type == "text"), "")
        return parse_json(text)

    def list_models(self, *, api_key):
        try:
            with self._client(api_key) as client:
                return [m.id for m in client.models.list()]
        except anthropic.AnthropicError as exc:
            raise _translate(exc) from None
