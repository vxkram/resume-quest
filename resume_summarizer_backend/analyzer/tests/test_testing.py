import random
from collections import Counter

from analyzer import testing

QUESTION = {"skill": "Python", "difficulty": "easy", "question": "Which?", "explanation": "",
            "options": ["right", "wrong 1", "wrong 2", "wrong 3"], "answer_index": 0}


def test_shuffle_keeps_the_answer_attached_to_its_text():
    for q in testing.shuffle_options([QUESTION] * 50, random.Random(1)):
        assert q["options"][q["answer_index"]] == "right"
        assert sorted(q["options"]) == sorted(QUESTION["options"])


def test_shuffle_spreads_the_answer_across_slots():
    positions = Counter(q["answer_index"] for q in testing.shuffle_options([QUESTION] * 400, random.Random(2)))
    assert set(positions) == {0, 1, 2, 3}
    assert min(positions.values()) > 60


def test_verdicts():
    assert testing.verdict(70, 100) == "underselling"
    assert testing.verdict(70, 60) == "matches_claim"
    assert testing.verdict(70, 40) == "not_backed_up"


def test_grade_counts_per_skill():
    questions = [dict(QUESTION, skill="Python"), dict(QUESTION, skill="Python"), dict(QUESTION, skill="SQL")]
    result = testing.grade(questions, [0, 1, None], [{"name": "python", "score": 80}])
    assert result["correct"] == 1 and result["score"] == 33
    skills = {s["skill"]: s for s in result["skills"]}
    assert skills["Python"]["demonstrated"] == 50 and skills["Python"]["verdict"] == "not_backed_up"
    assert skills["SQL"]["claimed"] is None and skills["SQL"]["verdict"] is None
