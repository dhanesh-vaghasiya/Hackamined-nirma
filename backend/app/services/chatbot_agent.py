"""
Agentic chatbot service — Groq LLM with tool-calling for real-time DB access.

The chatbot can autonomously decide to query the database for:
  - Job counts by role and city
  - Skill demand trends (growing / declining)
  - AI vulnerability scores for any role
  - Skill intelligence (demand, growth rate, top cities)
  - Related skills for a role
  - Course / reskilling information
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from collections import Counter

import requests
from sqlalchemy import func, desc, extract

from app import db
from app.models import (
    AiVulnerabilityScore,
    City,
    Course,
    InsightDeck,
    Job,
    JobSkill,
    RiskAssessment,
    SkillTrend,
    WorkerProfile,
)

logger = logging.getLogger(__name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
# Use a model with reliable tool-calling support
GROQ_CHAT_MODEL = os.getenv("GROQ_CHAT_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
MAX_TOOL_ITERATIONS = 5

# Known role keywords for fast local intent detection
_ROLE_PATTERNS = [
    "data scientist", "data analyst", "data engineer", "data entry",
    "machine learning", "ml engineer", "deep learning",
    "software engineer", "software developer", "backend developer",
    "frontend developer", "full stack", "fullstack", "web developer",
    "devops", "cloud engineer", "sre", "site reliability",
    "bpo", "business analyst", "financial analyst", "accountant",
    "product manager", "project manager", "scrum master",
    "ui/ux", "ux designer", "ui designer", "graphic designer",
    "cyber security", "security analyst", "network engineer",
    "ai engineer", "nlp engineer", "computer vision",
    "marketing", "digital marketing", "seo", "content writer",
    "hr", "human resource", "recruiter", "talent acquisition",
    "sales", "business development", "customer support",
    "teacher", "professor", "trainer",
    "nurse", "pharmacist", "doctor",
    "mechanical engineer", "civil engineer", "electrical engineer",
    "quality analyst", "qa engineer", "tester", "automation tester",
]


# ═══════════════════════════════════════════════════════════
# Tool implementations — live DB queries
# ═══════════════════════════════════════════════════════════

def _tool_get_job_count(role: str, city: str = "") -> dict:
    """Count job postings matching a role, optionally filtered by city."""
    q = db.session.query(func.count(Job.id)).filter(
        Job.title_norm.ilike(f"%{role}%")
    )
    city_name = "All India"
    if city and city.lower() not in ("", "all-india", "all india", "india"):
        city_row = db.session.query(City).filter(
            func.lower(City.name) == city.strip().lower()
        ).first()
        if city_row:
            q = q.filter(Job.city_id == city_row.id)
            city_name = city_row.name
    count = q.scalar() or 0
    return {"role": role, "city": city_name, "job_count": count}


def _tool_get_skill_trends() -> dict:
    """Return top growing and declining skills from the DB."""
    all_periods = [
        r[0] for r in db.session.query(SkillTrend.period)
        .distinct().order_by(desc(SkillTrend.period)).all()
    ]
    if len(all_periods) < 4:
        return {"top_growing_skills": {}, "declining_skills": {}}

    recent, prev = all_periods[:3], all_periods[3:6]

    def _demand(periods):
        rows = (
            db.session.query(SkillTrend.skill_name, func.sum(SkillTrend.demand_count).label("d"))
            .filter(SkillTrend.period.in_(periods))
            .group_by(SkillTrend.skill_name).all()
        )
        return {r.skill_name: r.d for r in rows}

    cur, pre = _demand(recent), _demand(prev)
    growing, declining = {}, {}
    for skill, demand in cur.items():
        prev_d = pre.get(skill, 0)
        pct = round(((demand - prev_d) / prev_d) * 100, 1) if prev_d > 0 else (100.0 if demand > 0 else 0)
        if demand < 20:
            continue
        if pct > 5:
            growing[skill] = pct
        elif pct < -5:
            declining[skill] = pct

    return {
        "top_growing_skills": dict(sorted(growing.items(), key=lambda x: x[1], reverse=True)[:15]),
        "declining_skills": dict(sorted(declining.items(), key=lambda x: x[1])[:10]),
    }


def _tool_get_ai_vulnerability(role: str, city: str = "") -> dict:
    """Get AI automation vulnerability score for a job role."""
    q = db.session.query(AiVulnerabilityScore).filter(
        AiVulnerabilityScore.job_title_norm.ilike(f"%{role}%")
    )
    if city and city.lower() not in ("", "all-india", "all india"):
        q = q.join(City, AiVulnerabilityScore.city_id == City.id).filter(
            func.lower(City.name) == city.strip().lower()
        )
    vuln = q.order_by(desc(AiVulnerabilityScore.score)).first()
    if vuln:
        return {
            "job_role": vuln.job_title_norm,
            "vulnerability_score": vuln.score,
            "risk_level": (
                "CRITICAL" if vuln.score >= 75 else "HIGH" if vuln.score >= 50
                else "MEDIUM" if vuln.score >= 25 else "LOW"
            ),
            "city": vuln.city.name if vuln.city else "All India",
            "explanation": vuln.reason or "No detailed explanation available.",
        }
    return {"job_role": role, "vulnerability_score": 50, "risk_level": "MEDIUM",
            "city": city or "All India", "explanation": f"No specific data for '{role}'."}


def _tool_get_skill_intel(skill: str) -> dict:
    """Get demand, growth rate, and top cities for a skill."""
    all_periods = [
        r[0] for r in db.session.query(SkillTrend.period)
        .distinct().order_by(desc(SkillTrend.period)).all()
    ]
    recent = all_periods[:3] if len(all_periods) >= 3 else all_periods
    prev = all_periods[3:6] if len(all_periods) >= 6 else []

    cur_demand = (
        db.session.query(func.sum(SkillTrend.demand_count))
        .filter(func.lower(SkillTrend.skill_name) == skill.lower(), SkillTrend.period.in_(recent))
        .scalar()
    ) or 0
    prev_demand = 0
    if prev:
        prev_demand = (
            db.session.query(func.sum(SkillTrend.demand_count))
            .filter(func.lower(SkillTrend.skill_name) == skill.lower(), SkillTrend.period.in_(prev))
            .scalar()
        ) or 0
    growth = round(((cur_demand - prev_demand) / prev_demand) * 100, 1) if prev_demand > 0 else (100.0 if cur_demand > 0 else 0.0)

    job_count = db.session.query(func.count(Job.id)).filter(Job.title_norm.ilike(f"%{skill}%")).scalar() or 0

    top_cities = (
        db.session.query(City.name, func.sum(SkillTrend.demand_count).label("d"))
        .join(City, SkillTrend.city_id == City.id)
        .filter(func.lower(SkillTrend.skill_name) == skill.lower())
        .group_by(City.name).order_by(desc("d")).limit(5).all()
    )
    return {
        "skill_name": skill, "current_demand": int(cur_demand), "growth_rate": growth,
        "job_postings_count": job_count,
        "top_cities": [{"city": c, "demand": int(d)} for c, d in top_cities],
    }


def _tool_get_courses(skill: str = "", limit: int = 5) -> list[dict]:
    """Search available reskilling courses, optionally filtered by skill."""
    q = db.session.query(Course)
    if skill:
        q = q.filter(
            Course.title.ilike(f"%{skill}%")
            | Course.description.ilike(f"%{skill}%")
        )
    courses = q.order_by(Course.created_at.desc()).limit(limit).all()
    if not courses and skill:
        courses = db.session.query(Course).limit(limit).all()
    return [
        {"title": c.title, "provider": c.provider, "institution": c.institution,
         "duration_weeks": c.duration_weeks, "is_free": c.is_free, "url": c.url,
         "skills_covered": c.skills_covered or []}
        for c in courses
    ]


def _tool_get_hiring_comparison(roles: list[str], city: str = "") -> list[dict]:
    """Compare hiring counts across multiple roles."""
    results = []
    for role in roles[:5]:
        data = _tool_get_job_count(role, city)
        results.append(data)
    return sorted(results, key=lambda x: x["job_count"], reverse=True)


def _tool_get_demand_trend(role: str, city: str = "") -> dict:
    """Get year-wise job posting counts for a role (demand trend)."""
    q = db.session.query(
        extract("year", Job.posted_date).label("yr"),
        func.count(Job.id).label("cnt"),
    ).filter(
        Job.title_norm.ilike(f"%{role}%"),
        Job.posted_date.isnot(None),
    )
    city_name = "All India"
    if city and city.lower() not in ("", "all-india", "all india", "india"):
        city_row = db.session.query(City).filter(
            func.lower(City.name) == city.strip().lower()
        ).first()
        if city_row:
            q = q.filter(Job.city_id == city_row.id)
            city_name = city_row.name
    rows = q.group_by("yr").order_by("yr").all()
    total = sum(r.cnt for r in rows)
    trend = {int(r.yr): r.cnt for r in rows}
    return {
        "role": role,
        "city": city_name,
        "total_job_postings": total,
        "demand_trend_by_year": trend,
    }


# Common noise words to skip when extracting skills from descriptions
_SKILL_STOPWORDS = {
    "and", "or", "the", "a", "an", "in", "of", "to", "for", "with", "on",
    "is", "are", "was", "be", "at", "by", "from", "not", "as", "it", "we",
    "you", "will", "can", "all", "has", "have", "do", "this", "that", "any",
    "our", "your", "but", "if", "so", "no", "up", "out", "who", "which",
    "their", "then", "must", "may", "should", "would", "could", "about",
    "into", "also", "been", "being", "more", "its", "they", "were",
    "experience", "years", "work", "working", "good", "strong", "knowledge",
    "understanding", "ability", "skills", "role", "team", "development",
    "required", "preferred", "minimum", "excellent", "etc", "based",
    "related", "relevant", "responsible", "ensure", "including", "across",
    "using", "like", "well", "new", "key", "job", "company", "candidate",
    "looking", "join", "best", "day", "need", "part", "full", "time",
    "salary", "location", "apply", "deadline", "position", "hiring",
    "openings", "opening", "vacancy", "post", "posted",
}

# Curated skills for reliable extraction from job descriptions
_KNOWN_SKILLS = {
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "sql", "nosql",
    "html", "css", "react", "angular", "vue", "node.js", "express", "django",
    "flask", "spring boot", "spring", ".net", "asp.net", "laravel",
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "terraform",
    "jenkins", "ci/cd", "git", "github", "devops", "linux", "unix",
    "machine learning", "deep learning", "nlp", "natural language processing",
    "computer vision", "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
    "data analysis", "data visualization", "data modeling", "data warehousing",
    "tableau", "power bi", "excel", "spark", "hadoop", "kafka", "airflow",
    "mongodb", "postgresql", "mysql", "redis", "elasticsearch", "dynamodb",
    "rest api", "graphql", "microservices", "api design",
    "agile", "scrum", "jira", "project management", "product management",
    "ui/ux", "figma", "sketch", "adobe xd", "photoshop", "illustrator",
    "seo", "digital marketing", "google analytics", "content marketing",
    "salesforce", "crm", "erp", "sap",
    "cyber security", "penetration testing", "ethical hacking", "networking",
    "communication", "leadership", "problem solving", "teamwork",
    "accounting", "tally", "financial analysis", "risk management",
    "autocad", "solidworks", "plc", "scada",
    "six sigma", "lean", "quality management",
}


def _tool_get_top_skills_for_role(role: str, limit: int = 10) -> dict:
    """Extract the most common skills from job descriptions for a role."""
    # First try the job_skills table
    js_rows = (
        db.session.query(JobSkill.skill_name, func.count(JobSkill.id).label("c"))
        .join(Job, JobSkill.job_id == Job.id)
        .filter(Job.title_norm.ilike(f"%{role}%"))
        .group_by(JobSkill.skill_name)
        .order_by(desc("c"))
        .limit(limit)
        .all()
    )
    if js_rows:
        return {
            "role": role,
            "top_skills": [{"skill": s, "mention_count": c} for s, c in js_rows],
            "source": "job_skills_table",
        }

    # Fallback: match known skills from job descriptions
    descs = (
        db.session.query(Job.description)
        .filter(Job.title_norm.ilike(f"%{role}%"), Job.description.isnot(None))
        .limit(2000)
        .all()
    )
    counter: Counter = Counter()
    # Pre-compile word-boundary patterns for skills ≤ 6 chars to avoid false matches
    _boundary_patterns = {}
    for skill in _KNOWN_SKILLS:
        if len(skill) <= 6:
            _boundary_patterns[skill] = re.compile(r"\b" + re.escape(skill) + r"\b", re.IGNORECASE)
    for (desc_text,) in descs:
        if not desc_text:
            continue
        lower_desc = desc_text.lower()
        for skill in _KNOWN_SKILLS:
            if skill in _boundary_patterns:
                if _boundary_patterns[skill].search(desc_text):
                    counter[skill] += 1
            elif skill in lower_desc:
                counter[skill] += 1
    top = counter.most_common(limit)

    # Display names for skills that need special casing
    _DISPLAY = {
        "ui/ux": "UI/UX", "aws": "AWS", "gcp": "GCP", "sql": "SQL",
        "nosql": "NoSQL", "css": "CSS", "html": "HTML", "nlp": "NLP",
        "ci/cd": "CI/CD", "sap": "SAP", "erp": "ERP", "crm": "CRM",
        "seo": "SEO", "r": "R", "go": "Go", "c++": "C++", "c#": "C#",
        ".net": ".NET", "asp.net": "ASP.NET", "git": "Git",
        "rest api": "REST API", "graphql": "GraphQL", "plc": "PLC",
        "scada": "SCADA",
    }
    def _display(s):
        return _DISPLAY.get(s, s.title())
    return {
        "role": role,
        "top_skills": [{"skill": _display(s), "mention_count": c} for s, c in top],
        "source": "known_skills_matching",
    }


def _tool_get_career_analysis(role: str, city: str = "") -> dict:
    """Full structured career analysis: demand trend, top skills, AI risk, courses."""
    demand = _tool_get_demand_trend(role, city)
    skills_data = _tool_get_top_skills_for_role(role, limit=10)
    vuln = _tool_get_ai_vulnerability(role, city)
    courses = _tool_get_courses(role, limit=5)
    return {
        "role": role,
        "city": demand["city"],
        "total_job_postings": demand["total_job_postings"],
        "demand_trend_by_year": demand["demand_trend_by_year"],
        "top_required_skills": [s["skill"] for s in skills_data["top_skills"][:10]],
        "ai_vulnerability": {
            "score": vuln["vulnerability_score"],
            "risk_level": vuln["risk_level"],
            "explanation": vuln["explanation"],
        },
        "courses": courses,
    }


# ═══════════════════════════════════════════════════════════
# Tool definitions for Groq function calling
# ═══════════════════════════════════════════════════════════

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_job_count",
            "description": "Get the number of job postings for a specific role, optionally in a specific city. Use this when the user asks 'how many jobs', 'job count', 'openings for', or anything about hiring numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role": {"type": "string", "description": "Job role to search, e.g. 'BPO', 'data entry', 'software engineer'"},
                    "city": {"type": "string", "description": "City name (optional). E.g. 'Pune', 'Mumbai'. Leave empty for all-India count."},
                },
                "required": ["role"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_skill_trends",
            "description": "Get currently growing and declining skill trends in the Indian job market. Use when user asks about trending skills, which skills are rising/falling, or market direction.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ai_vulnerability",
            "description": "Get the AI automation vulnerability/risk score for a specific job role. Use when user asks about AI risk, automation threat, job safety, or whether a role will be replaced by AI.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role": {"type": "string", "description": "Job role to assess, e.g. 'data entry operator', 'financial analyst'"},
                    "city": {"type": "string", "description": "City (optional). Leave empty for national average."},
                },
                "required": ["role"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_skill_intel",
            "description": "Get detailed intelligence about a specific skill: demand score, growth rate, number of job postings mentioning it, and top cities. Use when user asks about a specific skill's value, demand, or prospects.",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill": {"type": "string", "description": "Skill name, e.g. 'Python', 'SQL', 'AWS', 'data analysis'"},
                },
                "required": ["skill"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_courses",
            "description": "Search for available reskilling courses from NPTEL, SWAYAM, PMKVY, and other providers. Use when user asks about courses, learning resources, or training programs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill": {"type": "string", "description": "Skill or topic to search courses for (optional)"},
                    "limit": {"type": "integer", "description": "Max courses to return (default 5)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_hiring_comparison",
            "description": "Compare hiring counts across multiple job roles side by side. Use when user asks to compare roles, wants to know which role has more jobs, or asks 'which is better'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "roles": {"type": "array", "items": {"type": "string"}, "description": "List of role names to compare, e.g. ['data analyst', 'data scientist', 'business analyst']"},
                    "city": {"type": "string", "description": "City (optional). Leave empty for all-India."},
                },
                "required": ["roles"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_demand_trend",
            "description": "Get the year-wise demand trend for a job role, showing the number of job postings per year. Use whenever the user asks about demand, demand trend, job market outlook, or 'what is the demand for' a role.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role": {"type": "string", "description": "Job role, e.g. 'Data Scientist', 'BPO', 'Backend Developer'"},
                    "city": {"type": "string", "description": "City (optional). Leave empty for all-India."},
                },
                "required": ["role"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_skills_for_role",
            "description": "Get the most frequently mentioned skills from job postings for a role. Use when user asks about skills needed, required skills, or 'what skills are needed for' a role.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role": {"type": "string", "description": "Job role to find skills for"},
                    "limit": {"type": "integer", "description": "Number of top skills to return (default 10)"},
                },
                "required": ["role"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_career_analysis",
            "description": "Get a FULL structured career analysis for a role: demand trend by year, top skills, AI risk score, and courses. Use this when user asks for a complete analysis, roadmap, career overview, or general questions like 'Tell me about Data Scientist career' or 'Show roadmap for X'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role": {"type": "string", "description": "Job role to analyze"},
                    "city": {"type": "string", "description": "City (optional). Leave empty for all-India."},
                },
                "required": ["role"],
            },
        },
    },
]

TOOL_DISPATCH = {
    "get_job_count": lambda args: _tool_get_job_count(args["role"], args.get("city", "")),
    "get_skill_trends": lambda _: _tool_get_skill_trends(),
    "get_ai_vulnerability": lambda args: _tool_get_ai_vulnerability(args["role"], args.get("city", "")),
    "get_skill_intel": lambda args: _tool_get_skill_intel(args["skill"]),
    "get_courses": lambda args: _tool_get_courses(args.get("skill", ""), args.get("limit", 5)),
    "get_hiring_comparison": lambda args: _tool_get_hiring_comparison(args["roles"], args.get("city", "")),
    "get_demand_trend": lambda args: _tool_get_demand_trend(args["role"], args.get("city", "")),
    "get_top_skills_for_role": lambda args: _tool_get_top_skills_for_role(args["role"], args.get("limit", 10)),
    "get_career_analysis": lambda args: _tool_get_career_analysis(args["role"], args.get("city", "")),
}


# ═══════════════════════════════════════════════════════════
# System prompt builder
# ═══════════════════════════════════════════════════════════

def build_system_prompt(worker_ctx: dict | None, language: str) -> str:
    lang_instruction = ""
    if language == "hi":
        lang_instruction = (
            "\n\nLANGUAGE: The user is communicating in Hindi. "
            "You MUST respond entirely in Hindi (Devanagari script). Do NOT mix English unless using technical terms."
        )

    worker_block = ""
    if worker_ctx:
        worker_block = f"""

