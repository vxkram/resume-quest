"""A deterministic, offline stand-in for an LLM, for tests and CI.

It spots known skills by keyword and quotes the résumé lines they appear on, so
the rest of the pipeline (quote verification, scoring, quiz grading) runs for
real without a model. Only available when ENABLE_FAKE_PROVIDER=True.
"""

import re

from .base import Provider, ProviderInfo

KNOWN_SKILLS = {
    "Python": "language", "JavaScript": "language", "TypeScript": "language", "Java": "language",
    "Go": "language", "SQL": "language", "React": "framework", "Django": "framework",
    "FastAPI": "framework", "Flask": "framework", "PyTorch": "data_ml", "TensorFlow": "data_ml",
    "scikit-learn": "data_ml", "Docker": "cloud_devops", "Kubernetes": "cloud_devops",
    "AWS": "cloud_devops", "PostgreSQL": "database", "Redis": "database", "Git": "tool",
}
SECTION = re.compile(r"^\s*(skills|experience|work experience|projects|certifications|education)\s*:?\s*$", re.I)


def _resume(prompt):
    match = re.search(r"<resume>\n(.*)\n</resume>", prompt, re.S)
    return match.group(1) if match else ""


def _evidence(text, skill):
    section, items = "", []
    pattern = re.compile(rf"(?<![\w+#]){re.escape(skill)}(?![\w+#])")
    for line in text.splitlines():
        heading = SECTION.match(line)
        if heading:
            section = heading.group(1).lower()
            continue
        if not pattern.search(line):
            continue
        quote = line.strip(" •-*\t")
        if "skill" in section:
            kind = "listed"
        elif "cert" in section:
            kind = "cert"
        elif re.search(r"\d+\s*%|\d{2,}", quote):
            kind = "metric"
        elif "project" in section:
            kind = "project"
        else:
            kind = "job"
        items.append({"type": kind, "quote": quote})
    return items[:4]


class FakeProvider(Provider):
    info = ProviderInfo("fake", "Offline test provider", False, "keyword-matcher")

    def complete_json(self, *, system, prompt, schema, schema_name, api_key, model):
        text = _resume(prompt)
        found = [(name, cat) for name, cat in KNOWN_SKILLS.items()
                 if re.search(rf"(?<![\w+#]){re.escape(name)}(?![\w+#])", text)]
        names = [name for name, _ in found] or ["Communication"]
        if schema_name == "analysis":
            return {
                "headline": f"Engineer working with {', '.join(names[:3])}",
                "summary": f"Résumé mentions {len(found)} recognised technical skills.",
                "seniority": "mid",
                "domain": "software",
                "role_fits": [
                    {"title": "Backend Engineer", "confidence": 70, "rationale": "Server-side skills."},
                    {"title": "ML Engineer", "confidence": 55, "rationale": "Some ML tooling."},
                    {"title": "Full-Stack Engineer", "confidence": 40, "rationale": "Some frontend."},
                ],
                "skills": [{"name": n, "category": c, "evidence": _evidence(text, n)} for n, c in found],
                "strengths": ["Broad toolset"],
                "gaps": ["No leadership examples"],
            }
        if schema_name == "quiz":
            return {"questions": [
                {
                    "skill": name,
                    "difficulty": "medium",
                    "question": f"Which statement about {name} is correct? (#{i + 1})",
                    "options": [f"{name} fact A", f"{name} fact B", f"{name} fact C", f"{name} fact D"],
                    "answer_index": i % 4,
                    "explanation": f"Fact {'ABCD'[i % 4]} is the correct one.",
                }
                for i, name in enumerate((names * 3)[:8])
            ]}
        if schema_name == "interview":
            return {"questions": [
                {
                    "skill": name,
                    "difficulty": ["easy", "medium", "hard"][i % 3],
                    "question": f"Walk me through how you have used {name}.",
                    "good_answer_covers": ["A concrete project", "Trade-offs considered"],
                }
                for i, name in enumerate((names * 3)[:9])
            ]}
        raise ValueError(schema_name)
