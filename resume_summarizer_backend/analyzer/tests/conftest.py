from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

SAMPLES = Path(__file__).resolve().parents[3] / "samples"


@pytest.fixture
def sample_pdf():
    return (SAMPLES / "sample_resume.pdf").read_bytes()


@pytest.fixture
def sample_docx():
    return (SAMPLES / "sample_resume.docx").read_bytes()


@pytest.fixture
def sample_text():
    return (SAMPLES / "sample_resume.txt").read_text()


@pytest.fixture
def api():
    """A test client that sends the X-Resume-Quest header like the real frontend."""
    return Client(headers={"X-Resume-Quest": "1"})


@pytest.fixture
def upload(api, sample_pdf):
    def _upload(provider="fake", data=None, name="resume.pdf", headers=None, **extra):
        file = SimpleUploadedFile(name, data if data is not None else sample_pdf)
        return api.post("/api/analyses/", {"file": file, "provider": provider, **extra},
                        headers=headers or {})
    return _upload


@pytest.fixture
def analysis(upload, db):
    response = upload()
    assert response.status_code == 201, response.content
    return response.json()
