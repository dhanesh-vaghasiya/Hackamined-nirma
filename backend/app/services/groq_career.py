"""Groq-powered career intelligence service.

Calls Groq LLM to generate:
  1. AI-recommended next roles (ranked with reasoning)
  2. Week-by-week reskilling roadmap for a chosen target role
"""
from __future__ import annotations

import json
import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
from urllib.parse import quote_plus

import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

log = logging.getLogger(__name__)


def _get_groq_key() -> str | None:
    return os.getenv("GROQ_API_KEY", "").strip() or None


def _call_groq(system_prompt: str, user_prompt: str, *, temperature: float = 0.7, max_tokens: int = 2048) -> str | None:
    api_key = _get_groq_key()
    if not api_key:
        log.warning("GROQ_API_KEY not set – skipping LLM call")
        return None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        log.exception("Groq API call failed")
        return None


def _parse_json_from_llm(raw: str) -> Any:
    """Extract the first JSON block from LLM output."""
    # Try direct parse
    raw = raw.strip()
    if raw.startswith("```"):
        # Remove markdown code fences
        lines = raw.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw = "\n".join(lines).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Try to find JSON array or object
    for start_char, end_char in [("[", "]"), ("{", "}")]:
        s = raw.find(start_char)
        e = raw.rfind(end_char)
        if s != -1 and e != -1 and e > s:
            try:
                return json.loads(raw[s : e + 1])
            except json.JSONDecodeError:
                continue
    return None


# ── 0. AI Automation Vulnerability Assessment ───────────────────────

AI_VULN_SYSTEM_PROMPT = """\
You are an expert AI-workforce analyst. Given a worker's profile, assess TWO risk dimensions:

1. **automation_risk** (0-100): How likely is it that AI and automation will REPLACE or significantly reduce the need for the tasks this person does? Consider current AI capabilities (LLMs, computer vision, robotics, RPA) and near-future trends (2-5 years).

2. **ai_takeover_risk** (0-100): How likely is it that AI tools will make this specific job role obsolete or drastically reduced in headcount within 5 years? Consider industry trends, enterprise AI adoption rates, and existing AI products targeting this role.

SCORING GUIDE (for both):
- 0-20: Very safe — requires physical presence, creativity, complex human judgment, or empathy
- 21-40: Low risk — AI assists but cannot replace; human oversight critical
- 41-60: Moderate risk — AI can handle 40-60% of tasks; role will transform significantly
- 61-80: High risk — AI can automate most tasks; job demand likely to shrink
- 81-100: Critical — AI already replacing this role; immediate reskilling needed

Return ONLY a valid JSON object (no markdown, no extra text):
{
  "automation_risk": <int 0-100>,
  "automation_reason": "<1-2 sentence explanation>",
  "ai_takeover_risk": <int 0-100>,
  "ai_takeover_reason": "<1-2 sentence explanation>",
  "combined_ai_vulnerability": <int 0-100, weighted average>
}
"""


def assess_ai_vulnerability(profile: dict) -> dict | None:
    """Ask Groq to score AI automation and takeover risk for a worker profile."""

    user_prompt = f"""Assess the AI automation and takeover risk for this worker:

- Job Title: {profile.get('job_title', 'Unknown')}
- City: {profile.get('city', 'Unknown')}
- Experience: {profile.get('experience_years', 0)} years
- Skills: {', '.join(profile.get('skills', []))}
- Daily Tasks: {', '.join(profile.get('tasks', []))}
- Domain: {profile.get('domain', 'General')}

Score both automation_risk and ai_takeover_risk from 0-100. Return ONLY valid JSON."""

    raw = _call_groq(AI_VULN_SYSTEM_PROMPT, user_prompt, temperature=0.4, max_tokens=500)
    if not raw:
        return None

    parsed = _parse_json_from_llm(raw)
    if not isinstance(parsed, dict):
        log.error("Groq returned non-dict for AI vulnerability: %s", raw[:200])
        return None

    return {
        "automation_risk": min(100, max(0, int(parsed.get("automation_risk", 50)))),
        "automation_reason": str(parsed.get("automation_reason", "")),
        "ai_takeover_risk": min(100, max(0, int(parsed.get("ai_takeover_risk", 50)))),
        "ai_takeover_reason": str(parsed.get("ai_takeover_reason", "")),
        "combined_ai_vulnerability": min(100, max(0, int(parsed.get("combined_ai_vulnerability", 50)))),
    }