WORKER PROFILE (use this to personalize every answer):
- Job Title: {worker_ctx.get('job_title', 'Unknown')}
- City: {worker_ctx.get('city', 'Unknown')}
- Experience: {worker_ctx.get('experience_years', 0)} years
- Skills: {', '.join(worker_ctx.get('skills', [])) or 'Not assessed yet'}
- Tasks: {', '.join(worker_ctx.get('tasks', [])) or 'Not assessed yet'}
- Aspirations: {', '.join(worker_ctx.get('aspirations', [])) or 'None stated'}
- Risk Score: {worker_ctx.get('risk_score', 'Not assessed')} / 100
- Risk Level: {worker_ctx.get('risk_level', 'Not assessed')}
- Risk Factors: {', '.join(worker_ctx.get('risk_factors', [])) or 'N/A'}
- Hiring Count in City: {worker_ctx.get('hiring_count_in_city', 'Unknown')}"""

    return f"""You are OASIS Intelligence Assistant — an AI-powered career advisor built for Indian workers facing AI disruption.

IDENTITY & MISSION:
You help blue-collar and white-collar workers in India understand their risk of being displaced by AI/automation, discover safer career paths, and find actionable reskilling courses. You have LIVE access to a real database of 200,000+ Indian job postings, skill trends, AI vulnerability scores, and courses.

