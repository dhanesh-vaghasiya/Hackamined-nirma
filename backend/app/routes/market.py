from __future__ import annotations

from datetime import date, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import func, desc, case, extract, or_, and_

from app import db
from app.models import (
    AiVulnerabilityScore,
    City,
    Job,
    JobSkill,
    SkillTrend,
)

market_bp = Blueprint("market", __name__)


def _get_timeframe_start(tf: str) -> date:
    today = date.today()
    if tf == "7d":
        return today - timedelta(days=7)
    if tf == "30d":
        return today - timedelta(days=30)
    if tf == "90d":
        return today - timedelta(days=90)
    return today - timedelta(days=365)


@market_bp.route("/summary", methods=["GET"])
def market_summary():
    """Dashboard summary cards."""
    total_jobs = db.session.query(func.count(Job.id)).scalar() or 0
    unique_roles = db.session.query(func.count(func.distinct(Job.title_norm))).scalar() or 0
    unique_cities = db.session.query(func.count(func.distinct(City.id))).join(Job, Job.city_id == City.id).scalar() or 0
    vuln_count = db.session.query(func.count(AiVulnerabilityScore.id)).scalar() or 0

    # Top roles
    top_roles = (
        db.session.query(Job.title_norm, func.count(Job.id).label("cnt"))
        .filter(Job.title_norm.isnot(None))
        .group_by(Job.title_norm)
        .order_by(desc("cnt"))
        .limit(6)
        .all()
    )
    # Top cities
    top_cities = (
        db.session.query(City.name, func.count(Job.id).label("cnt"))
        .join(Job, Job.city_id == City.id)
        .group_by(City.name)
        .order_by(desc("cnt"))
        .limit(6)
        .all()
    )

    return jsonify({
        "rows": total_jobs,
        "unique_roles": unique_roles,
        "unique_cities": unique_cities,
        "vulnerability_roles": vuln_count,
        "top_roles": [{"role": r, "count": c} for r, c in top_roles],
        "top_cities": [{"city": c, "count": n} for c, n in top_cities],
    })


@market_bp.route("/hiring-trends", methods=["GET"])
def hiring_trends():
    """Hiring volume timeline + top city/role combos."""
    limit = max(5, min(200, int(request.args.get("limit", 60))))
    city_filter = (request.args.get("city") or "").strip().lower()
    timeframe = request.args.get("timeframe", "1yr")
    start_date = _get_timeframe_start(timeframe)

    # Monthly hiring timeline
    q = (
        db.session.query(
            func.to_char(Job.posted_date, 'YYYY-MM').label("month"),
            func.count(Job.id).label("count"),
        )
        .filter(Job.posted_date.isnot(None), Job.posted_date >= start_date)
    )
    if city_filter and city_filter != "all-india":
        q = q.join(City, Job.city_id == City.id).filter(func.lower(City.name) == city_filter)

    timeline = (
        q.group_by("month")
        .order_by("month")
        .limit(limit)
        .all()
    )

    # Top hiring role+city combos
    top_q = (
        db.session.query(
            Job.title_norm,
            City.name.label("city"),
            func.count(Job.id).label("demand"),
        )
        .join(City, Job.city_id == City.id)
        .filter(Job.posted_date.isnot(None), Job.posted_date >= start_date)
    )
    if city_filter and city_filter != "all-india":
        top_q = top_q.filter(func.lower(City.name) == city_filter)

    top_city_roles = (
        top_q.group_by(Job.title_norm, City.name)
        .order_by(desc("demand"))
        .limit(20)
        .all()
    )

    return jsonify({
        "timeline": [{"month": m, "count": c} for m, c in timeline],
        "top_city_roles": [
            {"job_title": t or "Unknown", "location": ci, "latest_demand": d}
            for t, ci, d in top_city_roles
        ],
    })