# ── 1. Suggest Next Roles ───────────────────────────────────────────

ROLE_SYSTEM_PROMPT = """\
You are an expert Indian workforce career advisor AI built into the OASIS platform.
You analyze a worker's profile, their AI-automation risk, market demand signals, and
suggest the BEST 3-4 career transition roles ranked from best to least.

RULES:
- Suggest ONLY realistic, achievable roles that this specific person can transition to.
- Consider their existing skills, experience, city job market, and risk level.
- Rank by: (1) low AI-automation risk, (2) strong hiring demand in India, (3) skill overlap with current profile.
- For each role give a clear, specific reason (2-3 sentences) explaining WHY this role is good for them.
- Include a match_score (0.0-1.0) reflecting how suitable this transition is.
- Include 3-5 key skills the person would need to learn for each role.

Return ONLY a valid JSON array (no markdown, no extra text) with this exact structure:
[
  {
    "rank": 1,
    "role": "Target Role Title",
    "match_score": 0.85,
    "reason": "Why this role is ideal for this person...",
    "skills_to_learn": ["skill1", "skill2", "skill3"],
    "ai_risk_level": "LOW",
    "demand_outlook": "Strong growth expected"
  }
]
"""


def suggest_next_roles(
    profile: dict,
    risk_data: dict,
    market_context: dict | None = None,
) -> list[dict] | None:
    """Ask Groq to suggest 3-4 AI-recommended next roles for a worker."""

    user_prompt = f"""Analyze this worker profile and suggest 3-4 best career transition roles:

WORKER PROFILE:
- Current Role: {profile.get('job_title', 'Unknown')}
- City: {profile.get('city', 'Unknown')}
- Experience: {profile.get('experience_years', 0)} years
- Current Skills: {', '.join(profile.get('skills', []))}
- Tasks: {', '.join(profile.get('tasks', []))}
- Aspirations: {', '.join(profile.get('aspirations', []))}
- Domain: {profile.get('domain', 'General')}

RISK ASSESSMENT:
- Risk Score: {risk_data.get('score', 50)}/100
- Risk Level: {risk_data.get('risk_level', 'MEDIUM')}
- Factors: {'; '.join(risk_data.get('factors', []))}
- Hiring Trend: {risk_data.get('hiring_trend_pct', 0)}% of city jobs match this role
- Jobs Found: {risk_data.get('hiring_count', 0)} matching positions

{f"MARKET CONTEXT: {json.dumps(market_context)}" if market_context else ""}

Suggest 3-4 roles ranked from best to least suitable. Return ONLY valid JSON array."""

    raw = _call_groq(ROLE_SYSTEM_PROMPT, user_prompt, temperature=0.6, max_tokens=1500)
    if not raw:
        return None

    parsed = _parse_json_from_llm(raw)
    if not isinstance(parsed, list):
        log.error("Groq returned non-list for role suggestions: %s", raw[:200])
        return None

    # Normalize and validate
    roles = []
    for item in parsed[:4]:
        if not isinstance(item, dict) or "role" not in item:
            continue
        roles.append({
            "rank": item.get("rank", len(roles) + 1),
            "role": str(item["role"]),
            "match_score": min(1.0, max(0.0, float(item.get("match_score", 0.5)))),
            "reason": str(item.get("reason", "")),
            "skills_to_learn": list(item.get("skills_to_learn", []))[:5],
            "ai_risk_level": str(item.get("ai_risk_level", "MEDIUM")),
            "demand_outlook": str(item.get("demand_outlook", "")),
        })

    return roles if roles else None


# ── 2. Build Reskilling Roadmap ─────────────────────────────────────