RULES:
1. ALWAYS use the provided tools to fetch live data before answering. NEVER guess or fabricate numbers.
2. When citing data, mention it comes from "our live database" or "real-time market data".
3. Be empathetic — many users are anxious about job loss. Be honest but encouraging.
4. For Hindi users, respond naturally in Hindi but keep technical terms in English.

STRICT STRUCTURED OUTPUT FORMAT:
When answering about a role's demand, skills, roadmap, or career analysis, you MUST follow this EXACT format.
Do NOT deviate. Do NOT output vague phrases like "1935 demand". Always show demand as number of job postings per year.

---
**Role:** [Role Name]

**Demand Analysis:**
Total Job Postings: [number]

Demand Trend (Job postings per year):
[year] : [count] job postings
[year] : [count] job postings
...
(If only one year of data exists, say: "In [YEAR] there were [X] job postings for this role.")

**Top Required Skills:**
- [Skill 1]
- [Skill 2]
- [Skill 3]
- [Skill 4]
- [Skill 5]

**AI Automation Risk:**
Score: [X] / 100 ([RISK_LEVEL])
[Brief explanation of risk factors]

**Recommended Learning Roadmap:**
1. [Step 1]
2. [Step 2]
3. [Step 3]
4. [Step 4]
5. [Step 5]

