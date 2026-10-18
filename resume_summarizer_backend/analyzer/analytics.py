"""Turning a résumé into numbers you can check.

Two halves:
- `score_skills` takes the skills and evidence quotes the model extracted, throws
  away every quote that isn't actually in the résumé, and scores each skill from
  what survives using a fixed, published formula.
- `resume_quality` is pure Python: sections, contact details, bullet quality,
  length and employment gaps. No model involved, so it is fast and repeatable.
"""

import re
import unicodedata
from datetime import date
from difflib import SequenceMatcher

# --- Skill scoring ----------------------------------------------------------

# Points for the first piece of evidence of each kind. Paid work counts most;
# a bare entry in a skills list counts least.
EVIDENCE_WEIGHTS = {"job": 35, "metric": 25, "project": 25, "cert": 20, "listed": 10}
EXTRA_EVIDENCE_POINTS = 5   # each further verified quote of a kind already counted...
EXTRA_EVIDENCE_CAP = 10     # ...up to this many points in total
LISTED_ONLY_CAP = 30        # a skill that is only ever listed can't score higher
LEVELS = [(80, "Expert"), (55, "Adept"), (30, "Apprentice"), (1, "Novice"), (0, "Unproven")]
FUZZY_MATCH = 0.9           # share of a quote that must match the résumé verbatim

_PUNCT = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-",
                        "•": " ", "▪": " ", "●": " ", "◦": " ", "­": ""})


def normalize(text):
    text = unicodedata.normalize("NFKC", text).translate(_PUNCT).lower()
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)  # re-join words hyphenated across lines
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .,;:-*")


def quote_in_text(quote, normalized_text):
    """True if the quote appears in the résumé, allowing for small extraction noise."""
    q = normalize(quote)
    if len(q) < 3:
        return False
    if q in normalized_text:
        return True
    if len(q) < 12:
        return False
    match = SequenceMatcher(None, normalized_text, q, autojunk=False).find_longest_match(
        0, len(normalized_text), 0, len(q)
    )
    return match.size / len(q) >= FUZZY_MATCH


def name_pattern(name):
    """Matches the skill name as a whole word. "CI/CD" also matches "CI" or "CD" alone."""
    names = [name] + ([part for part in name.split("/") if part.strip()] if "/" in name else [])
    alternatives = "|".join(re.escape(n.strip()) for n in names)
    return re.compile(rf"(?<![\w+#.])(?:{alternatives})(?![\w+#])", re.I)


def mentions_skill(quote, name):
    """True if the quote names the skill. Words of 5+ letters may match by stem
    ("mentoring" matches "Mentored"); short names like Go or R must match exactly."""
    q = normalize(quote)
    if name_pattern(name).search(q):
        return True
    words = [w for w in re.findall(r"[a-z]+", name.lower()) if len(w) >= 5]
    return any(re.search(rf"\b{w[:5]}", q) for w in words)


def level_for(score):
    return next(label for floor, label in LEVELS if score >= floor)


def score_skill(evidence):
    verified = [e for e in evidence if e["verified"]]
    kinds = {e["type"] for e in verified}
    score = sum(EVIDENCE_WEIGHTS[k] for k in kinds)
    score += min(EXTRA_EVIDENCE_CAP, EXTRA_EVIDENCE_POINTS * (len(verified) - len(kinds)))
    if kinds == {"listed"}:
        score = min(score, LISTED_ONLY_CAP)
    return min(100, score)


# Categories for common skills, so a small model's labelling mistakes don't matter.
KNOWN_CATEGORIES = {
    **dict.fromkeys(["python", "java", "javascript", "typescript", "go", "golang", "rust", "c", "c++",
                     "c#", "kotlin", "swift", "scala", "ruby", "php", "r", "sql", "bash", "matlab"], "language"),
    **dict.fromkeys(["react", "angular", "vue", "next.js", "django", "flask", "fastapi", "spring",
                     "spring boot", "express", "node.js", "rails", ".net", "tailwind"], "framework"),
    **dict.fromkeys(["pytorch", "tensorflow", "keras", "scikit-learn", "pandas", "numpy", "spark",
                     "airflow", "mlflow", "hugging face", "transformers", "opencv", "xgboost",
                     "machine learning", "deep learning", "nlp", "computer vision", "llms"], "data_ml"),
    **dict.fromkeys(["aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "terraform",
                     "github actions", "jenkins", "ci/cd", "linux", "ansible", "helm"], "cloud_devops"),
    **dict.fromkeys(["postgresql", "postgres", "mysql", "mongodb", "redis", "sqlite", "dynamodb",
                     "elasticsearch", "cassandra", "snowflake", "bigquery"], "database"),
    **dict.fromkeys(["git", "jira", "figma", "postman", "tableau", "power bi", "excel"], "tool"),
}
# Which kind of evidence a mention counts as, by the section it sits in.
SECTION_EVIDENCE = {"experience": "job", "projects": "project", "skills": "listed", "certifications": "cert"}


