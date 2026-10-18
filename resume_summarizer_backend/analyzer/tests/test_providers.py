"""Each adapter, with the vendor SDK replaced by a mock: right call shape, safe errors."""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import anthropic
import httpx
import openai
import pytest
from google.genai import errors as genai_errors

from analyzer.llm import call_structured
from analyzer.llm.anthropic_provider import AnthropicProvider
from analyzer.llm.base import ProviderError, parse_json
from analyzer.llm.gemini_provider import GeminiProvider
from analyzer.llm.ollama_provider import OllamaProvider
from analyzer.llm.openai_provider import OpenAIProvider
from analyzer.schemas import QUIZ_SCHEMA, QuizOut

ANSWER = {"questions": [
    {"skill": "Python", "difficulty": "easy", "question": f"Question {i}?",
     "options": ["a", "b", "c", "d"], "answer_index": 1, "explanation": "b."}
    for i in range(4)
]}
CALL = dict(system="sys", prompt="prompt", schema=QUIZ_SCHEMA, schema_name="quiz",
            api_key="sk-test-key-123456789", model="m")


def fake_response(status, url="https://api.example.com"):
    return httpx.Response(status, request=httpx.Request("POST", url))


def mock_client(monkeypatch, module, attr, client):
    factory = MagicMock(return_value=client)
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)
    monkeypatch.setattr(module, attr, factory)
    return factory


# --- OpenAI -----------------------------------------------------------------

def test_openai_uses_strict_json_schema(monkeypatch):
    client = MagicMock()
    client.responses.create.return_value = SimpleNamespace(output_text=json.dumps(ANSWER))
    factory = mock_client(monkeypatch, openai, "OpenAI", client)

    assert OpenAIProvider().complete_json(**CALL) == ANSWER
    assert factory.call_args.kwargs["api_key"] == "sk-test-key-123456789"
    kwargs = client.responses.create.call_args.kwargs
    assert kwargs["model"] == "m" and kwargs["instructions"] == "sys"
    assert kwargs["text"]["format"] == {"type": "json_schema", "name": "quiz",
                                        "schema": QUIZ_SCHEMA, "strict": True}


@pytest.mark.parametrize("exc, code", [
    (openai.AuthenticationError("bad key sk-test-key-123456789", response=fake_response(401), body=None), "invalid_key"),
    (openai.RateLimitError("slow down", response=fake_response(429), body=None), "rate_limited"),
    (openai.NotFoundError("no model", response=fake_response(404), body=None), "model_not_found"),
    (openai.APIConnectionError(request=httpx.Request("POST", "https://x")), "unreachable"),
    (openai.InternalServerError("boom", response=fake_response(500), body=None), "provider_error"),
])
def test_openai_errors_are_translated(monkeypatch, exc, code):
    client = MagicMock()
    client.responses.create.side_effect = exc
    mock_client(monkeypatch, openai, "OpenAI", client)
    with pytest.raises(ProviderError) as raised:
        OpenAIProvider().complete_json(**CALL)
    assert raised.value.code == code
    assert raised.value.__cause__ is None  # the SDK error (and its message) is not chained
    assert "sk-test" not in raised.value.public_message


def test_openai_model_list_filters_non_chat_models(monkeypatch):
    client = MagicMock()
    client.models.list.return_value = [SimpleNamespace(id=i) for i in
                                       ["gpt-5-mini", "text-embedding-3-small", "o4-mini", "dall-e-3", "gpt-image-1"]]
    mock_client(monkeypatch, openai, "OpenAI", client)
    assert OpenAIProvider().list_models(api_key="k") == ["gpt-5-mini", "o4-mini"]


# --- Anthropic --------------------------------------------------------------

def anthropic_message(text, stop_reason="end_turn"):
    return SimpleNamespace(stop_reason=stop_reason, content=[
        SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=text)])


def test_anthropic_uses_output_config_json_schema(monkeypatch):
    client = MagicMock()
    client.messages.create.return_value = anthropic_message(json.dumps(ANSWER))
    factory = mock_client(monkeypatch, anthropic, "Anthropic", client)

    assert AnthropicProvider().complete_json(**{**CALL, "model": "claude-haiku-5-5"}) == ANSWER
    assert factory.call_args.kwargs["api_key"] == "sk-test-key-123456789"
    kwargs = client.messages.create.call_args.kwargs
    assert kwargs["output_config"] == {"format": {"type": "json_schema", "schema": QUIZ_SCHEMA}}
    assert kwargs["system"] == "sys" and kwargs["messages"] == [{"role": "user", "content": "prompt"}]


def test_anthropic_opus_gets_server_side_refusal_fallback(monkeypatch):
    client = MagicMock()
    client.beta.messages.create.return_value = anthropic_message(json.dumps(ANSWER))
    mock_client(monkeypatch, anthropic, "Anthropic", client)

    AnthropicProvider().complete_json(**{**CALL, "model": "claude-opus-5-5"})
    kwargs = client.beta.messages.create.call_args.kwargs
    assert kwargs["betas"] == ["server-side-fallback-2026-07-01"]
    assert kwargs["fallbacks"] == "default"
    client.messages.create.assert_not_called()


@pytest.mark.parametrize("stop_reason, code", [("refusal", "refused"), ("max_tokens", "bad_output")])
def test_anthropic_stop_reasons(monkeypatch, stop_reason, code):
    client = MagicMock()
    client.messages.create.return_value = anthropic_message("{}", stop_reason)
    mock_client(monkeypatch, anthropic, "Anthropic", client)
    with pytest.raises(ProviderError) as raised:
        AnthropicProvider().complete_json(**{**CALL, "model": "claude-haiku-5-5"})
    assert raised.value.code == code


