#!/usr/bin/env bash
# One command to run the app locally: http://127.0.0.1:8000
# Creates the virtualenv, a secret key, the database and the frontend build on first run.
set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
if [ ! -x .venv/bin/python ]; then
  echo "Creating .venv with $PYTHON"
  "$PYTHON" -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi

ENV_FILE=resume_summarizer_backend/.env
if [ ! -f "$ENV_FILE" ]; then
  echo "Writing $ENV_FILE with a new secret key"
  key="$(.venv/bin/python -c 'import secrets; print(secrets.token_urlsafe(50))')"
  printf 'DJANGO_SECRET_KEY=%s\nDJANGO_DEBUG=False\n' "$key" > "$ENV_FILE"
  chmod 600 "$ENV_FILE"
fi

if [ ! -f resume_summarizer_frontend/dist/index.html ]; then
  echo "Building the frontend"
  (cd resume_summarizer_frontend && npm ci && npm run build)
fi

cd resume_summarizer_backend
../.venv/bin/python manage.py migrate --verbosity 0
echo "Résumé Quest is running at http://127.0.0.1:8000 (Ctrl+C to stop)"
exec ../.venv/bin/python manage.py runserver 127.0.0.1:8000 --noreload
