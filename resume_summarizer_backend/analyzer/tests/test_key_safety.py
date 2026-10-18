"""Proof that a pasted API key goes to the provider and nowhere else.

A sentinel key is pushed through every endpoint with the OpenAI SDK mocked out,
then we look for it in every response, every database row, every log line and
every file written under the project during the test.
"""

import io
import json
import logging
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import openai
import pytest
from django.db import connection
from django.test import RequestFactory
from django.views.debug import ExceptionReporter

from analyzer.llm.fake_provider import FakeProvider
from analyzer.security import (RedactKeysFilter, mask_key, read_api_key, redact)

# Built at runtime so the value never appears in source code that a traceback might print.
SENTINEL = "sk-proj-" + "".join(chr(ord("a") + (i * 7) % 26) for i in range(40)) + "wxyz"
MARK = SENTINEL[8:32]  # a chunk no legitimate output would contain
PROJECT = Path(__file__).resolve().parents[3]
SKIP_DIRS = {".venv", "node_modules", ".git", "__pycache__", ".pytest_cache"}

pytestmark = pytest.mark.django_db


@pytest.fixture
def mocked_openai(monkeypatch):
    """OpenAI SDK replaced by the fake provider's answers. Records the key it was given."""
    seen_keys = []

    def make_client(api_key, **_):
        seen_keys.append(api_key)
        client = MagicMock()
        client.__enter__ = MagicMock(return_value=client)
        client.__exit__ = MagicMock(return_value=False)

        def create(model, instructions, input, text):
            answer = FakeProvider().complete_json(
                system=instructions, prompt=input, schema=None,
                schema_name=text["format"]["name"], api_key="", model=model)
            return SimpleNamespace(output_text=json.dumps(answer))

        client.responses.create.side_effect = create
        client.models.list.return_value = [SimpleNamespace(id="gpt-5-mini")]
        return client

    monkeypatch.setattr(openai, "OpenAI", make_client)
    return seen_keys


@pytest.fixture
def console_log():
    """What the app's configured console log handler writes, captured as text."""
    handler = next(h for h in logging.getLogger().handlers
                   if any(isinstance(f, RedactKeysFilter) for f in h.filters))
    buffer = io.StringIO()
    original = handler.setStream(buffer)
    yield buffer
    handler.setStream(original)


def keyed(api):
    return {"X-LLM-Key": SENTINEL}


def all_database_text():
    chunks = []
    with connection.cursor() as cursor:
        for table in connection.introspection.table_names(cursor):
            cursor.execute(f'SELECT * FROM "{table}"')
            chunks.append(repr(cursor.fetchall()))
    return "\n".join(chunks)


def files_changed_since(start):
    for path in PROJECT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts) or not path.is_file():
            continue
        if path.stat().st_mtime >= start:
            yield path


def test_sentinel_key_reaches_the_provider_and_nothing_else(api, upload, mocked_openai, console_log, capfd):
    start = time.time() - 1
    bodies = []

    def record(response):
        bodies.append(response.content.decode() + repr(dict(response.headers)))
        return response

    created = record(upload(provider="openai", headers=keyed(api))).json()
    analysis_id = created["id"]
    quiz = record(api.post(f"/api/analyses/{analysis_id}/quiz/", {"provider": "openai"},
                           content_type="application/json", headers=keyed(api))).json()
    record(api.post(f"/api/quizzes/{quiz['id']}/submit/", {"answers": [0] * len(quiz["questions"])},
                    content_type="application/json"))
    record(api.post(f"/api/analyses/{analysis_id}/interview/", {"provider": "openai"},
                    content_type="application/json", headers=keyed(api)))
    record(api.get("/api/providers/openai/models/", headers=keyed(api)))
    record(api.get(f"/api/analyses/{analysis_id}/"))
    record(api.get("/api/analyses/"))

    # The key did reach the provider SDK, once per call...
    assert mocked_openai == [SENTINEL] * 4
    # ...and nowhere else.
    for body in bodies:
        assert SENTINEL not in body
        assert MARK not in body
    assert MARK not in all_database_text()
    out, err = capfd.readouterr()
    assert MARK not in out + err + console_log.getvalue()
    for path in files_changed_since(start):
        assert MARK.encode() not in path.read_bytes(), f"key written to {path}"


