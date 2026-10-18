"""Knowledge checks: building a quiz from the skill scores, and grading it."""

import random

from .analytics import level_for

QUIZ_SKILLS = 6
INTERVIEW_SKILLS = 6


def quiz_targets(skills):
    """The strongest claimed skills, ignoring ones with no verified evidence at all."""
    return [s for s in skills if s["score"] > 0][:QUIZ_SKILLS] or skills[:QUIZ_SKILLS]


def interview_targets(skills):
    return [s for s in skills if s["category"] != "soft"][:INTERVIEW_SKILLS] or skills[:INTERVIEW_SKILLS]


def shuffle_options(questions, rng=None):
    """Shuffle each question's options and move the answer key with them.

    Models tend to put the right answer in the same slot (small ones love "B"),
    which would let anyone pass by always picking it.
    """
    rng = rng or random.SystemRandom()
    shuffled = []
    for q in questions:
        order = list(range(len(q["options"])))
        rng.shuffle(order)
        shuffled.append({**q, "options": [q["options"][i] for i in order],
                         "answer_index": order.index(q["answer_index"])})
    return shuffled


def public_questions(questions):
    """A quiz as the browser sees it before submitting: no answers, no explanations."""
    return [
        {"index": i, "skill": q["skill"], "difficulty": q["difficulty"],
         "question": q["question"], "options": q["options"]}
        for i, q in enumerate(questions)
    ]


def verdict(claimed, demonstrated):
    diff = demonstrated - claimed
    if diff >= 20:
        return "underselling"
    if diff <= -25:
        return "not_backed_up"
    return "matches_claim"


def grade(questions, answers, skills):
    """answers: one chosen option index (or None) per question."""
    claimed = {s["name"].lower(): s["score"] for s in skills}
    per_question, per_skill = [], {}
    for q, chosen in zip(questions, answers):
        correct = chosen == q["answer_index"]
        per_question.append({
            "correct": correct,
            "chosen": chosen,
            "answer_index": q["answer_index"],
            "explanation": q["explanation"],
        })
        tally = per_skill.setdefault(q["skill"], [0, 0])
        tally[0] += correct
        tally[1] += 1
    skills_out = []
    for name, (right, total) in per_skill.items():
        demonstrated = round(100 * right / total)
        claim = claimed.get(name.lower())
        skills_out.append({
            "skill": name,
            "correct": right,
            "total": total,
            "demonstrated": demonstrated,
            "claimed": claim,
            "verdict": verdict(claim, demonstrated) if claim is not None else None,
        })
    right = sum(p["correct"] for p in per_question)
    score = round(100 * right / len(questions)) if questions else 0
    return {
        "score": score,
        "correct": right,
        "total": len(questions),
        "level": level_for(score),
        "questions": per_question,
        "skills": sorted(skills_out, key=lambda s: -s["total"]),
    }
