import re

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_variables
from django.views.static import serve
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from . import analytics, external_tests, prompts, testing
from .extract import extract_text
from .llm import available_providers, call_structured, get_provider
from .models import Analysis, Quiz
from .schemas import (ANALYSIS_SCHEMA, INTERVIEW_SCHEMA, QUIZ_SCHEMA, AnalysisOut,
                      InterviewOut, QuizOut)
from .security import read_api_key

MODEL_NAME = re.compile(r"^[\w.:/\-]{1,100}$")
SAFE_FILE_NAME = re.compile(r"[^\w.\- ]")

sensitive = method_decorator(sensitive_variables("api_key"))


def _provider_and_model(data):
    provider = get_provider(str(data.get("provider", "")))
    if provider is None:
        raise ValidationError({"provider": "Unknown provider."})
    model = str(data.get("model") or provider.info.default_model).strip()
    if not MODEL_NAME.match(model):
        raise ValidationError({"model": "That doesn't look like a model name."})
    return provider, model


def _key_for(request, provider):
    return read_api_key(request) if provider.info.needs_key else ""


def analysis_payload(analysis, full=True):
    data = {
        "id": str(analysis.id),
        "created_at": analysis.created_at.isoformat(),
        "file_name": analysis.file_name,
        "provider": analysis.provider,
        "model": analysis.model,
        "headline": analysis.profile["headline"],
        "top_role": analysis.profile["role_fits"][0]["title"],
        "seniority": analysis.profile["seniority"],
        "power_level": analytics.power_level(analysis.skills),
        "quality_rank": analysis.quality["rank"],
    }
    if full:
        data.update(
            profile=analysis.profile,
            skills=analysis.skills,
            categories=analytics.category_summary(analysis.skills),
            quality=analysis.quality,
            training=external_tests.training_plan(analysis.skills),
            interview=analysis.interview,
            latest_quiz=_latest_quiz(analysis),
        )
    return data


def _latest_quiz(analysis):
    quiz = analysis.quizzes.first()
    if quiz is None:
        return None
    return {"id": str(quiz.id), "submitted": quiz.result is not None,
            "score": quiz.result["score"] if quiz.result else None}


class ProvidersView(APIView):
    def get(self, request):
        return Response([
            {"id": p.info.id, "label": p.info.label, "needs_key": p.info.needs_key,
             "default_model": p.info.default_model, "key_hint": p.info.key_hint}
            for p in available_providers()
        ])


class ProviderModelsView(APIView):
    @sensitive
    def get(self, request, provider_id):
        provider = get_provider(provider_id)
        if provider is None:
            raise Http404
        api_key = _key_for(request, provider)
        return Response({"models": provider.list_models(api_key=api_key)})


class AnalysisListView(APIView):
    def get(self, request):
        return Response([analysis_payload(a, full=False) for a in Analysis.objects.all()[:50]])

    @sensitive
    def post(self, request):
        provider, model = _provider_and_model(request.data)
        api_key = _key_for(request, provider)
        upload = request.FILES.get("file")
        text, kind = extract_text(upload)

        result = call_structured(
            provider, system=prompts.SYSTEM, prompt=prompts.analysis_prompt(text),
            schema=ANALYSIS_SCHEMA, schema_name="analysis", model_cls=AnalysisOut,
            api_key=api_key, model=model,
        )
        skills = analytics.score_skills(result.skills, text)
        profile = result.model_dump(exclude={"skills"})
        name = SAFE_FILE_NAME.sub("", upload.name)[:120] or f"resume.{kind}"
        analysis = Analysis.objects.create(
            file_name=name, file_kind=kind, resume_text=text,
            provider=provider.info.id, model=model, profile=profile,
            skills=skills, quality=analytics.resume_quality(text),
        )
        return Response(analysis_payload(analysis), status=status.HTTP_201_CREATED)


class AnalysisDetailView(APIView):
    def get(self, request, pk):
        return Response(analysis_payload(get_object_or_404(Analysis, pk=pk)))

    def delete(self, request, pk):
        get_object_or_404(Analysis, pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class QuizCreateView(APIView):
    @sensitive
    def post(self, request, pk):
        analysis = get_object_or_404(Analysis, pk=pk)
        provider, model = _provider_and_model(request.data)
        api_key = _key_for(request, provider)
        targets = testing.quiz_targets(analysis.skills)
        if not targets:
            raise ValidationError({"detail": "No skills found to quiz on."})
        result = call_structured(
            provider, system=prompts.SYSTEM, prompt=prompts.quiz_prompt(analysis.resume_text, targets),
            schema=QUIZ_SCHEMA, schema_name="quiz", model_cls=QuizOut,
            api_key=api_key, model=model,
        )
        quiz = Quiz.objects.create(
            analysis=analysis, provider=provider.info.id, model=model,
            questions=testing.shuffle_options([q.model_dump() for q in result.questions]),
        )
        return Response(quiz_payload(quiz), status=status.HTTP_201_CREATED)


def quiz_payload(quiz):
    return {
        "id": str(quiz.id),
        "analysis_id": str(quiz.analysis_id),
        "questions": testing.public_questions(quiz.questions),
        "result": quiz.result,
    }


class QuizDetailView(APIView):
    def get(self, request, pk):
        return Response(quiz_payload(get_object_or_404(Quiz, pk=pk)))


class QuizSubmitView(APIView):
    def post(self, request, pk):
        quiz = get_object_or_404(Quiz.objects.select_related("analysis"), pk=pk)
        if quiz.result is not None:
            raise ValidationError({"detail": "This quiz was already submitted."})
        answers = request.data.get("answers")
        if not isinstance(answers, list) or len(answers) != len(quiz.questions):
            raise ValidationError({"answers": "Send one answer per question."})
        if any(a is not None and (not isinstance(a, int) or isinstance(a, bool) or not 0 <= a < 4)
               for a in answers):
            raise ValidationError({"answers": "Each answer is an option index 0-3, or null."})
        quiz.result = testing.grade(quiz.questions, answers, quiz.analysis.skills)
        quiz.submitted_at = timezone.now()
        quiz.save(update_fields=["result", "submitted_at"])
        return Response(quiz_payload(quiz))


class InterviewView(APIView):
    @sensitive
    def post(self, request, pk):
        analysis = get_object_or_404(Analysis, pk=pk)
        provider, model = _provider_and_model(request.data)
        api_key = _key_for(request, provider)
        targets = testing.interview_targets(analysis.skills)
        result = call_structured(
            provider, system=prompts.SYSTEM,
            prompt=prompts.interview_prompt(analysis.resume_text, targets),
            schema=INTERVIEW_SCHEMA, schema_name="interview", model_cls=InterviewOut,
            api_key=api_key, model=model,
        )
        analysis.interview = [q.model_dump() for q in result.questions]
        analysis.save(update_fields=["interview"])
        return Response({"questions": analysis.interview})


def frontend(request, path=""):
    """Serve the built single-page app: real files as-is, every other route gets index.html."""
    dist = settings.FRONTEND_DIST.resolve()
    target = (dist / path).resolve()
    if path and target.is_relative_to(dist) and target.is_file():
        return serve(request, path, document_root=dist)
    index = dist / "index.html"
    if not index.is_file():
        return HttpResponse(
            "Frontend not built. Run `npm run build` in resume_summarizer_frontend/, "
            "or use the Vite dev server on http://localhost:5173.",
            content_type="text/plain", status=503,
        )
    return HttpResponse(index.read_bytes(), content_type="text/html; charset=utf-8")
