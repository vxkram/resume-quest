"""
WSGI config for resume_summarizer_backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path

from django.core.wsgi import get_wsgi_application

# Vercel imports this file from the repository root, where the outer
# resume_summarizer_backend/ folder would shadow this package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'resume_summarizer_backend.settings')

application = get_wsgi_application()
