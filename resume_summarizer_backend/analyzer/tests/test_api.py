"""The whole HTTP API, end to end, with the offline fake provider."""

import pytest
from django.test import Client

from analyzer.models import Analysis, Quiz

pytestmark = pytest.mark.django_db


def test_providers_list_includes_every_provider_and_the_test_provider(api):
    providers = {p["id"]: p for p in api.get("/api/providers/").json()}
    assert set(providers) == {"openai", "anthropic", "gemini", "groq", "openrouter", "ollama", "fake"}
    assert providers["ollama"]["needs_key"] is False
    assert providers["anthropic"]["needs_key"] is True
    assert {p for p, info in providers.items() if info["free_tier"]} == {"gemini", "groq", "openrouter"}
    assert providers["groq"]["key_url"].startswith("https://")


def test_fake_provider_hidden_unless_enabled(api, settings):
    settings.ENABLE_FAKE_PROVIDER = False
    assert "fake" not in {p["id"] for p in api.get("/api/providers/").json()}


def test_analyze_returns_the_full_character_sheet(analysis):
    assert analysis["headline"] and analysis["top_role"] == "Backend Engineer"
    assert analysis["file_name"] == "resume.pdf"
    skills = {s["name"]: s for s in analysis["skills"]}
    # The fake provider quotes real lines, so evidence verifies and scores follow the formula.
    assert skills["PyTorch"]["verified_count"] >= 2
    assert skills["PyTorch"]["score"] > skills["Redis"]["score"]
    assert skills["Redis"]["level"] in {"Novice", "Apprentice"}  # only listed
    assert analysis["quality"]["rank"] in "SABCD"
    assert analysis["categories"][0]["average"] >= analysis["categories"][-1]["average"]
    assert analysis["power_level"] > 0
    training = {t["skill"]: t for t in analysis["training"]["by_skill"]}
    assert "Python" in training or "SQL" in training
    assert analysis["training"]["general"]
    assert analysis["latest_quiz"] is None and analysis["interview"] is None


def test_upload_is_not_kept_on_disk(analysis, settings, tmp_path):
    stored = Analysis.objects.get(pk=analysis["id"])
    assert "Alex Rivera" in stored.resume_text
    assert not hasattr(stored, "file")


def test_docx_upload(upload, sample_docx):
    response = upload(data=sample_docx, name="cv.docx")
    assert response.status_code == 201
    assert Analysis.objects.get(pk=response.json()["id"]).file_kind == "docx"


def test_bad_uploads(upload, api):
    assert upload(data=b"hello" * 100, name="x.pdf").json()["error"] == "bad_upload"
    response = api.post("/api/analyses/", {"provider": "fake"})
    assert response.status_code == 400 and "Attach" in response.json()["detail"]


def test_unknown_provider_and_bad_model_name(upload):
    response = upload(provider="nope")
    assert response.status_code == 400
    assert response.json() == {"error": "invalid", "detail": "Unknown provider."}
    assert upload(model="rm -rf /; echo").json()["detail"] == "That doesn't look like a model name."


def test_cloud_provider_without_key_is_rejected_before_any_call(upload):
    response = upload(provider="openai")
    assert response.status_code == 400
    assert response.json() == {"error": "invalid_key", "detail": "This provider needs an API key."}


def test_state_changing_requests_need_the_client_header(sample_pdf, analysis):
    bare = Client()
    from django.core.files.uploadedfile import SimpleUploadedFile
    assert bare.post("/api/analyses/", {"file": SimpleUploadedFile("a.pdf", sample_pdf),
                                        "provider": "fake"}).status_code == 403
    assert bare.delete(f"/api/analyses/{analysis['id']}/").status_code == 403
    assert bare.get("/api/analyses/").status_code == 200  # reads are fine