**Courses to Learn:**
- [Course name] — [Provider] — [Free/Paid] — [URL if available]
---

IMPORTANT FORMAT RULES:
- Demand MUST always be shown as "[year] : [number] job postings". NEVER say "1935 demand" or similar.
- Use the year-by-year data returned by the tools directly to fill in the trend section.
- If no year-by-year data is available, show the total count and state the time period.
- The structured format above is MANDATORY for any career, demand, skills, or roadmap query.
- For simple questions (greetings, yes/no, clarifications), respond naturally without this format.
- For comparison queries, use a table or side-by-side format with the same demand rules.
{lang_instruction}
{worker_block}"""


# ═══════════════════════════════════════════════════════════
# Groq API caller with tool-calling loop
# ═══════════════════════════════════════════════════════════

def _call_groq_with_tools(
    messages: list[dict],
    system_prompt: str,
) -> tuple[str, list[dict]]:
    """
    Call Groq LLM with tool definitions. Runs an agentic loop:
    LLM may request tool calls → we execute them → feed results back → repeat.

    Returns (final_reply, tools_used).
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return _fallback_response(messages[-1]["content"] if messages else ""), []

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # Only pass simple role/content dicts (strip any extra keys from history)
    clean_messages = []
    for m in messages:
        clean_messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})

    full_messages = [{"role": "system", "content": system_prompt}] + clean_messages
    tools_used: list[dict] = []

    for _iteration in range(MAX_TOOL_ITERATIONS):
        payload = {
            "model": GROQ_CHAT_MODEL,
            "messages": full_messages,
            "tools": TOOL_DEFINITIONS,
            "tool_choice": "auto",
            "temperature": 0.6,
            "max_tokens": 2500,
        }

        result = _groq_request_with_retry(headers, payload)
        if result is None:
            # All retries failed — fall back to plain chat
            reply = _call_groq_plain(full_messages, headers)
            return _sanitize_reply(reply), tools_used

        choice = result["choices"][0]
        assistant_msg = choice["message"]

        # If the LLM wants to call tools
        if assistant_msg.get("tool_calls"):
            # Append assistant message (must include tool_calls for the protocol)
            full_messages.append({
                "role": "assistant",
                "content": assistant_msg.get("content") or "",
                "tool_calls": assistant_msg["tool_calls"],
            })

            for tc in assistant_msg["tool_calls"]:
                fn_name = tc["function"]["name"]
                try:
                    fn_args = json.loads(tc["function"]["arguments"]) if tc["function"]["arguments"] else {}
                except (json.JSONDecodeError, TypeError):
                    fn_args = {}

                logger.info("Chatbot agent calling tool: %s(%s)", fn_name, fn_args)

                handler = TOOL_DISPATCH.get(fn_name)
                if handler:
                    try:
                        tool_result = handler(fn_args)
                    except Exception as tool_exc:
                        logger.error("Tool %s failed: %s", fn_name, tool_exc)
                        tool_result = {"error": f"Tool execution failed: {tool_exc}"}
                else:
                    tool_result = {"error": f"Unknown tool: {fn_name}"}

                tools_used.append({"tool": fn_name, "args": fn_args, "result_summary": _summarize_result(tool_result)})

                full_messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": json.dumps(tool_result, default=str),
                })
            continue  # Let the LLM process tool results

        # LLM gave a final text answer (no tool calls)
        reply = assistant_msg.get("content", "").strip()
        full_messages.append({"role": "assistant", "content": reply})
        return _sanitize_reply(reply), tools_used

    # If we exhausted iterations, return whatever content exists
    last_content = full_messages[-1].get("content", "") if full_messages else ""
    return _sanitize_reply(last_content) or _fallback_response(""), tools_used