ROADMAP_SYSTEM_PROMPT = """\
You are an expert Indian workforce reskilling advisor AI built into the OASIS platform.
A worker has chosen a target career role. Build them a DETAILED week-by-week reskilling
roadmap using REAL courses from real platforms.

RULES:
- Create a practical 8-16 week roadmap broken into weekly phases.
- Use REAL courses from: Coursera, Udemy, NPTEL, SWAYAM, edX, LinkedIn Learning, freeCodeCamp, Khan Academy, Google Skillshop, HubSpot Academy, Simplilearn.
- Each step must have a REAL clickable course URL. Use actual course URLs you know exist.
- Include estimated hours per week (5-15 hours).
- Group into logical phases (Foundation → Core Skills → Advanced → Portfolio/Certification).
- Consider the person's existing skills — skip basics they already know.
- Include at least one free option per phase.

Return ONLY a valid JSON object (no markdown, no extra text) with this exact structure:
{
  "target_role": "Role Name",
  "total_weeks": 12,
  "phases": [
    {
      "phase": 1,
      "title": "Foundation Phase",
      "weeks": "1-3",
      "week_start": 1,
      "week_end": 3,
      "hours_per_week": 10,
      "steps": [
        {
          "title": "Course or Activity Name",
          "provider": "Coursera",
          "url": "https://www.coursera.org/learn/...",
          "duration_weeks": 2,
          "is_free": true,
          "skills_covered": ["skill1", "skill2"],
          "description": "Brief description of what you'll learn"
        }
      ]
    }
  ],
  "expected_outcome": "After completing this roadmap, you will be able to...",
  "certification_tip": "Optional certification recommendation"
}
"""


def build_role_roadmap(
    profile: dict,
    risk_data: dict,
    chosen_role: str,
) -> dict | None:
    """Ask Groq to build a week-by-week reskilling roadmap for a chosen target role."""

    user_prompt = f"""Build a detailed reskilling roadmap for this worker to transition into "{chosen_role}":

CURRENT PROFILE:
- Current Role: {profile.get('job_title', 'Unknown')}
- City: {profile.get('city', 'Unknown')}
- Experience: {profile.get('experience_years', 0)} years
- Current Skills: {', '.join(profile.get('skills', []))}
- Domain: {profile.get('domain', 'General')}

RISK CONTEXT:
- Current Risk Score: {risk_data.get('score', 50)}/100
- Risk Level: {risk_data.get('risk_level', 'MEDIUM')}

TARGET ROLE: {chosen_role}

Build a practical, week-by-week roadmap with REAL courses from real platforms (Coursera, Udemy, NPTEL, etc.) that will help this person successfully transition from {profile.get('job_title', 'their current role')} to {chosen_role}. Consider their existing skills and skip basics they already know. Return ONLY valid JSON object."""

    raw = _call_groq(ROADMAP_SYSTEM_PROMPT, user_prompt, temperature=0.5, max_tokens=3000)
    if not raw:
        return None

    parsed = _parse_json_from_llm(raw)
    if not isinstance(parsed, dict):
        log.error("Groq returned non-dict for roadmap: %s", raw[:200])
        return None

    # Validate minimum structure
    if "phases" not in parsed or not isinstance(parsed["phases"], list):
        log.error("Groq roadmap missing phases")
        return None

    validated_phases = _validate_and_fix_urls(parsed["phases"])

    return {
        "target_role": parsed.get("target_role", chosen_role),
        "total_weeks": parsed.get("total_weeks", 12),
        "phases": validated_phases,
        "expected_outcome": parsed.get("expected_outcome", ""),
        "certification_tip": parsed.get("certification_tip", ""),
    }


# ── URL validation + YouTube fallback ────────────────────────────────────

def _check_url(url: str) -> bool:
    """Return True if the URL responds with a 2xx/3xx status."""
    if not url or not url.startswith("http"):
        return False
    try:
        r = requests.head(url, timeout=6, allow_redirects=True,
                          headers={"User-Agent": "Mozilla/5.0"})
        return r.status_code < 400
    except Exception:
        return False


