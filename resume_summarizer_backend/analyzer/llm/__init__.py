"""Provider registry and the one call the rest of the app uses."""

import logging

from django.conf import settings
from pydantic import ValidationError

from .anthropic_provider import AnthropicProvider
from .base import ProviderError
from .compatible_providers import GroqProvider, OpenRouterProvider
from .fake_provider import FakeProvider
from .gemini_provider import GeminiProvider
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)

_PROVIDERS = {p.info.id: p for p in (
    OpenAIProvider(), AnthropicProvider(), GeminiProvider(), GroqProvider(), OpenRouterProvider(), OllamaProvider(),
)}
_FAKE = FakeProvider()


def available_providers():
    providers = list(_PROVIDERS.values())
    if settings.ENABLE_FAKE_PROVIDER:
        providers.append(_FAKE)
    return providers


def get_provider(provider_id):
    for provider in available_providers():
        if provider.info.id == provider_id:
            return provider
    return None


def call_structured(provider, *, system, prompt, schema, schema_name, model_cls, api_key, model):
    """Ask for JSON, validate it, and retry once if the model fumbles the format."""
    for attempt in (1, 2):
        try:
            raw = provider.complete_json(
                system=system, prompt=prompt, schema=schema,
                schema_name=schema_name, api_key=api_key, model=model,
            )
            return model_cls.model_validate(raw)
        except ValidationError as exc:
            logger.warning("%s/%s returned invalid %s (attempt %d): %d errors",
                           provider.info.id, model, schema_name, attempt, exc.error_count())
        except ProviderError as exc:
            if exc.code != "bad_output":
                raise
            logger.warning("%s/%s returned unparseable %s (attempt %d)",
                           provider.info.id, model, schema_name, attempt)
    raise ProviderError("bad_output")
