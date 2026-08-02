# Resume Summarizer

A full-stack app that takes a resume PDF and, using GPT, extracts its key sections (skills, education, projects, experience), writes a short summary, and generates interview questions based on it — with a page to answer those questions and save the answers.

**Stack:** Django REST Framework backend · React frontend · OpenAI GPT-3.5

## How it works

1. **Upload** — the frontend posts a PDF to the backend, which extracts the raw text with `pdfminer.six`.
2. **Summarize** — that text goes to GPT-3.5 with a prompt asking for extracted sections, a summary, and 5 interview questions. The response is parsed into structured JSON and saved to disk.
3. **Review** — the frontend shows the summary, then the generated questions with input boxes for answers, which get POSTed back and merged into the saved JSON.

```
resume_summarizer_backend/    Django REST API
  api/                        views: upload, summary, questions, save-answers
  gpt_integration/             PDF text extraction + OpenAI call
  resumes/                     uploaded PDFs (gitignored)
  saved_jsons/                 per-resume summary/questions/answers (gitignored)
resume_summarizer_frontend/   React app (upload → summary → questions flow)
```

## Setup

### Backend

```bash
cd resume_summarizer_backend
python -m venv .venv
source .venv/bin/activate  # .venv\Scripts\activate on Windows

pip install -r ../requirements.txt
cp .env.example .env   # then add your OpenAI API key

python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd resume_summarizer_frontend
npm install
cp .env.example .env   # defaults to http://localhost:8000, override if needed
npm start
```

Open `http://localhost:3000`, upload a PDF resume, and you'll be walked through the summary and interview-question pages.

## Running tests

```bash
# backend
cd resume_summarizer_backend
pip install -r ../requirements.txt
pytest

# frontend
cd resume_summarizer_frontend
npm test -- --watchAll=false
```

## Notes

- The upload endpoint returns a friendly error (HTTP 503) if `OPENAI_API_KEY` isn't set, instead of crashing.
- Uploaded resumes and generated JSON live under `resumes/` and `saved_jsons/` — both are local/gitignored, not persisted anywhere durable. This is a demo app, not built for multi-user production use (no auth, no database-backed storage of results).