def test_provider_error_quoting_the_key_is_not_echoed(api, upload, monkeypatch, console_log):
    client = MagicMock()
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)
    client.responses.create.side_effect = openai.AuthenticationError(
        f"Incorrect API key provided: {SENTINEL}",
        response=httpx.Response(401, request=httpx.Request("POST", "https://api.openai.com")),
        body=None)
    monkeypatch.setattr(openai, "OpenAI", lambda **_: client)

    response = upload(provider="openai", headers=keyed(api))
    assert response.status_code == 401
    assert response.json() == {"error": "invalid_key", "detail": "The provider rejected the API key."}
    assert MARK not in console_log.getvalue()


def test_unexpected_crash_mentioning_the_key_is_redacted_in_logs(api, upload, monkeypatch, console_log):
    def explode(**_):
        raise RuntimeError(f"socket died while sending Authorization: Bearer {SENTINEL}")

    monkeypatch.setattr(openai, "OpenAI", explode)
    response = upload(provider="openai", headers=keyed(api))
    assert response.status_code == 500
    assert response.json() == {"error": "server_error", "detail": "Something went wrong."}
    logged = console_log.getvalue()
    assert "RuntimeError" in logged and "Traceback" in logged  # it was logged in full...
    assert MARK not in logged  # ...but the key was scrubbed
    assert "[REDACTED]" in logged


def test_keyless_provider_never_forwards_a_key(api, upload, monkeypatch):
    post = MagicMock(return_value=httpx.Response(200, json={"message": {"content": json.dumps(
        FakeProvider().complete_json(system="", prompt="<resume>\nPython\n</resume>", schema=None,
                                     schema_name="analysis", api_key="", model=""))}}))
    monkeypatch.setattr(httpx, "post", post)
    response = upload(provider="ollama", headers=keyed(api))
    assert response.status_code == 201
    assert MARK not in repr(post.call_args_list)


@pytest.mark.parametrize("bad", ["has space", "x" * 600, "ключ", "tab\tkey"])
def test_malformed_keys_are_rejected_without_echo(api, upload, bad):
    response = upload(provider="openai", headers={"X-LLM-Key": bad})
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_key"
    assert bad not in response.content.decode()


def test_django_error_report_hides_the_key(settings):
    settings.DEBUG = True
    request = RequestFactory().post("/api/analyses/", HTTP_X_LLM_KEY=SENTINEL)

    def view_that_crashes(request):
        api_key = read_api_key(request)  # noqa: F841 - must not show in the report's locals
        raise ValueError("boom")

    try:
        view_that_crashes(request)
    except ValueError:
        report = ExceptionReporter(request, *sys.exc_info())
        assert MARK not in report.get_traceback_html()
        assert MARK not in report.get_traceback_text()


def test_redact_patterns():
    assert redact(f"key={SENTINEL}") == "key=[REDACTED]"
    assert "sk-ant-api03" not in redact("sk-ant-api03-abcdefghijklmnopqrstuvwxyz")
    assert "AIzaSy" not in redact("AIzaSyA1234567890abcdefghijklmnopqrs")
    assert "gsk_" not in redact("gsk_abcdefghijklmnopqrstuvwxyz0123")
    assert "sk-or-v1" not in redact("sk-or-v1-0123456789abcdef0123456789")
    assert redact('{"x-api-key": "whatever-123"}') == '{"x-api-key": "[REDACTED]"}'
    assert redact("nothing secret here") == "nothing secret here"


def test_registered_keys_are_redacted_whatever_their_shape():
    request = RequestFactory().get("/", HTTP_X_LLM_KEY="plainweirdkey42")
    read_api_key(request)
    assert redact("the key is plainweirdkey42") == "the key is [REDACTED]"


def test_log_filter_scrubs_message_args_and_tracebacks():
    try:
        raise RuntimeError(SENTINEL)
    except RuntimeError:
        record = logging.LogRecord("x", logging.ERROR, __file__, 1, "using %s", (SENTINEL,), sys.exc_info())
    RedactKeysFilter().filter(record)
    formatted = logging.Formatter().format(record)
    assert MARK not in formatted and "[REDACTED]" in formatted


def test_mask_key():
    assert mask_key(SENTINEL) == "…wxyz"
    assert mask_key("short") == "…"
    assert mask_key("") == ""