def _youtube_search_url(title: str, provider: str = "") -> str:
    """Search YouTube and return a direct video link for the first result.
    Falls back to a search page URL if extraction fails."""
    q = f"{title} {provider} full course tutorial".strip()
    search_url = f"https://www.youtube.com/results?search_query={quote_plus(q)}"
    try:
        resp = requests.get(
            search_url, timeout=8,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                     "Accept-Language": "en-US,en;q=0.9"},
        )
        # YouTube embeds JSON with videoId in the HTML
        ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp.text)
        if ids:
            return f"https://www.youtube.com/watch?v={ids[0]}"
    except Exception:
        log.debug("YouTube search fallback failed for: %s", q)
    return search_url


def _validate_and_fix_urls(phases: list[dict]) -> list[dict]:
    """Check every step URL in parallel; replace dead ones with YouTube search."""
    # Collect all (phase_idx, step_idx, url) tuples
    tasks: list[tuple[int, int, str]] = []
    for pi, phase in enumerate(phases):
        for si, step in enumerate(phase.get("steps", [])):
            url = step.get("url", "")
            if url and url.startswith("http"):
                tasks.append((pi, si, url))

    if not tasks:
        return phases

    results: dict[tuple[int, int], bool] = {}
    with ThreadPoolExecutor(max_workers=10) as pool:
        future_map = {
            pool.submit(_check_url, url): (pi, si)
            for pi, si, url in tasks
        }
        for future in as_completed(future_map):
            key = future_map[future]
            try:
                results[key] = future.result()
            except Exception:
                results[key] = False

    # Replace dead URLs with YouTube fallback
    for (pi, si), alive in results.items():
        step = phases[pi]["steps"][si]
        if not alive:
            step["url"] = _youtube_search_url(
                step.get("title", ""), step.get("provider", "")
            )
            step["source"] = "youtube"
            step["provider"] = "YouTube"
        else:
            step["source"] = "original"

    return phases


# ── Detailed (topic-tree) roadmap via Groq ──────────────────────────────

DETAILED_ROADMAP_SYSTEM_PROMPT = """\
You are an expert career roadmap architect.  Given a target role, produce a STRUCTURED
learning roadmap that lists every major topic and subtopic a learner must cover, ordered
from beginner to advanced.

RULES:
- Organise into 8-15 top-level sections (topics).
- Each section contains 3-10 subtopics (specific things to learn).
- Order sections from foundational → advanced.
- Cover: prerequisites, core skills, tools/frameworks, advanced topics, portfolio/project ideas.
- Be specific — use real technology and concept names, not generic placeholders.

Return ONLY a valid JSON object (no markdown, no extra text):
{
  "slug": "role-name-slug",
  "source": "groq",
  "total_topics": <int>,
  "total_subtopics": <int>,
  "sections": [
    {
      "title": "Section Title",
      "type": "topic",
      "subtopics": ["Subtopic 1", "Subtopic 2", ...]
    }
  ]
}
"""


def build_detailed_roadmap_groq(role: str) -> dict | None:
    """Generate a detailed topic-tree roadmap via Groq when roadmap.sh has no match."""

    user_prompt = f"""Build a comprehensive, detailed learning roadmap for someone who wants to become a **{role}**.
Cover every important topic and subtopic they need to learn, ordered from foundational to advanced.
Return ONLY valid JSON."""

    raw = _call_groq(DETAILED_ROADMAP_SYSTEM_PROMPT, user_prompt, temperature=0.4, max_tokens=3000)
    if not raw:
        return None

    parsed = _parse_json_from_llm(raw)
    if not isinstance(parsed, dict) or "sections" not in parsed:
        log.error("Groq detailed roadmap invalid: %s", raw[:200])
        return None

    return {
        "slug": parsed.get("slug", role.lower().replace(" ", "-")),
        "source": "groq",
        "matched_from_role": role,
        "total_topics": parsed.get("total_topics", len(parsed["sections"])),
        "total_subtopics": parsed.get("total_subtopics", sum(len(s.get("subtopics", [])) for s in parsed["sections"])),
        "sections": parsed["sections"],
    }


# ── Sub-concept learning graph ─────────────────────────────────────

