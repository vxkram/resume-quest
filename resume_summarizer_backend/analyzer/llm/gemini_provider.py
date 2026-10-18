import httpx
from google import genai
from google.genai import errors, types

from .base import Provider, ProviderError, ProviderInfo, parse_json


def _translate(exc):
    if isinstance(exc, errors.ClientError):
        if exc.code in (401, 403) or "API_KEY_INVALID" in str(exc):
            return ProviderError("invalid_key")
        if exc.code == 429:
            # Free-tier keys get 429 RESOURCE_EXHAUSTED once the daily quota is used up.
            return ProviderError("no_credits" if "quota" in str(exc).lower() else "rate_limited")
        if exc.code == 404:
            return ProviderError("model_not_found")
    if isinstance(exc, httpx.HTTPError):
        return ProviderError("unreachable")
    return ProviderError("provider_error")


class GeminiProvider(Provider):
    info = ProviderInfo("gemini", "Google Gemini", True, "gemini-2.5-flash", "AIza…")

    def complete_json(self, *, system, prompt, schema, schema_name, api_key, model):
        try:
            with genai.Client(api_key=api_key) as client:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system,
                        response_mime_type="application/json",
                        response_json_schema=schema,
                    ),
                )
                text = response.text
        except (errors.APIError, httpx.HTTPError) as exc:
            raise _translate(exc) from None
        return parse_json(text)

    def list_models(self, *, api_key):
        try:
            with genai.Client(api_key=api_key) as client:
                models = list(client.models.list())
        except (errors.APIError, httpx.HTTPError) as exc:
            raise _translate(exc) from None
        return sorted(
            m.name.removeprefix("models/")
            for m in models
            if "generateContent" in (m.supported_actions or []) and "gemini" in m.name
        )