def test_quiz_flow_hides_answers_until_submitted(api, analysis):
    response = api.post(f"/api/analyses/{analysis['id']}/quiz/", {"provider": "fake"},
                        content_type="application/json")
    assert response.status_code == 201
    quiz = response.json()
    assert len(quiz["questions"]) == 8 and quiz["result"] is None
    for question in quiz["questions"]:
        assert set(question) == {"index", "skill", "difficulty", "question", "options"}
    # Fetching it again doesn't leak the answers either.
    assert "answer_index" not in str(api.get(f"/api/quizzes/{quiz['id']}/").json())

    # Read the answer key from the database. Get the first 6 right, the 7th wrong, skip the 8th.
    key = [q["answer_index"] for q in Quiz.objects.get(pk=quiz["id"]).questions]
    answers = key[:6] + [(key[6] + 1) % 4, None]
    result = api.post(f"/api/quizzes/{quiz['id']}/submit/", {"answers": answers},
                      content_type="application/json").json()["result"]
    assert result["correct"] == 6 and result["total"] == 8 and result["score"] == 75
    assert result["questions"][7]["chosen"] is None and not result["questions"][7]["correct"]
    assert all("explanation" in q for q in result["questions"])
    assert {s["verdict"] for s in result["skills"]} <= {"underselling", "matches_claim", "not_backed_up"}

    again = api.post(f"/api/quizzes/{quiz['id']}/submit/", {"answers": answers},
                     content_type="application/json")
    assert again.status_code == 400

    detail = api.get(f"/api/analyses/{analysis['id']}/").json()
    assert detail["latest_quiz"] == {"id": quiz["id"], "submitted": True, "score": 75}


@pytest.mark.parametrize("answers", [[0], "0,1,2", [0] * 7 + [4], [0] * 7 + [True], [0] * 7 + ["1"]])
def test_quiz_submit_validates_answers(api, analysis, answers):
    quiz = api.post(f"/api/analyses/{analysis['id']}/quiz/", {"provider": "fake"},
                    content_type="application/json").json()
    response = api.post(f"/api/quizzes/{quiz['id']}/submit/", {"answers": answers},
                        content_type="application/json")
    assert response.status_code == 400


def test_interview_questions_are_generated_and_cached(api, analysis):
    response = api.post(f"/api/analyses/{analysis['id']}/interview/", {"provider": "fake"},
                        content_type="application/json")
    questions = response.json()["questions"]
    assert response.status_code == 200 and len(questions) == 9
    assert [q["difficulty"] for q in questions] == sorted(
        (q["difficulty"] for q in questions), key=["easy", "medium", "hard"].index)
    assert api.get(f"/api/analyses/{analysis['id']}/").json()["interview"] == questions


def test_history_and_delete(api, analysis):
    history = api.get("/api/analyses/").json()
    assert [h["id"] for h in history] == [analysis["id"]]
    assert "skills" not in history[0]  # the list is a summary
    api.post(f"/api/analyses/{analysis['id']}/quiz/", {"provider": "fake"}, content_type="application/json")

    assert api.delete(f"/api/analyses/{analysis['id']}/").status_code == 204
    assert not Analysis.objects.exists() and not Quiz.objects.exists()
    assert api.get(f"/api/analyses/{analysis['id']}/").status_code == 404


def test_api_responses_are_not_cached_and_carry_security_headers(api):
    response = api.get("/api/providers/")
    assert response["Cache-Control"] == "no-store"
    assert "default-src 'self'" in response["Content-Security-Policy"]
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["Referrer-Policy"] == "no-referrer"
    assert response["X-Frame-Options"] == "DENY"


def body(response):
    return b"".join(response.streaming_content) if response.streaming else response.content


def test_frontend_routes_serve_index_and_block_traversal(client, settings, tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<!doctype html><div id=root></div>")
    (tmp_path / "assets" / "app.js").write_text("console.log(1)")
    (tmp_path.parent / "secret.txt").write_text("nope")
    settings.FRONTEND_DIST = tmp_path

    assert b"id=root" in body(client.get("/"))
    assert b"id=root" in body(client.get("/sheet/123"))  # client-side route
    assert body(client.get("/assets/app.js")) == b"console.log(1)"
    assert b"nope" not in body(client.get("/../secret.txt"))
    assert b"nope" not in body(client.get("/%2e%2e/secret.txt"))
    assert b"nope" not in body(client.get("/assets/..%2f..%2fsecret.txt"))


def test_frontend_not_built_message(client, settings, tmp_path):
    settings.FRONTEND_DIST = tmp_path / "missing"
    response = client.get("/")
    assert response.status_code == 503 and b"npm run build" in response.content


def test_disallowed_host_is_refused(client):
    assert client.get("/api/providers/", HTTP_HOST="evil.example.com").status_code == 400