@market_bp.route("/skills-intel", methods=["GET"])
def skills_intel():
    """Rising and declining skills + radar chart data.

    Compares the latest 3-month quarter vs the previous 3-month quarter
    for stable, meaningful trend percentages.
    """
    city_filter = (request.args.get("city") or "").strip().lower()

    # Get all distinct periods sorted descending
    all_periods = [
        r[0]
        for r in db.session.query(SkillTrend.period)
        .distinct()
        .order_by(desc(SkillTrend.period))
        .all()
    ]
    if len(all_periods) < 4:
        return jsonify({"rising": [], "declining": [], "radar": []})

    # Recent quarter = latest 3 months, previous quarter = 3 months before that
    recent_periods = all_periods[:3]
    prev_periods = all_periods[3:6]

    def _demand_by_skill(periods):
        q = (
            db.session.query(
                SkillTrend.skill_name,
                func.sum(SkillTrend.demand_count).label("demand"),
            )
            .filter(SkillTrend.period.in_(periods))
        )
        if city_filter and city_filter != "all-india":
            q = q.join(City, SkillTrend.city_id == City.id).filter(
                func.lower(City.name) == city_filter
            )
        return {r.skill_name: r.demand for r in q.group_by(SkillTrend.skill_name).all()}

    current = _demand_by_skill(recent_periods)
    previous = _demand_by_skill(prev_periods)

    # Minimum demand threshold — ignore skills with very low counts
    min_demand = 20

    skills = []
    for skill, cur_demand in current.items():
        if cur_demand < min_demand:
            continue
        prev_demand = previous.get(skill, 0)
        if prev_demand > 0:
            pct = round(((cur_demand - prev_demand) / prev_demand) * 100, 1)
        elif cur_demand > 0:
            pct = 100.0
        else:
            pct = 0.0
        skills.append({
            "skill": skill,
            "percent_change": pct,
            "latest_demand": cur_demand,
            "market_direction": "rising" if pct > 5 else ("declining" if pct < -5 else "stable"),
        })

    rising = sorted(skills, key=lambda x: x["percent_change"], reverse=True)[:15]
    declining = sorted(skills, key=lambda x: x["percent_change"])[:15]

    # Radar: top 6 by absolute demand, normalized to 0-100
    top_by_demand = sorted(skills, key=lambda x: x["latest_demand"], reverse=True)[:6]
    max_demand = max((s["latest_demand"] for s in top_by_demand), default=1)
    radar = [
        {
            "skill": s["skill"],
            "demand": min(100, int((s["latest_demand"] / max_demand) * 100)),
            "supply": min(100, int((s["latest_demand"] / max_demand) * 63)),
        }
        for s in top_by_demand
    ]

    return jsonify({"rising": rising, "declining": declining, "radar": radar})