def find_mentions(name, sections):
    """Every line in the résumé that names the skill, typed by its section.

    These are verified by construction: they are lines of the résumé itself.
    A mention in a job or project line that also has a number counts as a metric too.
    """
    pattern = name_pattern(name)
    found = []
    for section, line in sections:
        kind = SECTION_EVIDENCE.get(section)
        if kind is None or not pattern.search(line):
            continue
        quote = BULLET.sub("", line).strip()
        found.append({"type": kind, "quote": quote, "verified": True, "problem": None, "source": "scan"})
        if kind in ("job", "project") and re.search(r"\d", quote):
            found.append({"type": "metric", "quote": quote, "verified": True, "problem": None, "source": "scan"})
    return found


def score_skills(skill_claims, resume_text):
    """skill_claims: SkillClaim models from the LLM. Returns plain dicts, best first.

    Evidence comes from two places: the quotes the model gave (checked against the
    résumé and for naming the skill; failures are kept, marked and not scored) and a scan of the
    résumé for every line that names the skill.
    """
    normalized_text = normalize(resume_text)
    sections = split_sections(resume_text)
    skills = []
    for claim in skill_claims:
        evidence, seen = [], set()
        for item in claim.evidence:
            key = (item.type, normalize(item.quote))
            if key in seen:
                continue
            seen.add(key)
            # A quote counts only if it is really in the résumé AND is about this skill.
            if not quote_in_text(item.quote, normalized_text):
                problem = "not_found"
            elif not mentions_skill(item.quote, claim.name):
                problem = "off_topic"
            else:
                problem = None
            evidence.append({
                "type": item.type,
                "quote": item.quote.strip(),
                "verified": problem is None,
                "problem": problem,
                "source": "model",
            })
        for mention in find_mentions(claim.name, sections):
            line = normalize(mention["quote"])
            # Skip a scanned line the model already quoted (in full or in part) as the same kind.
            if any(e["type"] == mention["type"] and e["verified"] and normalize(e["quote"]) in line
                   for e in evidence):
                continue
            evidence.append(mention)
        evidence = evidence[:8]
        score = score_skill(evidence)
        skills.append({
            "name": claim.name,
            "category": KNOWN_CATEGORIES.get(claim.name.lower(), claim.category),
            "score": score,
            "level": level_for(score),
            "evidence": evidence,
            "verified_count": sum(e["verified"] for e in evidence),
            "rejected_count": sum(not e["verified"] for e in evidence),
        })
    return sorted(skills, key=lambda s: (-s["score"], s["name"].lower()))


def category_summary(skills):
    groups = {}
    for skill in skills:
        groups.setdefault(skill["category"], []).append(skill["score"])
    return sorted(
        ({"category": c, "average": round(sum(v) / len(v)), "count": len(v)} for c, v in groups.items()),
        key=lambda g: -g["average"],
    )


def power_level(skills):
    """Average of the five strongest skills: one headline number."""
    top = [s["score"] for s in skills[:5]]
    return round(sum(top) / len(top)) if top else 0


# --- Résumé quality ---------------------------------------------------------

SECTION_PATTERNS = {
    "summary": r"summary|profile|objective|about me",
    "experience": r"(work |professional )?experience|employment( history)?|work history",
    "education": r"education|academics?",
    "skills": r"(technical )?skills|technologies|tech stack|core competencies",
    "projects": r"(personal |academic |selected )?projects",
    "certifications": r"certifications?|certificates|licen[cs]es",
}
ACTION_VERBS = set("""
achieved added analysed analyzed architected automated boosted built championed coached
collaborated configured created cut debugged decreased defined delivered deployed designed
developed diagnosed directed drove eliminated enabled engineered enhanced established
evaluated expanded fixed founded generated grew guided handled headed implemented improved
increased initiated integrated introduced launched led maintained managed mentored migrated
modernized monitored negotiated optimised optimized orchestrated organized overhauled owned
pioneered planned presented prototyped published raised rebuilt redesigned reduced refactored
resolved restructured revamped saved scaled secured shipped simplified spearheaded streamlined
strengthened supervised taught tested trained transformed tuned upgraded wrote
""".split())
BULLET = re.compile(r"^\s*[•\-\*▪●◦–·]\s*")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?<!\d)(\+?\d[\d\s().-]{8,}\d)(?!\d)")
LINKEDIN = re.compile(r"linkedin\.com/", re.I)
GITHUB = re.compile(r"github\.com/|gitlab\.com/", re.I)
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}
_DATE = r"(?:(?P<{p}m>[A-Za-z]{{3,9}})\.?\s+|(?P<{p}n>\d{{1,2}})/)?(?P<{p}y>(?:19|20)\d\d)"
DATE_RANGE = re.compile(
    _DATE.format(p="s") + r"\s*(?:-|–|—|to|until)\s*(?:" + _DATE.format(p="e")
    + r"|(?P<present>present|current|now|today))",
    re.I,
)


def _section_of(line):
    stripped = line.strip().strip(":").lower()
    if len(stripped) > 40:
        return None
    for name, pattern in SECTION_PATTERNS.items():
        if re.fullmatch(pattern, stripped):
            return name
    return None