def _groq_request_with_retry(headers: dict, payload: dict, max_retries: int = 3) -> dict | None:
    """Send a request to Groq with retry + backoff for 429 / 400 errors."""
    for attempt in range(max_retries):
        try:
            resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=15)
            if resp.status_code == 429:
                # On daily limit (not per-minute), don't retry — fail fast
                body = resp.json().get("error", {}).get("message", "")
                if "daily" in body.lower() or "limit" in body.lower():
                    logger.warning("Groq daily limit reached, skipping retries")
                    return None
                wait = min(2 ** attempt, 3)
                logger.warning("Groq 429 rate limit, retry in %ss (attempt %d)", wait, attempt + 1)
                time.sleep(wait)
                continue
            if resp.status_code == 400:
                err = resp.json().get("error", {})
                if err.get("code") == "tool_use_failed":
                    logger.warning("Groq tool_use_failed, retrying (attempt %d)", attempt + 1)
                    time.sleep(1)
                    continue
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            logger.error("Groq API error (attempt %d): %s", attempt + 1, exc)
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            continue
    return None


def _sanitize_reply(text: str) -> str:
    """Strip any leaked <function=...> tags from the LLM output."""
    if not text:
        return text
    cleaned = re.sub(r"<function=[^>]*>.*?</function>", "", text, flags=re.DOTALL)
    cleaned = re.sub(r"<function=[^>]*>[^<]*", "", cleaned)
    return cleaned.strip()


# ═══════════════════════════════════════════════════════════
# FAST PATH — single LLM call with pre-fetched data
# ═══════════════════════════════════════════════════════════

def _extract_role_and_city(text: str) -> tuple[str | None, str]:
    """Extract a job role and optional city from the user message using local keyword matching."""
    lower = text.lower()

    # Skip greetings / trivial messages — no role to extract
    if re.match(r"^(hi|hello|hey|namaste|thanks|thank you|ok|bye|help|what can you do)[\s!?.]*$", lower.strip()):
        return None, ""

    found_role = None
    # Match longest role first
    for role in sorted(_ROLE_PATTERNS, key=len, reverse=True):
        if role in lower:
            found_role = role
            break

    # If no pattern matched, try multi-word noun phrases from the message (skip single words)
    if not found_role:
        words = re.findall(r"[a-zA-Z]+", text)
        for i in range(len(words)):
            for length in (3, 2):  # Only try 2+ word phrases
                if i + length > len(words):
                    continue
                phrase = " ".join(words[i:i+length]).lower()
                if len(phrase) < 6:
                    continue
                match = db.session.query(Job.title_norm).filter(
                    Job.title_norm.ilike(f"%{phrase}%")
                ).limit(1).first()
                if match:
                    found_role = phrase
                    break
            if found_role:
                break

    # Extract city
    city = ""
    # Exclude country-level words from city extraction
    _NON_CITY = {"india", "indian", "country", "world", "global"}
    city_patterns = re.findall(r"(?:in|at|from|for)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)", text)
    if city_patterns:
        candidate = city_patterns[-1]
        if candidate.lower() not in _NON_CITY:
            city_row = db.session.query(City).filter(
                func.lower(City.name) == candidate.lower()
            ).first()
            if city_row:
                city = city_row.name

    return found_role, city