@market_bp.route("/ai-vulnerability", methods=["GET"])
def ai_vulnerability():
    """AI Vulnerability Index — full dashboard payload.

    Returns:
        top_high_risk: 20 highest-scored roles
        top_low_risk: 20 lowest-scored roles
        signals: hiring decline, ai_tool_mentions, replacement_ratio
        trend_direction: is overall risk rising or falling?
        methodology: visible scoring explanation
        city_heatmap: job counts per city (for map view)
    """
    city_filter = (request.args.get("city") or "").strip().lower()

    # ── Helper: build an item dict for a vuln row ──
    def _build_item(role_name, score, confidence, reason, city_name,
                    recent_map, prev_map):
        cur = recent_map.get(role_name, 0)
        prev = prev_map.get(role_name, 0)
        if prev > 0:
            trend = round(((cur - prev) / prev) * 100, 1)
        elif cur > 0:
            trend = 100.0
        else:
            trend = 0.0
        return {
            "role": role_name,
            "city": city_name or "All India",
            "riskScore": score,
            "confidence": round(confidence or 0, 2),
            "riskReason": reason or "",
            "riskLevel": (
                "Critical" if score >= 75
                else ("High" if score >= 50
                      else ("Medium" if score >= 25 else "Low"))
            ),
            "hiringTrend": trend,
            "latestDemand": cur,
        }

    # ── Fetch time periods for trend computation ──
    all_periods = [
        r[0] for r in db.session.query(
            func.date_trunc("month", Job.posted_date).label("m")
        ).filter(Job.posted_date.isnot(None))
        .distinct().order_by(desc("m")).all()
    ]
    recent_periods = all_periods[:3] if len(all_periods) >= 3 else all_periods
    prev_periods = all_periods[3:6] if len(all_periods) >= 6 else []

    def _demand_map(role_names, periods):
        if not periods or not role_names:
            return {}
        q = (db.session.query(Job.title_norm, func.count(Job.id).label("d"))
             .filter(Job.title_norm.in_(role_names),
                     Job.posted_date.isnot(None),
                     func.date_trunc("month", Job.posted_date).in_(periods)))
        if city_filter and city_filter != "all-india":
            q = q.join(City, Job.city_id == City.id).filter(func.lower(City.name) == city_filter)
        return {r.title_norm: r.d for r in q.group_by(Job.title_norm).all()}

    # ── 1. Top 20 HIGHEST risk ──
    high_q = (db.session.query(
        AiVulnerabilityScore.job_title_norm,
        AiVulnerabilityScore.score,
        AiVulnerabilityScore.confidence,
        AiVulnerabilityScore.reason,
        City.name.label("city"),
    ).outerjoin(City, AiVulnerabilityScore.city_id == City.id))
    if city_filter and city_filter != "all-india":
        high_q = high_q.filter(func.lower(City.name) == city_filter)
    high_rows = high_q.order_by(desc(AiVulnerabilityScore.score)).limit(20).all()

    high_names = [r.job_title_norm for r in high_rows]
    hr_recent = _demand_map(high_names, recent_periods)
    hr_prev = _demand_map(high_names, prev_periods)
    top_high = [_build_item(r.job_title_norm, r.score, r.confidence, r.reason,
                            r.city, hr_recent, hr_prev) for r in high_rows]

    # ── 2. Top 20 LOWEST risk ──
    low_q = (db.session.query(
        AiVulnerabilityScore.job_title_norm,
        AiVulnerabilityScore.score,
        AiVulnerabilityScore.confidence,
        AiVulnerabilityScore.reason,
        City.name.label("city"),
    ).outerjoin(City, AiVulnerabilityScore.city_id == City.id))
    if city_filter and city_filter != "all-india":
        low_q = low_q.filter(func.lower(City.name) == city_filter)
    low_rows = low_q.order_by(AiVulnerabilityScore.score.asc()).limit(20).all()

    low_names = [r.job_title_norm for r in low_rows]
    lr_recent = _demand_map(low_names, recent_periods)
    lr_prev = _demand_map(low_names, prev_periods)
    top_low = [_build_item(r.job_title_norm, r.score, r.confidence, r.reason,
                           r.city, lr_recent, lr_prev) for r in low_rows]

    # ── 3. Signals ──
    # 3a. Hiring decline: roles with biggest drop in demand (recent vs prev)
    decline_q = (
        db.session.query(
            Job.title_norm,
            func.sum(case((func.date_trunc("month", Job.posted_date).in_(recent_periods), 1), else_=0)).label("recent"),
            func.sum(case((func.date_trunc("month", Job.posted_date).in_(prev_periods), 1), else_=0)).label("prev"),
        )
        .filter(Job.posted_date.isnot(None), Job.title_norm.isnot(None))
    )
    if city_filter and city_filter != "all-india":
        decline_q = decline_q.join(City, Job.city_id == City.id).filter(func.lower(City.name) == city_filter)
    decline_rows = decline_q.group_by(Job.title_norm).having(
        func.sum(case((func.date_trunc("month", Job.posted_date).in_(prev_periods), 1), else_=0)) > 5
    ).all()

    hiring_declines = []
    for r in decline_rows:
        rec, pre = int(r.recent or 0), int(r.prev or 0)
        if pre > 0:
            pct = round(((rec - pre) / pre) * 100, 1)
            if pct < -10:
                hiring_declines.append({"role": r.title_norm, "recent": rec, "previous": pre, "changePct": pct})
    hiring_declines.sort(key=lambda x: x["changePct"])
    hiring_declines = hiring_declines[:15]

    # 3b. AI tool mentions in job descriptions
    AI_KEYWORDS = [
        "artificial intelligence", "machine learning", "deep learning",
        "chatgpt", "openai", "llm", "generative ai", "gen ai", "copilot",
        "automation", "rpa", "robotic process", "ai-powered", "ai powered",
        "neural network", "nlp", "natural language processing", "computer vision",
    ]
    ai_mention_clause = or_(*[
        func.lower(Job.description).contains(kw) for kw in AI_KEYWORDS
    ])
    total_with_desc = db.session.query(func.count(Job.id)).filter(
        Job.description.isnot(None), Job.description != ""
    ).scalar() or 1
    ai_mention_count = db.session.query(func.count(Job.id)).filter(
        Job.description.isnot(None), ai_mention_clause
    ).scalar() or 0
    ai_mention_pct = round((ai_mention_count / total_with_desc) * 100, 1)

    # Top roles with most AI mentions
    ai_role_mentions = (
        db.session.query(Job.title_norm, func.count(Job.id).label("cnt"))
        .filter(Job.description.isnot(None), ai_mention_clause, Job.title_norm.isnot(None))
        .group_by(Job.title_norm)
        .order_by(desc("cnt"))
        .limit(10)
        .all()
    )

    # 3c. Role replacement ratio: roles where AI vuln score > 70 AND demand declining
    high_vuln_roles = {
        r[0] for r in db.session.query(AiVulnerabilityScore.job_title_norm)
        .filter(AiVulnerabilityScore.score >= 70).all()
    }
    replacement_candidates = [
        d for d in hiring_declines if d["role"] in high_vuln_roles
    ]

    signals = {
        "hiring_declines": hiring_declines,
        "ai_tool_mentions": {
            "total_jobs_with_desc": total_with_desc,
            "jobs_mentioning_ai": ai_mention_count,
            "pct": ai_mention_pct,
            "top_roles": [{"role": r.title_norm, "count": r.cnt} for r in ai_role_mentions],
        },
        "replacement_ratio": {
            "high_vuln_declining_roles": len(replacement_candidates),
            "total_high_vuln_roles": len(high_vuln_roles),
            "ratio_pct": round((len(replacement_candidates) / max(len(high_vuln_roles), 1)) * 100, 1),
            "roles": replacement_candidates[:10],
        },
    }

    # ── 4. Trend direction: is overall risk rising or falling? ──
    avg_score = db.session.query(func.avg(AiVulnerabilityScore.score)).scalar() or 50
    total_scored = db.session.query(func.count(AiVulnerabilityScore.id)).scalar() or 0
    high_risk_count = db.session.query(func.count(AiVulnerabilityScore.id)).filter(
        AiVulnerabilityScore.score >= 70).scalar() or 0
    low_risk_count = db.session.query(func.count(AiVulnerabilityScore.id)).filter(
        AiVulnerabilityScore.score <= 30).scalar() or 0

    # ── 5. City heatmap: job counts + avg vulnerability per city ──
    # Scores have city_id=NULL, so join through jobs.title_norm
    city_jobs = (
        db.session.query(City.name, func.count(Job.id).label("job_count"))
        .join(Job, Job.city_id == City.id)
        .group_by(City.name)
        .order_by(desc("job_count"))
        .all()
    )
    # Avg vuln per city — match via distinct role names in each city
    city_vuln = dict(
        db.session.query(
            City.name,
            func.avg(AiVulnerabilityScore.score),
        )
        .join(Job, Job.city_id == City.id)
        .join(AiVulnerabilityScore,
              AiVulnerabilityScore.job_title_norm == Job.title_norm)
        .group_by(City.name)
        .all()
    )

    return jsonify({
        "top_high_risk": top_high,
        "top_low_risk": top_low,
        "signals": signals,
        "overview": {
            "avg_score": round(avg_score, 1),
            "total_scored": total_scored,
            "high_risk_count": high_risk_count,
            "low_risk_count": low_risk_count,
        },
        "city_heatmap": [
            {
                "city": h.name,
                "jobCount": int(h.job_count),
                "avgVuln": round(float(city_vuln.get(h.name, 0) or 0), 1),
            }
            for h in city_jobs
        ],
    })


