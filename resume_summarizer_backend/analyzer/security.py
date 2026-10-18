"""Everything that keeps a user's LLM API key from leaking.

The key's lifetime is one request: the browser sends it in the X-LLM-Key header,
`read_api_key` registers it for redaction, it is handed to the provider SDK, and
the middleware forgets it when the response goes out. It is never written to the
database, a file, a cache or a log line, and no error message ever echoes it.
"""

import contextvars
import logging
import re

from django.http import JsonResponse
from django.views.debug import SafeExceptionReporterFilter
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler as drf_exception_handler

from .llm.base import ProviderError

logger = logging.getLogger(__name__)

KEY_HEADER = "HTTP_X_LLM_KEY"
# Every state-changing API call must carry this header. Browsers won't let
# another site add a custom header to a cross-origin request without a CORS
# preflight, and this server answers no preflights, so forged requests die here.
CLIENT_HEADER = "HTTP_X_RESUME_QUEST"
MAX_KEY_LENGTH = 512
REDACTED = "[REDACTED]"

# Shapes of real provider keys, caught even if they were never registered.
KEY_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
    re.compile(r"(?i)(x-llm-key|authorization|x-api-key|x-goog-api-key)(['\"]?\s*[:=]\s*['\"]?)([^\s'\",}]+)"),
]

_active_keys: contextvars.ContextVar[frozenset] = contextvars.ContextVar(
    "active_keys", default=frozenset()
)


def redact(text):
    if not isinstance(text, str) or not text:
        return text
    for key in _active_keys.get():
        text = text.replace(key, REDACTED)
    for pattern in KEY_PATTERNS:
        if pattern.groups == 3:
            text = pattern.sub(lambda m: m.group(1) + m.group(2) + REDACTED, text)
        else:
            text = pattern.sub(REDACTED, text)
    return text


class InvalidKey(APIException):
    status_code = 400
    default_detail = "The API key looks malformed."
    default_code = "invalid_key"


def read_api_key(request, required=True):
    """Return the key from the X-LLM-Key header and register it for redaction."""
    key = request.META.get(KEY_HEADER, "").strip()
    if not key:
        if required:
            raise InvalidKey("This provider needs an API key.")
        return ""
    if len(key) > MAX_KEY_LENGTH or not key.isascii() or not key.isprintable() or " " in key:
        raise InvalidKey()
    _active_keys.set(_active_keys.get() | {key})
    return key


def mask_key(key):
    """What the UI may show of a key: never more than the last four characters."""
    if not key:
        return ""
    return f"…{key[-4:]}" if len(key) > 12 else "…"


class RedactKeysFilter(logging.Filter):
    """Scrubs keys out of every log record before a handler writes it."""

    def filter(self, record):
        record.msg = redact(record.getMessage())
        record.args = ()
        if record.exc_info:
            record.exc_text = redact(logging.Formatter().formatException(record.exc_info))
            record.exc_info = None
        if record.stack_info:
            record.stack_info = redact(record.stack_info)
        return True


class KeyRedactingReporterFilter(SafeExceptionReporterFilter):
    """Django's error pages and error emails: hide keys in headers and locals."""

    hidden_settings = re.compile(
        "API|AUTH|TOKEN|KEY|SECRET|PASS|SIGNATURE|HTTP_COOKIE", flags=re.I
    )

    def get_safe_request_meta(self, request):
        meta = super().get_safe_request_meta(request)
        meta[KEY_HEADER] = self.cleansed_substitute if KEY_HEADER in meta else None
        return {k: v for k, v in meta.items() if v is not None}

    def get_traceback_frame_variables(self, request, tb_frame):
        cleansed = []
        for name, value in super().get_traceback_frame_variables(request, tb_frame):
            if self.hidden_settings.search(name) or redact(repr(value)) != repr(value):
                value = self.cleansed_substitute
            cleansed.append((name, value))
        return cleansed


class SecurityHeadersMiddleware:
    """CSP and friends on every response, no-store on the API, key cleanup."""

    CSP = "; ".join(
        [
            "default-src 'self'",
            "script-src 'self'",
            "style-src 'self'",
            "img-src 'self' data:",
            "font-src 'self'",
            "connect-src 'self'",
            "object-src 'none'",
            "base-uri 'none'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ]
    )
    UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = _active_keys.set(frozenset())
        try:
            is_api = request.path.startswith("/api/")
            if is_api and request.method in self.UNSAFE_METHODS and request.META.get(CLIENT_HEADER) != "1":
                response = JsonResponse(
                    {"error": "forbidden", "detail": "Missing X-Resume-Quest header."}, status=403
                )
            else:
                response = self.get_response(request)
        finally:
            _active_keys.reset(token)
        response["Content-Security-Policy"] = self.CSP
        response["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
        response["Cross-Origin-Resource-Policy"] = "same-origin"
        if is_api:
            response["Cache-Control"] = "no-store"
        return response


def _first_message(data):
    """DRF error data ({"field": ["msg"]}, ["msg"], "msg") reduced to one readable string."""
    while isinstance(data, (dict, list)) and data:
        data = data.get("detail", next(iter(data.values()))) if isinstance(data, dict) else data[0]
    return str(data or "Invalid request.")


def exception_handler(exc, context):
    """API errors as small JSON bodies that never quote a provider's raw error."""
    if isinstance(exc, ProviderError):
        return JsonResponse({"error": exc.code, "detail": exc.public_message}, status=exc.status)
    response = drf_exception_handler(exc, context)
    if response is not None:
        codes = exc.get_codes() if isinstance(exc, APIException) else None
        code = codes if isinstance(codes, str) else getattr(exc, "default_code", "error")
        response.data = {"error": code, "detail": redact(_first_message(response.data))}
        return response
    logger.exception("Unhandled error in %s", context["view"].__class__.__name__)
    return JsonResponse({"error": "server_error", "detail": "Something went wrong."}, status=500)