def _prefetch_data(role: str, city: str = "") -> dict:
    """Pre-fetch all career data from DB in one shot. ~10ms, no API calls."""
    demand = _tool_get_demand_trend(role, city)
    skills = _tool_get_top_skills_for_role(role, limit=10)
    vuln = _tool_get_ai_vulnerability(role, city)
    courses = _tool_get_courses(role, limit=5)
    return {
        "demand": demand,
        "skills": skills,
        "vulnerability": vuln,
        "courses": courses,
    }


def _format_data_block(data: dict) -> str:
    """Format pre-fetched data into a text block the LLM can use directly."""
    d = data["demand"]
    s = data["skills"]
    v = data["vulnerability"]
    c = data["courses"]

    trend_lines = "\n".join(
        f"  {year}: {count} job postings"
        for year, count in sorted(d["demand_trend_by_year"].items())
    ) or "  No year-wise data available."

    skill_list = ", ".join(
        sk["skill"] for sk in s.get("top_skills", [])[:10]
    ) or "No skill data extracted."

    course_lines = "\n".join(
        f"  - {cr['title']} | {cr['provider']} | {'Free' if cr.get('is_free') else 'Paid'} | {cr.get('url', 'N/A')}"
        for cr in (c if isinstance(c, list) else [])
    ) or "  No courses found in database."

    return f"""LIVE DATABASE RESULTS (use these exact numbers in your response):
Role: {d['role']}
City: {d['city']}
Total Job Postings: {d['total_job_postings']}

Year-wise demand:
{trend_lines}

Top Skills (from job descriptions):
  {skill_list}

AI Vulnerability Score: {v['vulnerability_score']} / 100
Risk Level: {v['risk_level']}
Risk Explanation: {v['explanation']}

Courses found:
{course_lines}"""


def generate_reply(
    user_message: str,
    history: list[dict],
    system_prompt: str,
) -> tuple[str, list[str]]:
    """
    FAST single-call approach:
    1. Detect role/city locally (instant)
    2. Pre-fetch data from DB (~10ms)
    3. Inject real data into prompt
    4. ONE Groq API call
    Returns (reply_text, tools_used_names).
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return _fallback_response(user_message), []

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # Step 1: Fast local intent detection
    role, city = _extract_role_and_city(user_message)
    tools_used = []
    data_block = ""

    # Greetings / simple messages — respond instantly, no LLM needed
    lower_stripped = user_message.strip().lower().rstrip("!?.")
    if not role and re.match(
        r"^(hi|hello|hey|namaste|thanks?|thank you|ok|okay|bye|help|"
        r"what can you do|good morning|good evening|good night)$",
        lower_stripped,
    ):
        return (
            "I'm the OASIS Intelligence Assistant. I have live access to "
            "200,000+ Indian job postings. Ask me about:\n"
            "- Job demand for any role (e.g. 'data scientist jobs in Pune')\n"
            "- AI automation risk for your role\n"
            "- Top skills and reskilling courses\n"
            "- Career transition paths\n\n"
            "How can I help you today?"
        ), []

    # Step 2: Pre-fetch data if a role was detected
    if role:
        data = _prefetch_data(role, city)
        data_block = _format_data_block(data)
        tools_used = ["get_demand_trend", "get_top_skills_for_role",
                       "get_ai_vulnerability", "get_courses"]
        logger.info("Fast path: prefetched data for role=%s city=%s", role, city)

    # Step 3: Build messages with injected data
    clean_history = [
        {"role": m.get("role", "user"), "content": m.get("content", "")}
        for m in history[-8:]  # last 8 messages for context
    ]

    # If we have pre-fetched data, rewrite the prompt so the LLM uses the data
    # instead of trying to call non-existent tools.
    prompt = system_prompt
    if data_block:
        # Replace the "use tools" rule with "use the data below"
        prompt = prompt.replace(
            "1. ALWAYS use the provided tools to fetch live data before answering. NEVER guess or fabricate numbers.",
            "1. The data has ALREADY been fetched for you and is provided below. Use ONLY these numbers in your answer. NEVER fabricate numbers.",
        )
        prompt = prompt + "\n\n" + data_block + (
            "\n\nIMPORTANT: Answer the user's question NOW using the data above. "
            "Do NOT introduce yourself. Do NOT ask follow-up questions. "
            "Go directly into the structured format with the real numbers provided."
        )

    messages = [{"role": "system", "content": prompt}] + clean_history
    messages.append({"role": "user", "content": user_message})

    # Step 4: ONE LLM call — no tools, just plain completion
    payload = {
        "model": GROQ_CHAT_MODEL,
        "messages": messages,
        "temperature": 0.5,
        "max_tokens": 1200,
    }

    result = _groq_request_with_retry(headers, payload, max_retries=2)
    if result:
        reply = result["choices"][0]["message"]["content"].strip()
        return _sanitize_reply(reply), tools_used

    # LLM failed — if we have pre-fetched data, build a template response
    if role and data_block:
        return _template_response(data), tools_used

    return _fallback_response(user_message), tools_used


def _template_response(data: dict) -> str:
    """Build a structured response from pre-fetched data when LLM is unavailable."""
    d = data["demand"]
    s = data["skills"]
    v = data["vulnerability"]
    c = data.get("courses") or []

    trend_lines = "\n".join(
        f"{year} : {count} job postings"
        for year, count in sorted(d["demand_trend_by_year"].items())
    ) or "Data not available."

    skills_lines = "\n".join(
        f"- {sk['skill']}" for sk in s.get("top_skills", [])[:8]
    ) or "- No skill data available"

    course_lines = "\n".join(
        f"- {cr['title']} — {cr['provider']} — {'Free' if cr.get('is_free') else 'Paid'}"
        for cr in (c if isinstance(c, list) else [])
    ) or "- No courses found in database. Try NPTEL or SWAYAM for free courses."

    # Proper casing for common acronyms in role names
    role_name = d['role'].title()
    for acr in ("Bpo", "Sre", "Qa", "Hr", "Ai", "Ml", "Nlp", "Ui", "Ux", "Seo"):
        upper = acr.upper()
        role_name = role_name.replace(acr, upper)

    return f"""**Role:** {role_name}