# ── Skill-extraction helpers (same logic as rebuild_skill_trends.py) ──
import re as _re

_IT_SKILLS_RAW = [
    ("python", [r"\bpython\b"]), ("java", [r"\bjava\b(?!\s*script)"]),
    ("javascript", [r"\bjavascript\b", r"\bjs\b"]), ("typescript", [r"\btypescript\b"]),
    ("c++", [r"\bc\+\+\b", r"\bcpp\b"]), ("c#", [r"\bc#\b", r"\bcsharp\b"]),
    ("golang", [r"\bgolang\b"]), ("rust", [r"\brust\b"]), ("ruby", [r"\bruby\b"]),
    ("php", [r"\bphp\b"]), ("swift", [r"\bswift\b"]), ("kotlin", [r"\bkotlin\b"]),
    ("scala", [r"\bscala\b"]), ("perl", [r"\bperl\b"]),
    ("r programming", [r"\br programming\b", r"\br language\b"]),
    ("shell scripting", [r"\bshell\b", r"\bbash\b", r"\bpowershell\b"]),
    ("sql", [r"\bsql\b(?!\s*server)", r"\bplsql\b", r"\btsql\b"]),
    ("react", [r"\breact\b", r"\breactjs\b"]), ("angular", [r"\bangular\b"]),
    ("vue.js", [r"\bvue\b", r"\bvuejs\b"]), ("next.js", [r"\bnextjs\b", r"\bnext\.js\b"]),
    ("svelte", [r"\bsvelte\b"]), ("html/css", [r"\bhtml\b", r"\bcss\b"]),
    ("tailwind", [r"\btailwind\b"]), ("bootstrap", [r"\bbootstrap\b"]),
    ("node.js", [r"\bnode\s?js\b", r"\bnodejs\b"]), ("django", [r"\bdjango\b"]),
    ("flask", [r"\bflask\b"]), ("spring boot", [r"\bspring\s?boot\b", r"\bspring\b"]),
    (".net", [r"\b\.net\b", r"\bdotnet\b", r"\basp\.net\b"]),
    ("express.js", [r"\bexpress\b"]), ("fastapi", [r"\bfastapi\b"]),
    ("laravel", [r"\blaravel\b"]), ("rails", [r"\brails\b"]),
    ("aws", [r"\baws\b", r"\bamazon web services\b"]), ("azure", [r"\bazure\b"]),
    ("gcp", [r"\bgcp\b", r"\bgoogle cloud\b"]),
    ("docker", [r"\bdocker\b"]), ("kubernetes", [r"\bkubernetes\b", r"\bk8s\b"]),
    ("terraform", [r"\bterraform\b"]), ("ansible", [r"\bansible\b"]),
    ("jenkins", [r"\bjenkins\b"]), ("ci/cd", [r"\bci.?cd\b"]),
    ("git", [r"\bgit\b(?!hub)", r"\bgitlab\b", r"\bgithub\b"]),
    ("linux", [r"\blinux\b", r"\bubuntu\b"]), ("nginx", [r"\bnginx\b"]),
    ("devops", [r"\bdevops\b"]),
    ("mysql", [r"\bmysql\b"]), ("postgresql", [r"\bpostgresql\b", r"\bpostgres\b"]),
    ("mongodb", [r"\bmongodb\b", r"\bmongo\b"]), ("redis", [r"\bredis\b"]),
    ("elasticsearch", [r"\belasticsearch\b"]), ("oracle db", [r"\boracle\b"]),
    ("sql server", [r"\bsql server\b", r"\bmssql\b"]),
    ("dynamodb", [r"\bdynamodb\b"]), ("cassandra", [r"\bcassandra\b"]),
    ("machine learning", [r"\bmachine learning\b", r"\bml\b"]),
    ("deep learning", [r"\bdeep learning\b"]),
    ("data engineering", [r"\bdata engineer\b"]),
    ("artificial intelligence", [r"\bartificial intellig\b", r"\bai\b"]),
    ("nlp", [r"\bnlp\b", r"\bnatural language\b"]),
    ("computer vision", [r"\bcomputer vision\b"]),
    ("tensorflow", [r"\btensorflow\b"]), ("pytorch", [r"\bpytorch\b"]),
    ("pandas", [r"\bpandas\b"]), ("numpy", [r"\bnumpy\b"]),
    ("spark", [r"\bspark\b", r"\bpyspark\b"]), ("hadoop", [r"\bhadoop\b"]),
    ("kafka", [r"\bkafka\b"]), ("tableau", [r"\btableau\b"]),
    ("power bi", [r"\bpower bi\b", r"\bpowerbi\b"]), ("etl", [r"\betl\b"]),
    ("snowflake", [r"\bsnowflake\b"]), ("databricks", [r"\bdatabricks\b"]),
    ("airflow", [r"\bairflow\b"]),
    ("generative ai", [r"\bgenerat.{0,4}\bai\b", r"\bllm\b", r"\bgpt\b", r"\blangchain\b"]),
    ("cybersecurity", [r"\bcyber\s?security\b", r"\binfosec\b"]),
    ("penetration testing", [r"\bpenetration test\b", r"\bpentest\b"]),
    ("siem", [r"\bsiem\b", r"\bsplunk\b"]),
    ("sap", [r"\bsap\b"]), ("salesforce", [r"\bsalesforce\b"]),
    ("servicenow", [r"\bservicenow\b"]),
    ("android", [r"\bandroid\b"]), ("ios", [r"\bios\b"]),
    ("react native", [r"\breact native\b"]), ("flutter", [r"\bflutter\b"]),
    ("rpa", [r"\brpa\b", r"\buipath\b", r"\bblue prism\b"]),
    ("rest api", [r"\brest\s?api\b", r"\brestful\b"]),
    ("graphql", [r"\bgraphql\b"]), ("microservices", [r"\bmicroservice\b"]),
    ("selenium", [r"\bselenium\b"]), ("jira", [r"\bjira\b"]),
    ("agile/scrum", [r"\bagile\b", r"\bscrum\b"]),
    ("embedded systems", [r"\bembedded\b", r"\bfirmware\b"]),
    ("iot", [r"\biot\b"]), ("fpga", [r"\bfpga\b"]), ("vlsi", [r"\bvlsi\b"]),
    ("blockchain", [r"\bblockchain\b", r"\bweb3\b", r"\bsolidity\b"]),
    ("networking", [r"\bnetwork engineer\b", r"\bnetworking\b", r"\bcisco\b"]),
    ("mainframe", [r"\bmainframe\b", r"\bcobol\b"]),
]
_SKILL_PATTERNS = [
    (name, [_re.compile(p, _re.IGNORECASE) for p in pats])
    for name, pats in _IT_SKILLS_RAW
]


