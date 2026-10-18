from analyzer import external_tests


def test_aliases_map_to_the_same_tests():
    assert external_tests.tests_for("PostgreSQL") == external_tests.tests_for("postgres")
    assert external_tests.tests_for("  Node.js ") == external_tests.tests_for("javascript")
    assert external_tests.tests_for("Underwater basket weaving") == []


def test_training_plan_orders_weakest_first_and_does_not_repeat_links():
    skills = [
        {"name": "PyTorch", "score": 90, "level": "Expert"},
        {"name": "SQL", "score": 10, "level": "Novice"},
        {"name": "scikit-learn", "score": 50, "level": "Apprentice"},  # same Kaggle links as PyTorch
        {"name": "Basket weaving", "score": 5, "level": "Novice"},
    ]
    plan = external_tests.training_plan(skills)
    assert [p["skill"] for p in plan["by_skill"]] == ["SQL", "scikit-learn"]
    assert plan["general"]


def test_every_link_is_https_on_a_known_platform():
    allowed = ("hackerrank.com", "exercism.org", "leetcode.com", "codeforces.com", "aws.amazon.com",
               "learn.microsoft.com", "cloud.google.com", "linuxfoundation.org", "hashicorp.com",
               "learngitbranching.js.org", "kaggle.com")
    for url in external_tests.all_urls():
        assert url.startswith("https://")
        assert any(domain in url for domain in allowed), url
