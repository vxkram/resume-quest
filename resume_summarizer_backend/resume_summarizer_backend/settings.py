"""
Django settings for the resume analyzer.

This is a local, single-user app: it binds to localhost, keeps its data in a
local SQLite file and never stores LLM API keys (they arrive per request in the
X-LLM-Key header and are dropped when the request ends).
"""

from pathlib import Path
import os

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BASE_DIR.parent

load_dotenv(BASE_DIR / ".env")

DEBUG = os.environ.get("DJANGO_DEBUG", "False") == "True"

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "Set DJANGO_SECRET_KEY (or DJANGO_DEBUG=True for local development)."
        )
    SECRET_KEY = "dev-only-insecure-key-do-not-use-in-production"

# Only answer to localhost names. This also blocks DNS-rebinding attacks, where
# a hostile page points its own domain at 127.0.0.1 to reach this server.
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "rest_framework",
    "analyzer",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "analyzer.security.SecurityHeadersMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "resume_summarizer_backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["django.template.context_processors.request"]},
    },
]

WSGI_APPLICATION = "resume_summarizer_backend.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# The built frontend (npm run build) is served by Django from here, so the page
# and the API share one origin and no CORS is needed.
FRONTEND_DIST = REPO_DIR / "resume_summarizer_frontend" / "dist"

# Uploads: keep the whole file in memory (never written to disk) and cap it.
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_BYTES + 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_BYTES + 1024
FILE_UPLOAD_HANDLERS = ["django.core.files.uploadhandler.MemoryFileUploadHandler"]

REST_FRAMEWORK = {
    # No sessions or cookies: nothing for a cross-site request to ride on.
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "EXCEPTION_HANDLER": "analyzer.security.exception_handler",
}

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "no-referrer"
X_FRAME_OPTIONS = "DENY"
DEFAULT_EXCEPTION_REPORTER_FILTER = "analyzer.security.KeyRedactingReporterFilter"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"redact_keys": {"()": "analyzer.security.RedactKeysFilter"}},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["redact_keys"],
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        # The LLM SDKs log request details at DEBUG; never let that through.
        "openai": {"level": "WARNING"},
        "anthropic": {"level": "WARNING"},
        "google_genai": {"level": "WARNING"},
        "httpx": {"level": "WARNING"},
        "httpx2": {"level": "WARNING"},
    },
}

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")

# Offline, keyword-based provider used by the tests. Hidden from the UI unless enabled.
ENABLE_FAKE_PROVIDER = os.environ.get("ENABLE_FAKE_PROVIDER", "False") == "True"
