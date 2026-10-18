from datetime import date

from analyzer import analytics
from analyzer.schemas import SkillClaim


def claim(name, *evidence, category="language"):
    return SkillClaim(name=name, category=category,
                      evidence=[{"type": t, "quote": q} for t, q in evidence])


def test_quote_verification_accepts_real_quotes_and_rejects_invented_ones(sample_text):
    text = analytics.normalize(sample_text)
    assert analytics.quote_in_text("Built a PyTorch recommendation model", text)
    # Case, curly quotes, dashes and line breaks don't matter.
    assert analytics.quote_in_text("built a pytorch   RECOMMENDATION\nmodel", text)
    assert analytics.quote_in_text("AWS Certified Machine Learning – Specialty", text)
    # A paraphrase or an invention does not pass.
    assert not analytics.quote_in_text("Led a team of 12 engineers at Google", text)
    assert not analytics.quote_in_text("Rust", text)
    assert not analytics.quote_in_text("ab", text)


def test_quote_verification_tolerates_small_extraction_noise(sample_text):
    text = analytics.normalize(sample_text)
    # One word dropped from a long quote, as happens when a PDF line wraps oddly.
    assert analytics.quote_in_text(
        "Migrated nightly feature pipelines from cron scripts to Airflow, reducing failed runs by", text)


def test_quotes_must_be_about_the_skill(sample_text):
    [python] = analytics.score_skills([claim(
        "Python",
        ("job", "Built a PyTorch recommendation model"),          # real line, but not about Python
        ("cert", "AWS Certified Machine Learning - Specialty"),   # same
    )], sample_text)
    model_quotes = [e for e in python["evidence"] if e["source"] == "model"]
    assert [e["problem"] for e in model_quotes] == ["off_topic", "off_topic"]
    assert not any(e["verified"] for e in model_quotes)
    # The résumé scan still finds the real Python lines.
    assert {e["type"] for e in python["evidence"] if e["verified"]} == {"job", "metric", "project", "listed"}


def test_mentions_skill():
    assert analytics.mentions_skill("Mentored two junior engineers", "mentoring")
    assert analytics.mentions_skill("Wrote SQL transformations", "SQL")
    assert not analytics.mentions_skill("Worked at Google", "Go")
    assert analytics.mentions_skill("Shipped services in Go and Rust", "Go")
    assert analytics.mentions_skill("flags feature drift in production models", "feature drift monitoring")
    assert analytics.mentions_skill("set up GitHub Actions CI", "CI/CD")
    assert not analytics.mentions_skill("a CIDR block", "CI/CD")


def test_scoring_formula():
    def ev(*kinds):
        return [{"type": k, "verified": True} for k in kinds]

    assert analytics.score_skill(ev("listed")) == 10
    assert analytics.score_skill(ev("listed", "listed", "listed", "listed")) == 20  # extras capped at +10
    assert analytics.score_skill(ev("job", "metric", "project", "cert", "listed")) == 100
    assert analytics.score_skill(ev("job", "listed")) == 45
    assert analytics.score_skill([{"type": "job", "verified": False}]) == 0


def test_listed_only_skills_are_capped():
    evidence = [{"type": "listed", "verified": True}] * 10
    assert analytics.score_skill(evidence) <= analytics.LISTED_ONLY_CAP


def test_score_skills_drops_invented_evidence(sample_text):
    skills = analytics.score_skills([
        claim("PyTorch",
              ("job", "Built a PyTorch recommendation model"),
              ("metric", "lifted click-through rate by 14%"),
              ("listed", "PyTorch")),
        claim("Rust", ("job", "Rewrote the payments engine in Rust")),
    ], sample_text)
    pytorch, rust = skills
    assert pytorch["name"] == "PyTorch" and pytorch["score"] == 70
    assert pytorch["level"] == "Adept" and pytorch["verified_count"] == 3
    assert rust["score"] == 0 and rust["level"] == "Unproven"
    assert rust["rejected_count"] == 1 and rust["evidence"][0]["verified"] is False
    assert rust["evidence"][0]["problem"] == "not_found"


def test_scan_finds_every_mention_and_types_it_by_section(sample_text):
    mentions = analytics.find_mentions("PyTorch", analytics.split_sections(sample_text))
    kinds = sorted(m["type"] for m in mentions)
    assert kinds == ["job", "listed", "metric"]
    assert all(m["verified"] and m["source"] == "scan" for m in mentions)
    # Word boundaries: "Go" must not match "Google", and "Java" must not match "JavaScript".
    sections = [("experience", "Built tools at Google with JavaScript")]
    assert analytics.find_mentions("Go", sections) == []
    assert analytics.find_mentions("Java", sections) == []
    assert analytics.find_mentions("C++", [("skills", "C, C++, Rust")])[0]["type"] == "listed"


def test_a_weak_model_with_one_quote_still_gets_full_credit(sample_text):
    # Small models often return a single listed quote. The scan fills in the rest.
    [skill] = analytics.score_skills([claim("PyTorch", ("listed", "PyTorch"))], sample_text)
    assert {e["type"] for e in skill["evidence"]} == {"listed", "job", "metric"}
    assert skill["score"] == 70


def test_known_skills_get_a_fixed_category(sample_text):
    [skill] = analytics.score_skills([claim("Kubernetes", category="tool")], sample_text)
    assert skill["category"] == "cloud_devops"


def test_levels():
    assert [analytics.level_for(s) for s in (0, 1, 30, 55, 80, 100)] == [
        "Unproven", "Novice", "Apprentice", "Adept", "Expert", "Expert"]


def test_category_summary_and_power_level():
    skills = [{"category": "language", "score": 80}, {"category": "language", "score": 40},
              {"category": "tool", "score": 10}]
    assert analytics.category_summary(skills) == [
        {"category": "language", "average": 60, "count": 2},
        {"category": "tool", "average": 10, "count": 1},
    ]
    assert analytics.power_level(skills) == 43
    assert analytics.power_level([]) == 0


def test_resume_quality_on_sample(sample_text):
    quality = analytics.resume_quality(sample_text, today=date(2026, 10, 1))
    checks = {c["id"]: c["passed"] for c in quality["checks"]}
    assert quality["contact"] == {"email": True, "phone": True, "linkedin": True, "github": True}
    assert all(quality["sections"][s] for s in ("summary", "experience", "education", "skills", "projects"))
    assert quality["bullet_count"] >= 9
    assert quality["quantified_pct"] >= 40 and checks["quantified"]
    assert quality["action_verb_pct"] >= 60 and checks["verbs"]
    # Aug 2021 -> Mar 2022 is a 7-month gap between the two jobs.
    assert quality["gaps"] == [{"from": "Aug 2021", "to": "Mar 2022", "months": 7}]
    assert not checks["gaps"]
    assert quality["score"] == 100 - 10 - 5 and quality["rank"] == "A"  # length and gaps fail


def test_resume_quality_on_a_bare_resume():
    quality = analytics.resume_quality("John\nI like computers.\n")
    assert quality["score"] == 5  # only "no gaps" passes
    assert quality["rank"] == "D"
    assert quality["bullet_count"] == 0


def test_gap_detection_handles_formats():
    text = "Experience\nAcme 01/2018 - 06/2019\nBeta Jan 2021 to Present\nGamma 2015 - 2016\n"
    gaps = analytics.employment_gaps(text, {"experience": text.splitlines()}, today=date(2026, 1, 1))
    assert gaps == [
        {"from": "Dec 2016", "to": "Jan 2018", "months": 13},
        {"from": "Jun 2019", "to": "Jan 2021", "months": 19},
    ]