**Demand Analysis:**
Total Job Postings: {d['total_job_postings']}

Demand Trend (Job postings per year):
{trend_lines}

**Top Required Skills:**
{skills_lines}

**AI Automation Risk:**
Score: {v['vulnerability_score']} / 100 ({v['risk_level']})
{v['explanation']}

**Recommended Learning Roadmap:**
1. Focus on the top skills listed above
2. Gain hands-on project experience
3. Build a portfolio demonstrating these skills
4. Explore certifications in your domain
5. Network with professionals in this field

**Courses to Learn:**
{course_lines}"""


def _call_groq_plain(messages: list[dict], headers: dict) -> str:
    """Fallback: call Groq without tools (plain chat completion)."""
    clean = [m for m in messages if m["role"] in ("system", "user", "assistant")]
    # Strip tool_calls key from assistant messages
    plain_msgs = []
    for m in clean:
        plain_msgs.append({"role": m["role"], "content": m.get("content", "")})
    payload = {
        "model": GROQ_CHAT_MODEL,
        "messages": plain_msgs,
        "temperature": 0.6,
        "max_tokens": 2500,
    }
    result = _groq_request_with_retry(headers, payload, max_retries=2)
    if result:
        return result["choices"][0]["message"]["content"].strip()
    return _fallback_response("")


def _summarize_result(result) -> str:
    """Short summary of a tool result for logging/storage."""
    s = json.dumps(result, default=str)
    return s[:200] + "..." if len(s) > 200 else s


# ═══════════════════════════════════════════════════════════
# Worker context loader
# ═══════════════════════════════════════════════════════════

def load_worker_context(profile_id: int | None) -> dict | None:
    """Load worker profile + risk assessment from DB."""
    if not profile_id:
        return None

    wp = db.session.query(WorkerProfile).get(profile_id)
    if not wp:
        return None

    city_name = wp.city.name if wp.city else "Unknown"

    ra = (
        db.session.query(RiskAssessment)
        .filter(RiskAssessment.worker_profile_id == wp.id)
        .order_by(desc(RiskAssessment.created_at))
        .first()
    )

    hiring_count = 0
    if wp.city_id and wp.job_title_norm:
        hiring_count = (
            db.session.query(func.count(Job.id))
            .filter(Job.city_id == wp.city_id, Job.title_norm.ilike(f"%{wp.job_title_norm}%"))
            .scalar() or 0
        )

    trending = []
    if wp.city_id:
        trending = (
            db.session.query(SkillTrend.skill_name, func.sum(SkillTrend.demand_count).label("d"))
            .filter(SkillTrend.city_id == wp.city_id)
            .group_by(SkillTrend.skill_name).order_by(desc("d")).limit(10).all()
        )

    return {
        "job_title": wp.job_title,
        "job_title_norm": wp.job_title_norm,
        "city": city_name,
        "experience_years": wp.experience_years,
        "skills": wp.extracted_skills or [],
        "tasks": wp.extracted_tasks or [],
        "aspirations": wp.aspirations or [],
        "risk_score": ra.score if ra else None,
        "risk_level": ra.risk_level if ra else None,
        "risk_factors": ra.factors if ra else [],
        "hiring_count_in_city": hiring_count,
        "trending_skills": [{"skill": s, "demand": d} for s, d in trending],
    }


# ═══════════════════════════════════════════════════════════
# Fallback (no API key / API down)
# ═══════════════════════════════════════════════════════════

def _fallback_response(query: str) -> str:
    q = query.lower()
    if re.search(r"risk|score|high|why|vulnerable", q):
        return ("Your risk score is computed from three signals: "
                "(1) AI vulnerability index for your role — how much of your work can be automated, "
                "(2) Hiring trends in your city — whether demand is growing or declining, "
                "(3) Your experience level. "
                "Check the risk assessment panel in the Worker Portal for specifics.")
    if re.search(r"path|reskill|course|learn|train", q):
        return ("I recommend exploring free courses on NPTEL and SWAYAM. "
                "Popular choices include Data Analysis (IIT Madras), AI Fundamentals, "
                "and Digital Marketing through PMKVY. "
                "Use the Worker Portal to get a personalized reskilling roadmap.")
    if re.search(r"job|bpo|hiring|how many|openings", q):
        return ("I can look up live job counts from our database of 200,000+ postings. "
                "Please specify both the role and city, e.g., "
                "'How many BPO jobs are in Pune right now?'")
    if re.search(r"[\u0900-\u097F]", q):
        return ("आपकी प्रोफ़ाइल के आधार पर, मैं NPTEL और SWAYAM के मुफ़्त कोर्स से शुरू करने की सलाह दूँगा। "
                "कृपया अपना प्रोफ़ाइल भरें ताकि मैं व्यक्तिगत मार्गदर्शन दे सकूँ।")
    return ("I'm the OASIS Intelligence Assistant. I have live access to 200,000+ Indian job postings. "
            "Ask me about: job counts, skill trends, AI risk for any role, reskilling courses, "
            "or career transition paths. How can I help?")


def detect_language(text: str) -> str:
    """Detect Hindi vs English."""
    if re.search(r"[\u0900-\u097F]", text):
        return "hi"
    return "en"


# ═══════════════════════════════════════════════════════════
# Quick Insight Deck extraction
# ═══════════════════════════════════════════════════════════

_INSIGHT_EXTRACT_PROMPT = """You are a JSON extraction engine. Given a user question and the AI assistant reply, extract structured insight fields.