def test_anthropic_bad_key(monkeypatch):
    client = MagicMock()
    client.messages.create.side_effect = anthropic.AuthenticationError(
        "invalid x-api-key", response=fake_response(401), body=None)
    mock_client(monkeypatch, anthropic, "Anthropic", client)
    with pytest.raises(ProviderError) as raised:
        AnthropicProvider().complete_json(**{**CALL, "model": "claude-haiku-5-5"})
    assert raised.value.code == "invalid_key" and raised.value.status == 401


# --- Gemini -----------------------------------------------------------------

def test_gemini_uses_response_json_schema(monkeypatch):
    from google import genai

    client = MagicMock()
    client.models.generate_content.return_value = SimpleNamespace(text=json.dumps(ANSWER))
    factory = mock_client(monkeypatch, genai, "Client", client)

    assert GeminiProvider().complete_json(**CALL) == ANSWER
    assert factory.call_args.kwargs["api_key"] == "sk-test-key-123456789"
    config = client.models.generate_content.call_args.kwargs["config"]
    assert config.response_mime_type == "application/json"
    assert config.response_json_schema == QUIZ_SCHEMA
    assert config.system_instruction == "sys"


@pytest.mark.parametrize("code, message, expected", [
    (400, "API key not valid. API_KEY_INVALID", "invalid_key"),
    (403, "forbidden", "invalid_key"),
    (429, "quota", "rate_limited"),
    (404, "no such model", "model_not_found"),
])
def test_gemini_errors(monkeypatch, code, message, expected):
    from google import genai

    client = MagicMock()
    client.models.generate_content.side_effect = genai_errors.ClientError(
        code, {"error": {"message": message, "status": "X"}})
    mock_client(monkeypatch, genai, "Client", client)
    with pytest.raises(ProviderError) as raised:
        GeminiProvider().complete_json(**CALL)
    assert raised.value.code == expected


# --- Ollama -----------------------------------------------------------------

def test_ollama_posts_schema_to_local_server(monkeypatch, settings):
    settings.OLLAMA_URL = "http://127.0.0.1:11434"
    post = MagicMock(return_value=httpx.Response(200, json={"message": {"content": json.dumps(ANSWER)}}))
    monkeypatch.setattr(httpx, "post", post)

    assert OllamaProvider().complete_json(**{**CALL, "api_key": ""}) == ANSWER
    url = post.call_args.args[0]
    body = post.call_args.kwargs["json"]
    assert url == "http://127.0.0.1:11434/api/chat"
    assert body["format"] == QUIZ_SCHEMA and body["stream"] is False and body["think"] is False


def test_ollama_retries_without_think_for_models_that_lack_it(monkeypatch):
    responses = [httpx.Response(400, json={"error": '"m" does not support thinking'}),
                 httpx.Response(200, json={"message": {"content": json.dumps(ANSWER)}})]
    post = MagicMock(side_effect=responses)
    monkeypatch.setattr(httpx, "post", post)
    assert OllamaProvider().complete_json(**{**CALL, "api_key": ""}) == ANSWER
    assert "think" not in post.call_args_list[1].kwargs["json"]


@pytest.mark.parametrize("effect, code", [
    (httpx.ConnectError("refused"), "unreachable"),
    (httpx.Response(404, json={"error": "model not found"}), "model_not_found"),
    (httpx.Response(500, json={"error": "oom"}), "provider_error"),
])
def test_ollama_errors(monkeypatch, effect, code):
    monkeypatch.setattr(httpx, "post", MagicMock(side_effect=[effect]))
    with pytest.raises(ProviderError) as raised:
        OllamaProvider().complete_json(**{**CALL, "api_key": ""})
    assert raised.value.code == code


def test_ollama_model_list_skips_image_models(monkeypatch):
    monkeypatch.setattr(httpx, "get", MagicMock(return_value=httpx.Response(
        200, json={"models": [{"name": "qwen3.5:4b"}, {"name": "x/flux2-klein:4b-fp8"}, {"name": "llama3.2:1b"}]},
        request=httpx.Request("GET", "http://x"))))
    assert OllamaProvider().list_models(api_key="") == ["llama3.2:1b", "qwen3.5:4b"]


# --- shared -----------------------------------------------------------------

def test_parse_json_handles_fences_and_rejects_junk():
    assert parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    for junk in ["", "nope", "[1, 2]", None]:
        with pytest.raises(ProviderError):
            parse_json(junk)


def test_call_structured_retries_once_then_gives_up():
    provider = MagicMock()
    provider.info.id = "x"
    provider.complete_json.side_effect = [{"questions": []}, ANSWER]
    result = call_structured(provider, model_cls=QuizOut, **CALL)
    assert len(result.questions) == 4 and provider.complete_json.call_count == 2

    provider.complete_json.reset_mock(side_effect=True)
    provider.complete_json.side_effect = ProviderError("bad_output")
    with pytest.raises(ProviderError) as raised:
        call_structured(provider, model_cls=QuizOut, **CALL)
    assert raised.value.code == "bad_output" and provider.complete_json.call_count == 2


def test_call_structured_does_not_retry_auth_errors():
    provider = MagicMock()
    provider.complete_json.side_effect = ProviderError("invalid_key")
    with pytest.raises(ProviderError):
        call_structured(provider, model_cls=QuizOut, **CALL)
    assert provider.complete_json.call_count == 1


def test_quiz_validation_drops_broken_questions():
    raw = {"questions": ANSWER["questions"] + [
        {**ANSWER["questions"][0], "options": ["a", "b", "c"]},          # only 3 options
        {**ANSWER["questions"][0], "options": ["a", "a", "b", "c"]},     # duplicate option
        {**ANSWER["questions"][0], "answer_index": 7},                   # answer out of range
    ]}
    assert len(QuizOut.model_validate(raw).questions) == 4