def _extract_skills(text: str) -> list[str]:
    """Extract canonical IT skill names from text."""
    found = []
    for skill_name, patterns in _SKILL_PATTERNS:
        for pat in patterns:
            if pat.search(text):
                found.append(skill_name)
                break
    return found


@market_bp.route("/job-roles", methods=["GET"])
def job_roles():
    """Return all distinct job roles with their posting counts."""
    q_filter = (request.args.get("q") or "").strip().lower()
    limit = min(200, max(10, int(request.args.get("limit", 100))))

    query = (
        db.session.query(
            Job.title_norm,
            func.count(Job.id).label("count"),
        )
        .filter(Job.title_norm.isnot(None))
    )
    if q_filter:
        query = query.filter(Job.title_norm.ilike(f"%{q_filter}%"))

    rows = (
        query.group_by(Job.title_norm)
        .order_by(desc("count"))
        .limit(limit)
        .all()
    )
    return jsonify({
        "roles": [{"role": r.title_norm, "count": r.count} for r in rows]
    })


@market_bp.route("/job-role-skills", methods=["GET"])
def job_role_skills():
    """Extract skills for a specific job role from its job descriptions/titles."""
    role = (request.args.get("role") or "").strip().lower()
    if not role:
        return jsonify({"skills": []})

    jobs = (
        db.session.query(Job.title, Job.description)
        .filter(Job.title_norm == role)
        .limit(50)
        .all()
    )
    if not jobs:
        return jsonify({"skills": []})

    from collections import Counter
    skill_counter = Counter()
    for j in jobs:
        text = f"{j.title or ''} {j.description or ''}"
        for sk in _extract_skills(text):
            skill_counter[sk] += 1

    min_count = max(1, len(jobs) // 10)
    skills = [sk for sk, cnt in skill_counter.most_common() if cnt >= min_count]
    return jsonify({"skills": skills, "role": role, "jobsSampled": len(jobs)})


@market_bp.route("/available-skills", methods=["GET"])
def available_skills():
    """Return all distinct tracked skill names for autocomplete."""
    rows = (
        db.session.query(SkillTrend.skill_name)
        .distinct()
        .order_by(SkillTrend.skill_name)
        .all()
    )
    return jsonify({"skills": [r.skill_name for r in rows]})


@market_bp.route("/skill-gap", methods=["POST"])
def skill_gap():
    """Dynamic skill-gap radar: compare user skills against market demand & supply.

    Body: { "skills": ["python", "react", ...], "city": "all-india" }
    - demand  = current quarter (latest 3 months) hiring need, normalized 0-100
    - supply  = previous quarter (3 months before) hiring volume as proxy for
                available workforce — skills hired heavily before → more supply now
    """
    body = request.get_json(silent=True) or {}
    user_skills = [s.strip().lower() for s in (body.get("skills") or []) if s.strip()]
    if not user_skills:
        return jsonify({"radar": []})

    city_filter = (body.get("city") or "").strip().lower()

    # All distinct months sorted newest-first
    all_periods = [
        r[0]
        for r in db.session.query(SkillTrend.period)
        .distinct()
        .order_by(desc(SkillTrend.period))
        .all()
    ]
    recent = all_periods[:3] if len(all_periods) >= 3 else all_periods
    prev = all_periods[3:6] if len(all_periods) >= 6 else []

    def _query_demand(periods):
        if not periods:
            return {}
        q = (
            db.session.query(
                SkillTrend.skill_name,
                func.sum(SkillTrend.demand_count).label("demand"),
            )
            .filter(
                SkillTrend.period.in_(periods),
                func.lower(SkillTrend.skill_name).in_(user_skills),
            )
        )
        if city_filter and city_filter != "all-india":
            q = q.join(City, SkillTrend.city_id == City.id).filter(
                func.lower(City.name) == city_filter
            )
        return {r.skill_name.lower(): r.demand for r in q.group_by(SkillTrend.skill_name).all()}

    demand_map = _query_demand(recent)   # current quarter → employer demand
    supply_map = _query_demand(prev)     # previous quarter → workforce supply proxy

    # Normalize both to 0-100 using a shared max so they're on the same scale
    all_vals = list(demand_map.values()) + list(supply_map.values())
    max_val = max(all_vals, default=1) or 1

    radar = []
    for sk in user_skills:
        d = demand_map.get(sk, 0)
        s = supply_map.get(sk, 0)
        radar.append({
            "skill": sk,
            "demand": min(100, int((d / max_val) * 100)),
            "supply": min(100, int((s / max_val) * 100)),
            "rawDemand": d,
            "rawSupply": s,
        })

    return jsonify({"radar": radar})


@market_bp.route("/records", methods=["GET"])
def market_records():
    """Paginated job market records."""
    page = max(1, int(request.args.get("page", 1)))
    page_size = max(10, min(500, int(request.args.get("page_size", 100))))
    city_filter = (request.args.get("city") or "").strip().lower()
    role_query = (request.args.get("q") or "").strip().lower()

    q = (
        db.session.query(
            Job.title_norm,
            City.name.label("city"),
            Job.posted_date,
            func.count(Job.id).label("demand"),
            AiVulnerabilityScore.score.label("risk_score"),
            AiVulnerabilityScore.confidence.label("risk_confidence"),
            AiVulnerabilityScore.reason.label("risk_reason"),
        )
        .outerjoin(City, Job.city_id == City.id)
        .outerjoin(
            AiVulnerabilityScore,
            Job.title_norm == AiVulnerabilityScore.job_title_norm,
        )
        .filter(Job.title_norm.isnot(None))
    )

    if city_filter and city_filter != "all-india":
        q = q.filter(func.lower(City.name) == city_filter)
    if role_query:
        q = q.filter(Job.title_norm.ilike(f"%{role_query}%"))

    q = q.group_by(Job.title_norm, City.name, Job.posted_date,
                    AiVulnerabilityScore.score, AiVulnerabilityScore.confidence,
                    AiVulnerabilityScore.reason)

    total = q.count()
    rows = q.order_by(desc("demand")).offset((page - 1) * page_size).limit(page_size).all()

    items = [
        {
            "role": r.title_norm or "Unknown",
            "city": r.city or "Unknown",
            "latestMonth": r.posted_date.strftime("%Y-%m") if r.posted_date else "",
            "latestDemand": r.demand,
            "riskScore": float(r.risk_score or 0),
            "riskConfidence": float(r.risk_confidence or 0),
            "riskReason": r.risk_reason or "",
        }
        for r in rows
    ]

    total_pages = max(1, (total + page_size - 1) // page_size)

    # Meta counts
    meta_roles = db.session.query(func.count(func.distinct(Job.title_norm))).scalar() or 0
    meta_cities = db.session.query(func.count(func.distinct(City.id))).join(Job, Job.city_id == City.id).scalar() or 0

    return jsonify({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "meta": {"unique_roles": meta_roles, "unique_cities": meta_cities},
    })


@market_bp.route("/skill-trend", methods=["GET"])
def skill_trend():
    """Monthly demand trend for a specific skill, optionally filtered by city.

    Params: ?skill=python&city=all-india
    Returns 12 months of data with month label + demand count.
    """
    skill = (request.args.get("skill") or "").strip().lower()
    if not skill:
        return jsonify({"trend": [], "skill": ""})

    city_filter = (request.args.get("city") or "").strip().lower()

    q = (
        db.session.query(
            SkillTrend.period,
            func.sum(SkillTrend.demand_count).label("demand"),
        )
        .filter(func.lower(SkillTrend.skill_name) == skill)
    )
    if city_filter and city_filter != "all-india":
        q = q.join(City, SkillTrend.city_id == City.id).filter(
            func.lower(City.name) == city_filter
        )
    rows = q.group_by(SkillTrend.period).order_by(SkillTrend.period).all()

    MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    trend = []
    for period, demand in rows:
        label = f"{MONTH_NAMES[period.month - 1]} {period.year}"
        trend.append({"month": label, "demand": int(demand)})

    return jsonify({"trend": trend, "skill": skill})


@market_bp.route("/cities", methods=["GET"])
def list_cities():
    """Return all cities for dropdown filters."""
    cities = db.session.query(City).order_by(City.name).all()
    return jsonify([c.to_dict() for c in cities])


@market_bp.route("/job-count", methods=["GET"])
def job_count():
    """Live job count for a role in a city — used by chatbot."""
    role = (request.args.get("role") or "").strip().lower()
    city = (request.args.get("city") or "").strip().lower()

    q = db.session.query(func.count(Job.id)).filter(Job.title_norm.ilike(f"%{role}%"))
    if city and city != "all-india":
        q = q.join(City, Job.city_id == City.id).filter(func.lower(City.name) == city)

    count = q.scalar() or 0
    return jsonify({"role": role, "city": city or "All India", "count": count})
