"""Settings for pytest: a throwaway secret key and the offline fake provider."""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-secret-key")
os.environ["ENABLE_FAKE_PROVIDER"] = "True"

from .settings import *  # noqa: E402,F401,F403
