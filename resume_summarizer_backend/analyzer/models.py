import uuid

from django.db import models


class Analysis(models.Model):
    """One analysed résumé. Holds the extracted text, never the uploaded file or any key."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    # Hosted mode: SHA-256 of the browser's save token. Empty when running locally.
    owner = models.CharField(max_length=64, blank=True, default="", db_index=True)
    file_name = models.CharField(max_length=120)
    file_kind = models.CharField(max_length=8)
    resume_text = models.TextField()
    provider = models.CharField(max_length=20)
    model = models.CharField(max_length=100)
    profile = models.JSONField()        # headline, summary, seniority, domain, role fits, strengths, gaps
    skills = models.JSONField()         # scored skills with verified evidence
    quality = models.JSONField()        # deterministic résumé checks
    interview = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class Quiz(models.Model):
    """A generated quiz. The answer key stays here until the quiz is submitted."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE, related_name="quizzes")
    created_at = models.DateTimeField(auto_now_add=True)
    provider = models.CharField(max_length=20)
    model = models.CharField(max_length=100)
    questions = models.JSONField()
    result = models.JSONField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
