"""What we ask the model for (JSON schemas) and how we check what comes back (pydantic).

The schemas stick to the subset every provider's structured-output mode accepts
(types, enums, required, additionalProperties: false). Bounds, lengths and
de-duplication are enforced afterwards by the pydantic models instead.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

SENIORITY = ["intern", "entry", "mid", "senior", "lead"]
CATEGORIES = ["language", "framework", "data_ml", "cloud_devops", "database", "tool", "soft", "other"]
EVIDENCE_TYPES = ["listed", "project", "job", "metric", "cert"]
DIFFICULTY = ["easy", "medium", "hard"]


def _obj(properties):
    return {
        "type": "object",
        "properties": properties,
        "required": list(properties),
        "additionalProperties": False,
    }


def _array(items):
    return {"type": "array", "items": items}


STR = {"type": "string"}
INT = {"type": "integer"}

ANALYSIS_SCHEMA = _obj({
    "headline": STR,
    "summary": STR,
    "seniority": {"type": "string", "enum": SENIORITY},
    "domain": STR,
    "role_fits": _array(_obj({"title": STR, "confidence": INT, "rationale": STR})),
    "skills": _array(_obj({
        "name": STR,
        "category": {"type": "string", "enum": CATEGORIES},
        "evidence": _array(_obj({
            "type": {"type": "string", "enum": EVIDENCE_TYPES},
            "quote": STR,
        })),
    })),
    "strengths": _array(STR),
    "gaps": _array(STR),
})

QUIZ_SCHEMA = _obj({
    "questions": _array(_obj({
        "skill": STR,
        "difficulty": {"type": "string", "enum": DIFFICULTY},
        "question": STR,
        "options": _array(STR),
        "answer_index": INT,
        "explanation": STR,
    })),
})

INTERVIEW_SCHEMA = _obj({
    "questions": _array(_obj({
        "skill": STR,
        "difficulty": {"type": "string", "enum": DIFFICULTY},
        "question": STR,
        "good_answer_covers": _array(STR),
    })),
})


class Evidence(BaseModel):
    type: Literal["listed", "project", "job", "metric", "cert"]
    quote: str = Field(max_length=600)


class SkillClaim(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    category: Literal["language", "framework", "data_ml", "cloud_devops", "database", "tool", "soft", "other"]
    evidence: list[Evidence] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value):
        return value.strip()


class RoleFit(BaseModel):
    title: str = Field(min_length=1, max_length=80)
    confidence: int
    rationale: str = Field(max_length=600)

    @field_validator("confidence")
    @classmethod
    def clamp(cls, value):
        return max(0, min(100, value))


class AnalysisOut(BaseModel):
    headline: str = Field(max_length=200)
    summary: str = Field(max_length=2000)
    seniority: Literal["intern", "entry", "mid", "senior", "lead"]
    domain: str = Field(max_length=100)
    role_fits: list[RoleFit]
    skills: list[SkillClaim]
    strengths: list[str]
    gaps: list[str]

    @model_validator(mode="after")
    def tidy(self):
        self.role_fits = sorted(self.role_fits, key=lambda r: -r.confidence)[:3]
        seen, skills = set(), []
        for skill in self.skills:
            if skill.name.lower() not in seen:
                seen.add(skill.name.lower())
                skills.append(skill)
        self.skills = skills[:25]
        self.strengths = [s for s in self.strengths if s.strip()][:5]
        self.gaps = [g for g in self.gaps if g.strip()][:5]
        if not self.role_fits:
            raise ValueError("no role fits")
        return self


class QuizQuestion(BaseModel):
    skill: str = Field(min_length=1, max_length=60)
    difficulty: Literal["easy", "medium", "hard"]
    question: str = Field(min_length=5, max_length=600)
    options: list[str]
    answer_index: int
    explanation: str = Field(max_length=800)


class QuizOut(BaseModel):
    questions: list[QuizQuestion]

    @field_validator("questions", mode="before")
    @classmethod
    def drop_broken(cls, items):
        """Keep only questions with 4 distinct options and an answer that points at one."""
        good = []
        for item in items or []:
            if not isinstance(item, dict):
                continue
            options = [str(o).strip() for o in item.get("options") or []]
            index = item.get("answer_index")
            if (len(options) == 4 and len({o.lower() for o in options}) == 4
                    and isinstance(index, int) and 0 <= index < 4):
                good.append({**item, "options": options})
        return good[:10]

    @model_validator(mode="after")
    def enough(self):
        if len(self.questions) < 3:
            raise ValueError("too few usable questions")
        return self


class InterviewQuestion(BaseModel):
    skill: str = Field(min_length=1, max_length=60)
    difficulty: Literal["easy", "medium", "hard"]
    question: str = Field(min_length=5, max_length=600)
    good_answer_covers: list[str]


class InterviewOut(BaseModel):
    questions: list[InterviewQuestion]

    @model_validator(mode="after")
    def tidy(self):
        order = {d: i for i, d in enumerate(DIFFICULTY)}
        self.questions = sorted(self.questions, key=lambda q: order[q.difficulty])[:15]
        if len(self.questions) < 3:
            raise ValueError("too few questions")
        return self
