"""
Post-scrape intelligence updater.

After new jobs are scraped and stored in the DB, this module:
  1. Extracts skills from the new jobs → upserts SkillTrend rows.
  2. Computes / refreshes AiVulnerabilityScore for each new title_norm.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import date

from app import db
from app.models import AiVulnerabilityScore, City, Job, SkillTrend

# ── Skill extraction patterns (same canonical list as market.py) ───

_IT_SKILLS_RAW = [
    ("python", [r"\bpython\b"]), ("java", [r"\bjava\b(?!\s*script)"]),
    ("javascript", [r"\bjavascript\b", r"\bjs\b"]), ("typescript", [r"\btypescript\b"]),
    ("c++", [r"\bc\+\+\b", r"\bcpp\b"]), ("c#", [r"\bc#\b", r"\bcsharp\b"]),
    ("golang", [r"\bgolang\b"]), ("rust", [r"\brust\b"]), ("ruby", [r"\bruby\b"]),
    ("php", [r"\bphp\b"]), ("swift", [r"\bswift\b"]), ("kotlin", [r"\bkotlin\b"]),
    ("scala", [r"\bscala\b"]), ("perl", [r"\bperl\b"]),
    ("sql", [r"\bsql\b(?!\s*server)", r"\bplsql\b", r"\btsql\b"]),
    ("react", [r"\breact\b", r"\breactjs\b"]), ("angular", [r"\bangular\b"]),
    ("vue.js", [r"\bvue\b", r"\bvuejs\b"]), ("node.js", [r"\bnode\s?js\b", r"\bnodejs\b"]),
    ("django", [r"\bdjango\b"]), ("flask", [r"\bflask\b"]),
    ("spring boot", [r"\bspring\s?boot\b", r"\bspring\b"]),
    (".net", [r"\b\.net\b", r"\bdotnet\b", r"\basp\.net\b"]),
    ("aws", [r"\baws\b"]), ("azure", [r"\bazure\b"]),
    ("gcp", [r"\bgcp\b", r"\bgoogle cloud\b"]),
    ("docker", [r"\bdocker\b"]), ("kubernetes", [r"\bkubernetes\b", r"\bk8s\b"]),
    ("terraform", [r"\bterraform\b"]), ("jenkins", [r"\bjenkins\b"]),
    ("ci/cd", [r"\bci.?cd\b"]), ("git", [r"\bgit\b(?!hub)"]),
    ("linux", [r"\blinux\b"]), ("devops", [r"\bdevops\b"]),
    ("mysql", [r"\bmysql\b"]), ("postgresql", [r"\bpostgresql\b", r"\bpostgres\b"]),
    ("mongodb", [r"\bmongodb\b", r"\bmongo\b"]), ("redis", [r"\bredis\b"]),
    ("machine learning", [r"\bmachine learning\b", r"\bml\b"]),
    ("deep learning", [r"\bdeep learning\b"]),
    ("artificial intelligence", [r"\bartificial intellig\b", r"\bai\b"]),
    ("nlp", [r"\bnlp\b", r"\bnatural language\b"]),
    ("tensorflow", [r"\btensorflow\b"]), ("pytorch", [r"\bpytorch\b"]),
    ("pandas", [r"\bpandas\b"]), ("spark", [r"\bspark\b", r"\bpyspark\b"]),
    ("kafka", [r"\bkafka\b"]), ("tableau", [r"\btableau\b"]),
    ("power bi", [r"\bpower bi\b", r"\bpowerbi\b"]),
    ("generative ai", [r"\bgenerat.{0,4}\bai\b", r"\bllm\b", r"\bgpt\b", r"\blangchain\b"]),
    ("selenium", [r"\bselenium\b"]), ("agile/scrum", [r"\bagile\b", r"\bscrum\b"]),
    ("rest api", [r"\brest\s?api\b", r"\brestful\b"]),
    ("microservices", [r"\bmicroservice\b"]),
    ("react native", [r"\breact native\b"]), ("flutter", [r"\bflutter\b"]),
]

_SKILL_PATTERNS = [
    (name, [re.compile(p, re.IGNORECASE) for p in pats])
    for name, pats in _IT_SKILLS_RAW
]

# AI-heavy keywords that bump vulnerability score
_AI_KEYWORDS = re.compile(
    r"\b(ai|artificial.intellig|machine.learn|deep.learn|automat|llm|gpt|chatbot"
    r"|nlp|computer.vision|generative)\b",
    re.IGNORECASE,
)

# Routine / repetitive task keywords (more automatable)
_ROUTINE_KEYWORDS = re.compile(
    r"\b(data.entry|manual.test|copy.?paste|repetitive|routine|clerical|admin"
    r"|bookkeeping|transcription)\b",
    re.IGNORECASE,
)


def _extract_skills(text: str) -> set[str]:
    found = set()
    for skill_name, patterns in _SKILL_PATTERNS:
        for pat in patterns:
            if pat.search(text):
                found.add(skill_name)
                break
    return found


def _normalize_title(title: str) -> str:
    t = title.strip().lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _compute_vuln_score(title: str, description: str) -> tuple[int, float, str]:
    """Heuristic AI vulnerability score for a job role.

    Returns (score 0-100, confidence 0-1, reason).
    """
    text = f"{title} {description}".lower()

    ai_hits = len(_AI_KEYWORDS.findall(text))
    routine_hits = len(_ROUTINE_KEYWORDS.findall(text))

    # Base score: routine tasks → higher risk, AI keywords → role already adapting → lower risk
    score = min(100, max(0, 30 + routine_hits * 15 - ai_hits * 5))

    # Confidence increases with more textual signal
    word_count = len(text.split())
    confidence = min(0.9, 0.3 + word_count / 500)

    reasons = []
    if routine_hits:
        reasons.append(f"{routine_hits} routine-task signals detected")
    if ai_hits:
        reasons.append(f"{ai_hits} AI/automation mentions (role is adapting)")
    if not reasons:
        reasons.append("Moderate baseline risk; limited textual signals")

    return score, round(confidence, 2), "; ".join(reasons)


# ── Public API ────────────────────────────────────────────────


def update_skill_trends(job_ids: list[int] | None = None) -> dict:
    """Extract skills from (new) jobs and upsert into skill_trends.

    If job_ids is given, only those jobs are processed.
    Otherwise all jobs with posted_date are processed (full rebuild).
    """
    q = (
        db.session.query(Job.title_norm, Job.description, Job.posted_date, Job.city_id)
        .filter(Job.posted_date.isnot(None))
    )
    if job_ids:
        q = q.filter(Job.id.in_(job_ids))

    jobs = q.all()
    if not jobs:
        return {"skill_trends_upserted": 0, "jobs_processed": 0}

    # {(skill, city_id, period): demand_count}
    demand: dict[tuple[str, int | None, date], int] = defaultdict(int)

    for title_norm, desc, posted_date, city_id in jobs:
        text = (title_norm or "") + " " + (desc or "")
        skills = _extract_skills(text)
        period = posted_date.replace(day=1)
        for skill in skills:
            demand[(skill, city_id, period)] += 1

    upserted = 0
    for (skill, city_id, period), count in demand.items():
        existing = SkillTrend.query.filter_by(
            skill_name=skill, city_id=city_id, period=period
        ).first()
        if existing:
            existing.demand_count += count
        else:
            db.session.add(SkillTrend(
                skill_name=skill,
                city_id=city_id,
                period=period,
                demand_count=count,
                change_pct=0.0,
            ))
        upserted += 1

    db.session.commit()
    return {"skill_trends_upserted": upserted, "jobs_processed": len(jobs)}


def update_ai_vulnerability(job_ids: list[int] | None = None) -> dict:
    """Compute / refresh AI vulnerability scores for newly scraped job titles.

    Groups jobs by (title_norm, city_id), computes a heuristic score,
    and upserts into ai_vulnerability_scores.
    """
    q = db.session.query(Job).filter(Job.title_norm.isnot(None))
    if job_ids:
        q = q.filter(Job.id.in_(job_ids))

    jobs = q.all()
    if not jobs:
        return {"vuln_scores_upserted": 0}

    # Group descriptions by (title_norm, city_id)
    groups: dict[tuple[str, int | None], list[str]] = defaultdict(list)
    for job in jobs:
        groups[(job.title_norm, job.city_id)].append(job.description or "")

    upserted = 0
    for (title_norm, city_id), descriptions in groups.items():
        merged_text = " ".join(descriptions[:10])  # cap to avoid huge strings
        score, confidence, reason = _compute_vuln_score(title_norm, merged_text)

        existing = AiVulnerabilityScore.query.filter_by(
            job_title_norm=title_norm, city_id=city_id
        ).first()
        if existing:
            existing.score = score
            existing.confidence = confidence
            existing.reason = reason
        else:
            db.session.add(AiVulnerabilityScore(
                job_title_norm=title_norm,
                city_id=city_id,
                score=score,
                confidence=confidence,
                reason=reason,
            ))
        upserted += 1

    db.session.commit()
    return {"vuln_scores_upserted": upserted}
