import json
import os
from unittest.mock import patch

import pytest
from django.urls import reverse


@pytest.fixture
def saved_jsons_dir(settings, tmp_path):
    saved_dir = tmp_path / "saved_jsons"
    saved_dir.mkdir()
    settings.SAVED_JSONS_ROOT = str(saved_dir)
    return saved_dir


@pytest.fixture
def media_root(settings, tmp_path):
    media_dir = tmp_path / "resumes"
    media_dir.mkdir()
    settings.MEDIA_ROOT = str(media_dir)
    return media_dir


def write_result_json(saved_jsons_dir, file_name, data):
    path = saved_jsons_dir / f"{file_name}.json"
    path.write_text(json.dumps(data))
    return path


@pytest.mark.django_db
def test_summary_view_404_when_missing(client, saved_jsons_dir):
    response = client.get(reverse('summary', kwargs={'file_name': 'nope'}))
    assert response.status_code == 404


@pytest.mark.django_db
def test_summary_view_returns_summary(client, saved_jsons_dir):
    write_result_json(saved_jsons_dir, 'resume', {'summary': 'A short summary.'})
    response = client.get(reverse('summary', kwargs={'file_name': 'resume'}))
    assert response.status_code == 200
    assert response.json() == {'summary': 'A short summary.'}


@pytest.mark.django_db
def test_questions_view_404_when_missing(client, saved_jsons_dir):
    response = client.get(reverse('questions', kwargs={'file_name': 'nope'}))
    assert response.status_code == 404


@pytest.mark.django_db
def test_questions_view_returns_questions(client, saved_jsons_dir):
    write_result_json(saved_jsons_dir, 'resume', {'questions': ['1. Tell me about X.']})
    response = client.get(reverse('questions', kwargs={'file_name': 'resume'}))
    assert response.status_code == 200
    assert response.json() == {'questions': ['1. Tell me about X.']}


@pytest.mark.django_db
def test_save_answers_404_when_missing(client, saved_jsons_dir):
    response = client.post(
        reverse('save-answers', kwargs={'file_name': 'nope'}),
        data=json.dumps({'answers': ['a']}),
        content_type='application/json',
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_save_answers_persists_to_json_file(client, saved_jsons_dir):
    path = write_result_json(
        saved_jsons_dir, 'resume', {'user_answers': {'answers_to_questions': ['']}}
    )
    response = client.post(
        reverse('save-answers', kwargs={'file_name': 'resume'}),
        data=json.dumps({'answers': ['my answer']}),
        content_type='application/json',
    )
    assert response.status_code == 200
    saved = json.loads(path.read_text())
    assert saved['user_answers']['answers_to_questions'] == ['my answer']


@pytest.mark.django_db
def test_upload_rejects_non_pdf(client, media_root):
    from django.core.files.uploadedfile import SimpleUploadedFile

    fake_file = SimpleUploadedFile('resume.txt', b'not a pdf', content_type='text/plain')
    response = client.post(reverse('resume-upload'), {'file': fake_file})
    assert response.status_code == 400


@pytest.mark.django_db
def test_upload_returns_503_when_openai_key_missing(client, media_root, saved_jsons_dir, settings):
    from django.core.files.uploadedfile import SimpleUploadedFile

    settings.OPENAI_API_KEY = ''
    fake_pdf = SimpleUploadedFile('resume.pdf', b'%PDF-1.4 fake', content_type='application/pdf')

    with patch('api.resume_upload_view.extract_text_from_pdf', return_value='Some resume text'):
        response = client.post(reverse('resume-upload'), {'file': fake_pdf})

    assert response.status_code == 503
    assert 'OPENAI_API_KEY' in response.json()['error']