SUBCONCEPT_GRAPH_SYSTEM_PROMPT = """\
You are an expert educator.
Given a target role and a topic from a learning roadmap, produce a concept-map
with exactly 5 or 6 key things a learner must study to fully understand that topic.

RULES:
- Return exactly 5 or 6 nodes — each is a specific, concrete concept to learn.
- Return edges connecting related concepts (NOT a strict chain — concepts can connect
  to multiple others, forming a web/graph like a mind-map).
- Keep node labels short (2-4 words max).
- Each node must have a one-line description.
- Pick one node as the "root" (the most foundational concept).

Return ONLY a valid JSON object (no markdown, no extra text):
{
  "topic": "The Topic Name",
  "nodes": [
    { "id": "node_1", "label": "Concept Name", "description": "One-line explanation" }
  ],
  "edges": [
    { "from": "node_1", "to": "node_2" }
  ],
  "root": "node_1"
}
"""


def get_topic_subconcepts(role: str, topic: str) -> dict | None:
    """Ask Groq for a concept-map graph of key things to learn for a topic."""

    user_prompt = (
        f"A person wants to become a **{role}**. One topic they need to learn is **{topic}**.\n"
        f"What are the 5-6 most important concepts they must learn to fully understand {topic}?\n"
        f"Show them as a connected graph — how these concepts relate to each other.\n"
        f"Return ONLY valid JSON."
    )

    raw = _call_groq(SUBCONCEPT_GRAPH_SYSTEM_PROMPT, user_prompt, temperature=0.4, max_tokens=2000)
    if not raw:
        return None

    parsed = _parse_json_from_llm(raw)
    if not isinstance(parsed, dict) or "nodes" not in parsed or "edges" not in parsed:
        log.error("Groq sub-concept graph invalid: %s", raw[:200])
        return None

    return {
        "topic": parsed.get("topic", topic),
        "nodes": parsed["nodes"],
        "edges": parsed["edges"],
        "root": parsed.get("root", parsed["nodes"][0]["id"] if parsed["nodes"] else None),
    }

# ── 4. Flashcards generation ────────────────────────────────────────

FLASHCARDS_SYSTEM_PROMPT = """\
You are an expert technical educator and interview coach.
Given a specific job role, a main learning topic, and its sub-concepts, your goal is to generate exactly 8 high-quality study flashcards to test the user's knowledge.

RULES:
- Generate EXACTLY 8 flashcards.
- The questions should test practical understanding, edge cases, and core principles relevant to the target role.
- Keep the questions concise (1-2 sentences).
- Keep the answers clear and punchy (max 2-3 sentences), explaining the "Why" or "How".
- Return ONLY a valid JSON array of objects. Do not wrap in a markdown block. Do not include extra text.

Return exactly this structure:
[
  {
    "question": "What is the primary difference between X and Y in this context?",
    "answer": "X is used for ..., whereas Y is optimized for ... because of ..."
  }
]
"""

def generate_topic_flashcards(role: str, topic: str, subtopics: list[str]) -> list[dict] | None:
    """Ask Groq to generate 8 study flashcards for a specific topic."""
    
    subtopics_str = ", ".join(subtopics) if subtopics else "None provided"
    
    user_prompt = (
        f"A learner is studying to become a **{role}**.\n"
        f"They are currently reviewing the topic: **{topic}**.\n"
        f"The core sub-concepts they learned are: {subtopics_str}.\n\n"
        f"Generate exactly 8 assessment flashcards based on this material. Return ONLY the JSON array."
    )

    raw = _call_groq(FLASHCARDS_SYSTEM_PROMPT, user_prompt, temperature=0.6, max_tokens=1500)
    if not raw:
        return None

    parsed = _parse_json_from_llm(raw)
    if not isinstance(parsed, list):
        log.error("Groq flashcards valid list not returned: %s", raw[:200])
        return None
        
    cards = []
    for item in parsed[:8]:
        if isinstance(item, dict) and "question" in item and "answer" in item:
            cards.append({
                "question": str(item["question"]).strip(),
                "answer": str(item["answer"]).strip()
            })
            
    # Pad if LLM returned fewer than 8
    while len(cards) < 8:
        cards.append({
            "question": f"Key concept related to {topic}?",
            "answer": "Review the core principles of this topic to solidify your understanding."
        })

    return cards[:8]