def _month_index(match, prefix):
    year = int(match.group(f"{prefix}y"))
    month_name = (match.group(f"{prefix}m") or "")[:3].lower()
    month_num = match.group(f"{prefix}n")
    month = MONTHS.get(month_name) or (int(month_num) if month_num and 1 <= int(month_num) <= 12 else None)
    return year * 12 + ((month or (1 if prefix == "s" else 12)) - 1)


def employment_gaps(text, section_lines, today=None):
    """Gaps of more than 6 months between date ranges in the experience section."""
    today = today or date.today()
    now = today.year * 12 + today.month - 1
    lines = section_lines.get("experience") or text.splitlines()
    ranges = []
    for match in DATE_RANGE.finditer("\n".join(lines)):
        start = _month_index(match, "s")
        end = now if match.group("present") else _month_index(match, "e")
        if start <= end <= now + 1:
            ranges.append((start, end))
    ranges.sort()
    gaps, latest_end = [], None
    for start, end in ranges:
        if latest_end is not None and start - latest_end > 6:
            gaps.append({"from": _fmt(latest_end), "to": _fmt(start), "months": start - latest_end})
        latest_end = end if latest_end is None else max(latest_end, end)
    return gaps


def _fmt(index):
    year, month = divmod(index, 12)
    return f"{['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][month]} {year}"


def _bullets(section_lines):
    """Achievement lines: bulleted lines, or long-enough lines under experience/projects."""
    bullets = []
    for section, lines in section_lines.items():
        for line in lines:
            words = BULLET.sub("", line).split()
            if BULLET.match(line) and len(words) >= 3:
                bullets.append(words)
            elif section in ("experience", "projects") and len(words) >= 8:
                bullets.append(words)
    return bullets


QUALITY_CHECKS = [
    # id, label, weight, tip
    ("email", "Email address", 10, "Add an email address recruiters can reply to."),
    ("phone", "Phone number", 5, "Add a phone number."),
    ("links", "LinkedIn or GitHub link", 10, "Link your LinkedIn or GitHub profile."),
    ("experience", "Experience section", 15, "Add an Experience section with dated roles."),
    ("education", "Education section", 10, "Add an Education section."),
    ("skills", "Skills section", 10, "Add a Skills section so ATS filters can match keywords."),
    ("length", "Length 350-1100 words", 10, "Aim for 350-1100 words: one or two pages."),
    ("quantified", "40%+ of bullets have numbers", 15, "Quantify results: %, $, users, time saved."),
    ("verbs", "60%+ of bullets start with a verb", 10, "Start bullets with a strong verb (Built, Cut, Led)."),
    ("gaps", "No unexplained gaps over 6 months", 5, "Explain long gaps (study, travel, caregiving)."),
]
RANKS = [(90, "S"), (75, "A"), (60, "B"), (45, "C"), (0, "D")]


def split_sections(text):
    """[(section, line), ...] for every non-heading line; text before any heading is "header"."""
    current, out = "header", []
    for line in text.splitlines():
        name = _section_of(line)
        if name:
            current = name
        elif line.strip():
            out.append((current, line))
    return out


def resume_quality(text, today=None):
    headings = {_section_of(line) for line in text.splitlines()} - {None}
    section_lines = {}
    for section, line in split_sections(text):
        section_lines.setdefault(section, []).append(line)

    bullets = _bullets(section_lines)
    quantified = sum(any(re.search(r"\d", w) for w in b) for b in bullets)
    verb_led = sum(b[0].lower().strip(",.") in ACTION_VERBS for b in bullets)
    quantified_pct = round(100 * quantified / len(bullets)) if bullets else 0
    verb_pct = round(100 * verb_led / len(bullets)) if bullets else 0
    word_count = len(text.split())
    gaps = employment_gaps(text, section_lines, today)
    contact = {
        "email": bool(EMAIL.search(text)),
        "phone": bool(PHONE.search(text)),
        "linkedin": bool(LINKEDIN.search(text)),
        "github": bool(GITHUB.search(text)),
    }
    sections = {name: name in headings for name in SECTION_PATTERNS}
    passed = {
        "email": contact["email"],
        "phone": contact["phone"],
        "links": contact["linkedin"] or contact["github"],
        "experience": sections["experience"],
        "education": sections["education"],
        "skills": sections["skills"],
        "length": 350 <= word_count <= 1100,
        "quantified": bool(bullets) and quantified_pct >= 40,
        "verbs": bool(bullets) and verb_pct >= 60,
        "gaps": not gaps,
    }
    checks = [{"id": cid, "label": label, "passed": passed[cid], "tip": tip}
              for cid, label, _, tip in QUALITY_CHECKS]
    score = sum(weight for cid, _, weight, _ in QUALITY_CHECKS if passed[cid])
    return {
        "score": score,
        "rank": next(rank for floor, rank in RANKS if score >= floor),
        "word_count": word_count,
        "bullet_count": len(bullets),
        "quantified_pct": quantified_pct,
        "action_verb_pct": verb_pct,
        "sections": sections,
        "contact": contact,
        "gaps": gaps,
        "checks": checks,
    }
