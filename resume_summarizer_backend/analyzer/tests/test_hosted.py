"""Hosted mode: strangers share one server, so each browser only sees its own saves."""

import hashlib
from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.utils import timezone

from analyzer.models import Analysis

ALICE = "a" * 43
BOB = "b" * 43


@pytest.fixture
def hosted(settings, db):
    settings.HOSTED = True
    settings.SAVE_RETENTION_HOURS = 24


def browser(token):
    return Client(headers={"X-Resume-Quest": "1", "X-Save-Token": token})


def analyse(client, sample_pdf):
    file = SimpleUploadedFile("resume.pdf", sample_pdf)
    response = client.post("/api/analyses/", {"file": file, "provider": "fake"})
    assert response.status_code == 201, response.content
    return response.json()


def test_config_reports_the_mode(api, settings):
    assert api.get("/api/config/").json() == {"hosted": False, "save_hours": None, "max_upload_mb": 5}
    settings.HOSTED = True
    assert api.get("/api/config/").json()["hosted"] is True


def test_ollama_is_offered_locally_but_hidden_when_hosted(api, settings):
    assert "ollama" in [p["id"] for p in api.get("/api/providers/").json()]
    settings.HOSTED = True
    assert "ollama" not in [p["id"] for p in api.get("/api/providers/").json()]
    assert api.get("/api/providers/ollama/models/").status_code == 404


@pytest.mark.parametrize("token", [None, "short", "x" * 200, "has spaces in it, which is not allowed here"])
def test_hosted_api_needs_a_well_formed_save_token(hosted, token):
    headers = {"X-Resume-Quest": "1"} | ({"X-Save-Token": token} if token else {})
    response = Client(headers=headers).get("/api/analyses/")
    assert response.status_code == 400
    assert "X-Save-Token" in response.json()["detail"]


def test_saves_are_private_to_each_browser(hosted, sample_pdf):
    alice, bob = browser(ALICE), browser(BOB)
    mine = analyse(alice, sample_pdf)

    assert [s["id"] for s in alice.get("/api/analyses/").json()] == [mine["id"]]
    assert bob.get("/api/analyses/").json() == []
    assert bob.get(f"/api/analyses/{mine['id']}/").status_code == 404
    assert bob.delete(f"/api/analyses/{mine['id']}/").status_code == 404
    for action in ("quiz", "interview"):
        response = bob.post(f"/api/analyses/{mine['id']}/{action}/", {"provider": "fake"},
                            content_type="application/json")
        assert response.status_code == 404
    assert alice.get(f"/api/analyses/{mine['id']}/").status_code == 200


def test_quizzes_are_private_to_each_browser(hosted, sample_pdf):
    alice, bob = browser(ALICE), browser(BOB)
    analysis = analyse(alice, sample_pdf)
    quiz = alice.post(f"/api/analyses/{analysis['id']}/quiz/", {"provider": "fake"},
                      content_type="application/json").json()
    answers = [0] * len(quiz["questions"])

    assert bob.get(f"/api/quizzes/{quiz['id']}/").status_code == 404
    assert bob.post(f"/api/quizzes/{quiz['id']}/submit/", {"answers": answers},
                    content_type="application/json").status_code == 404
    assert alice.post(f"/api/quizzes/{quiz['id']}/submit/", {"answers": answers},
                      content_type="application/json").status_code == 200


def test_only_a_hash_of_the_token_is_stored(hosted, sample_pdf):
    analyse(browser(ALICE), sample_pdf)
    assert Analysis.objects.get().owner == hashlib.sha256(ALICE.encode()).hexdigest()


def test_saves_expire_and_are_purged(hosted, sample_pdf):
    alice = browser(ALICE)
    old = analyse(alice, sample_pdf)
    Analysis.objects.filter(pk=old["id"]).update(created_at=timezone.now() - timedelta(hours=25))

    assert alice.get("/api/analyses/").json() == []
    assert alice.get(f"/api/analyses/{old['id']}/").status_code == 404

    analyse(browser(BOB), sample_pdf)
    assert not Analysis.objects.filter(pk=old["id"]).exists()


def test_local_mode_ignores_save_tokens(api, sample_pdf, db):
    mine = analyse(browser(ALICE), sample_pdf)
    assert Analysis.objects.get().owner == ""
    assert [s["id"] for s in api.get("/api/analyses/").json()] == [mine["id"]]