Return ONLY valid JSON with these exact keys (no markdown, no explanation):
{
  "topic": "main subject of the question in 2-5 words",
  "goal": "what the user wants to achieve in 2-5 words",
  "focus_area": "main recommendation or focus area from the reply in 5-10 words",
  "key_skills": "comma-separated list of up to 5 key skills/technologies mentioned",
  "benefit": "short benefit or impact statement in under 15 words",
  "market_demand": "technology or role demand summary in under 15 words",
  "market_regions": "top cities or regions mentioned, comma-separated (or 'India-wide' if none)",
  "market_description": "one-sentence market insight"
}

If a field cannot be determined, use a sensible default based on the question context. Never leave a field empty."""


def extract_insight_deck(
    user_message: str,
    ai_reply: str,
    user_id: int,
) -> InsightDeck | None:
    """
    Extract structured insight deck from a Q&A pair using a fast LLM call.
    Returns an InsightDeck model instance (unsaved) or None on failure.
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return _extract_insight_local(user_message, ai_reply, user_id)

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": GROQ_CHAT_MODEL,
        "messages": [
            {"role": "system", "content": _INSIGHT_EXTRACT_PROMPT},
            {"role": "user", "content": f"USER QUESTION:\n{user_message}\n\nAI REPLY:\n{ai_reply[:2000]}"},
        ],
        "temperature": 0.1,
        "max_tokens": 400,
    }

    try:
        resp = requests.post(
            GROQ_API_URL, headers=headers, json=payload, timeout=10
        )
        if resp.status_code != 200:
            logger.warning("Insight extraction LLM call failed: %s", resp.status_code)
            return _extract_insight_local(user_message, ai_reply, user_id)

        raw = resp.json()["choices"][0]["message"]["content"].strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
        fields = json.loads(raw)
    except (json.JSONDecodeError, KeyError, Exception) as exc:
        logger.warning("Insight extraction parse error: %s", exc)
        return _extract_insight_local(user_message, ai_reply, user_id)

    return InsightDeck(
        user_id=user_id,
        question=user_message[:500],
        topic=fields.get("topic", "General Query")[:200],
        goal=fields.get("goal", "Information")[:200],
        focus_area=fields.get("focus_area", "Career guidance")[:300],
        key_skills=fields.get("key_skills", "N/A")[:500],
        benefit=fields.get("benefit", "Better career insights")[:300],
        market_demand=fields.get("market_demand", "Varies by region")[:300],
        market_regions=fields.get("market_regions", "India-wide")[:300],
        market_description=fields.get("market_description", "Check live data for details.")[:500],
    )


def _extract_insight_local(user_message: str, ai_reply: str, user_id: int) -> InsightDeck:
    """Fallback: extract insight deck using local heuristics (no LLM)."""
    lower_q = user_message.lower()
    lower_r = ai_reply.lower()

    # Topic: detect from role patterns or first noun phrase
    topic = "General Career Query"
    for role in sorted(_ROLE_PATTERNS, key=len, reverse=True):
        if role in lower_q:
            topic = role.title() + " Career"
            break

    # Goal
    goal = "Information"
    if re.search(r"improv|learn|upskill|reskill|course", lower_q):
        goal = "Skill Improvement"
    elif re.search(r"salary|pay|earn|income", lower_q):
        goal = "Salary Increase"
    elif re.search(r"job|hiring|opening|demand", lower_q):
        goal = "Job Search"
    elif re.search(r"risk|safe|automat|ai|replac", lower_q):
        goal = "Risk Assessment"
    elif re.search(r"compar|better|which", lower_q):
        goal = "Career Comparison"

    # Key skills from reply
    found_skills = []
    for skill in sorted(_KNOWN_SKILLS, key=len, reverse=True):
        if skill in lower_r and skill not in [s.lower() for s in found_skills]:
            found_skills.append(skill.title() if len(skill) > 3 else skill.upper())
            if len(found_skills) >= 5:
                break
    key_skills = ", ".join(found_skills) if found_skills else "N/A"

    # Focus area from first recommendation-like sentence
    focus_area = "Career guidance and skill development"
    rec_match = re.search(r"(?:recommend|focus|should|suggest)[^.]{5,60}", lower_r)
    if rec_match:
        focus_area = rec_match.group(0).strip().capitalize()[:300]

    # Market regions
    _CITIES = ["bangalore", "mumbai", "delhi", "pune", "hyderabad", "chennai",
               "kolkata", "noida", "gurgaon", "ahmedabad", "indore", "jaipur"]
    found_cities = [c.title() for c in _CITIES if c in lower_r]
    market_regions = ", ".join(found_cities[:4]) if found_cities else "India-wide"

    # Market demand
    market_demand = topic.replace(" Career", "") + " demand across India"

    # Market description
    market_description = f"Job market data indicates active demand for {topic.lower().replace(' career', '')} roles."
    if found_cities:
        market_description += f" High demand in {', '.join(found_cities[:3])}."

    return InsightDeck(
        user_id=user_id,
        question=user_message[:500],
        topic=topic[:200],
        goal=goal[:200],
        focus_area=focus_area[:300],
        key_skills=key_skills[:500],
        benefit="Better career positioning and skill growth"[:300],
        market_demand=market_demand[:300],
        market_regions=market_regions[:300],
        market_description=market_description[:500],
    )
