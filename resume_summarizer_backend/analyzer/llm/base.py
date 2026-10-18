"""The one interface every LLM provider implements: prompt + JSON schema in, dict out."""

import json
from dataclasses import dataclass


class ProviderError(Exception):
    """A provider failure, reduced to something safe to show the user.

    The provider's own error text is deliberately dropped: SDK messages can quote
    request details, and we never want a key or a header to reach a response.
    """

    MESSAGES = {
        "invalid_key": (401, "The provider rejected the API key."),
        "rate_limited": (429, "The provider is rate limiting this key. Try again shortly."),
        "model_not_found": (400, "That model isn't available for this key."),
        "unreachable": (503, "Couldn't reach the provider."),
        "bad_output": (502, "The model didn't return usable JSON. Try again or pick a stronger model."),
        "refused": (502, "The model declined to answer."),
        "provider_error": (502, "The provider returned an error."),
    }

    def __init__(self, code):
        if code not in self.MESSAGES:
            code = "provider_error"
        self.code = code
        self.status, self.public_message = self.MESSAGES[code]
        super().__init__(code)


@dataclass(frozen=True)
class ProviderInfo:
    id: str
    label: str
    needs_key: bool
    default_model: str
    key_hint: str = ""


class Provider:
    info: ProviderInfo

    def complete_json(self, *, system, prompt, schema, schema_name, api_key, model):
        """Return the model's answer as a dict that follows `schema`."""
        raise NotImplementedError

    def list_models(self, *, api_key):
        return []


def parse_json(text):
    """Parse a model's JSON answer, tolerating a ```json fence around it."""
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    try:
        value = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        raise ProviderError("bad_output") from None
    if not isinstance(value, dict):
        raise ProviderError("bad_output")
    return value
