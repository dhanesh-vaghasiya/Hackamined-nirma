"""
Dummy database tools for the AI agent.
These return in-memory data that mirrors the real DB schema.
Replace these functions with real DB queries later.
"""


# ── Skill Intel Data ─────────────────────────────────────
_SKILL_INTEL = {
    "Python": {
        "skill_name": "Python", "demand_score": 92.0, "growth_rate": 18.5,
        "salary_impact": 30.0, "ai_relevance_score": 95.0,
        "top_industries": ["IT", "Finance", "Healthcare"],
        "job_postings_count": 45000,
    },
    "Prompt Engineering": {
        "skill_name": "Prompt Engineering", "demand_score": 88.0, "growth_rate": 142.0,
        "salary_impact": 25.0, "ai_relevance_score": 99.0,
        "top_industries": ["AI/ML", "Marketing", "Education"],
        "job_postings_count": 12000,
    },
    "Excel": {
        "skill_name": "Excel", "demand_score": 75.0, "growth_rate": -5.0,
        "salary_impact": 8.0, "ai_relevance_score": 30.0,
        "top_industries": ["Finance", "Admin", "Retail"],
        "job_postings_count": 62000,
    },
    "Data Analytics": {
        "skill_name": "Data Analytics", "demand_score": 90.0, "growth_rate": 35.0,
        "salary_impact": 28.0, "ai_relevance_score": 85.0,
        "top_industries": ["IT", "E-commerce", "BFSI"],
        "job_postings_count": 38000,
    },
    "Cybersecurity": {
        "skill_name": "Cybersecurity", "demand_score": 85.0, "growth_rate": 28.0,
        "salary_impact": 35.0, "ai_relevance_score": 60.0,
        "top_industries": ["IT", "Banking", "Government"],
        "job_postings_count": 22000,
    },
    "Tally": {
        "skill_name": "Tally", "demand_score": 55.0, "growth_rate": -12.0,
        "salary_impact": 5.0, "ai_relevance_score": 15.0,
        "top_industries": ["Finance", "SME", "Retail"],
        "job_postings_count": 28000,
    },
    "Power BI": {
        "skill_name": "Power BI", "demand_score": 82.0, "growth_rate": 22.0,
        "salary_impact": 20.0, "ai_relevance_score": 55.0,
        "top_industries": ["Finance", "Consulting", "IT"],
        "job_postings_count": 18000,
    },
    "SQL": {
        "skill_name": "SQL", "demand_score": 88.0, "growth_rate": 10.0,
        "salary_impact": 22.0, "ai_relevance_score": 70.0,
        "top_industries": ["IT", "Finance", "E-commerce"],
        "job_postings_count": 50000,
    },
    "Cloud Computing": {
        "skill_name": "Cloud Computing", "demand_score": 87.0, "growth_rate": 30.0,
        "salary_impact": 32.0, "ai_relevance_score": 75.0,
        "top_industries": ["IT", "Fintech", "Healthcare"],
        "job_postings_count": 28000,
    },
    "AI Literacy": {
        "skill_name": "AI Literacy", "demand_score": 80.0, "growth_rate": 118.0,
        "salary_impact": 15.0, "ai_relevance_score": 98.0,
        "top_industries": ["Education", "HR", "Marketing"],
        "job_postings_count": 8000,
    },
    "Machine Learning": {
        "skill_name": "Machine Learning", "demand_score": 91.0, "growth_rate": 25.0,
        "salary_impact": 38.0, "ai_relevance_score": 97.0,
        "top_industries": ["AI/ML", "Healthcare", "Finance"],
        "job_postings_count": 32000,
    },
    "Financial Modelling": {
        "skill_name": "Financial Modelling", "demand_score": 72.0, "growth_rate": 8.0,
        "salary_impact": 25.0, "ai_relevance_score": 40.0,
        "top_industries": ["Banking", "Consulting", "Private Equity"],
        "job_postings_count": 12000,
    },
}

# ── AI Vulnerability Data ────────────────────────────────
_AI_VULNERABILITY = {
    "Data Entry Operator": {
        "job_role": "Data Entry Operator", "vulnerability_score": 0.89,
        "risk_level": "high",
        "explanation": "Highly repetitive, rule-based tasks easily automated by OCR and RPA.",
        "factors": {"repetitiveness": 0.95, "cognitive_complexity": 0.15, "human_interaction": 0.10},
    },
    "Junior Accountant": {
        "job_role": "Junior Accountant", "vulnerability_score": 0.72,
        "risk_level": "high",
        "explanation": "Bookkeeping and routine filings are automatable; advisory work is safer.",
        "factors": {"repetitiveness": 0.80, "cognitive_complexity": 0.40, "human_interaction": 0.30},
    },
    "Customer Support Executive": {
        "job_role": "Customer Support Executive", "vulnerability_score": 0.65,
        "risk_level": "medium",
        "explanation": "Chatbots handle L1 queries; complex escalations still need humans.",
        "factors": {"repetitiveness": 0.60, "cognitive_complexity": 0.45, "human_interaction": 0.75},
    },
    "Content Writer": {
        "job_role": "Content Writer", "vulnerability_score": 0.58,
        "risk_level": "medium",
        "explanation": "AI generates generic content; creative strategy and brand voice remain human.",
        "factors": {"repetitiveness": 0.40, "cognitive_complexity": 0.65, "human_interaction": 0.50},
    },
    "Warehouse Supervisor": {
        "job_role": "Warehouse Supervisor", "vulnerability_score": 0.41,
        "risk_level": "low",
        "explanation": "Physical oversight, team management, and exception handling are hard to automate.",
        "factors": {"repetitiveness": 0.35, "cognitive_complexity": 0.55, "human_interaction": 0.80},
    },
    "Software Developer": {
        "job_role": "Software Developer", "vulnerability_score": 0.32,
        "risk_level": "low",
        "explanation": "AI assists coding but design decisions, debugging, and architecture remain human-driven.",
        "factors": {"repetitiveness": 0.20, "cognitive_complexity": 0.90, "human_interaction": 0.55},
    },
}

# ── Skill Trend Data ─────────────────────────────────────
_SKILL_TRENDS = {
    "top_growing_skills": {
        "Prompt Engineering": 142, "AI Literacy": 118, "Data Analytics": 95,
        "Cloud Computing": 88, "Cybersecurity": 76, "Python": 45,
        "Machine Learning": 40, "Power BI": 35, "SQL": 20,
    },
    "declining_skills": {
        "Tally": -12, "Excel": -5, "Manual Testing": -18,
        "Data Entry": -25, "Typing": -20,
    },
}

# ── Role → Related Skills Mapping ────────────────────────
_ROLE_SKILLS = {
    "Data Entry Operator": ["Excel", "Tally", "Data Entry", "Typing"],
    "Junior Accountant": ["Accounting", "Tally", "GST Filing", "Excel", "QuickBooks"],
    "Customer Support Executive": ["Communication", "CRM", "Ticketing Systems", "English"],
    "Content Writer": ["SEO Writing", "Content Marketing", "Copywriting", "WordPress", "Canva"],
    "Warehouse Supervisor": ["Inventory Management", "Logistics", "WMS", "Supply Chain"],
    "Software Developer": ["Python", "JavaScript", "SQL", "Git", "Cloud Computing"],
    "Financial Analyst": ["Financial Modelling", "Power BI", "Excel", "SQL", "Statistics"],
    "Data Analyst": ["Python", "SQL", "Data Visualization", "Statistics", "Excel"],
    "Product Manager": ["Product Thinking", "User Research", "SQL", "Wireframing", "Analytics"],
}

# ── Processed User Outputs (mock job market signals) ─────
_PROCESSED_OUTPUTS = {
    1: {
        "skills": ["Excel", "Tally", "Data Entry", "Typing"],
        "tools": ["MS Excel", "Tally ERP"],
        "tasks": ["Manual data entry", "Invoice processing", "Spreadsheet maintenance"],
        "aspirations": [],
    },
    2: {
        "skills": ["Accounting", "GST Filing", "Bookkeeping", "Tally", "QuickBooks"],
        "tools": ["Tally ERP", "QuickBooks", "MS Excel"],
        "tasks": ["GST return filing", "Ledger maintenance", "Bank reconciliation"],
        "aspirations": [],
    },
    3: {
        "skills": ["Communication", "CRM", "Problem Solving"],
        "tools": ["Freshdesk", "Zendesk"],
        "tasks": ["Customer calls", "Ticket resolution", "Escalation handling"],
        "aspirations": ["Product Management", "UX Research"],
    },
    4: {
        "skills": ["SEO Writing", "Content Marketing", "Copywriting", "WordPress", "Canva"],
        "tools": ["WordPress", "Canva", "Google Analytics"],
        "tasks": ["Blog writing", "Social media content creation", "Keyword research"],
        "aspirations": [],
    },
    5: {
        "skills": ["Inventory Management", "Logistics", "WMS", "Supply Chain"],
        "tools": ["WMS Software", "SAP", "Excel"],
        "tasks": ["Stock auditing", "Dispatch coordination", "Vendor communication"],
        "aspirations": [],
    },
}


# ═══════════════════════════════════════════════════════════
# Tool Functions (called by the agent)
# ═══════════════════════════════════════════════════════════

def get_skill_trends():
    """Return current skill demand trends (growing and declining)."""
    return _SKILL_TRENDS


def get_ai_vulnerability(role: str, city: str = ""):
    """Return AI automation vulnerability for a given job role."""
    # Try exact match first, then fuzzy
    for key, val in _AI_VULNERABILITY.items():
        if role.lower() in key.lower() or key.lower() in role.lower():
            result = dict(val)
            if city:
                result["city"] = city
            return result
    return {
        "job_role": role, "vulnerability_score": 0.50,
        "risk_level": "medium", "city": city,
        "explanation": f"No specific data for '{role}'. Estimated medium risk.",
        "factors": {},
    }


def get_skill_intel(skill: str):
    """Return intelligence data for a specific skill."""
    for key, val in _SKILL_INTEL.items():
        if skill.lower() == key.lower():
            return val
    return {"skill_name": skill, "demand_score": None, "message": "No data available"}


def get_related_skills(skill_or_role: str):
    """Return skills related to a given skill or role."""
    # Check role mapping
    for key, skills in _ROLE_SKILLS.items():
        if skill_or_role.lower() in key.lower() or key.lower() in skill_or_role.lower():
            return {"role": key, "related_skills": skills}
    # Check skill intel for industries overlap
    for key, val in _SKILL_INTEL.items():
        if skill_or_role.lower() == key.lower():
            related = [s for s in _SKILL_INTEL if s != key][:5]
            return {"skill": key, "related_skills": related}
    return {"query": skill_or_role, "related_skills": []}


def get_processed_output(user_id: int):
    """Return processed analysis output for a user (skills, tools, tasks, aspirations)."""
    return _PROCESSED_OUTPUTS.get(user_id, {
        "skills": [], "tools": [], "tasks": [], "aspirations": [],
        "message": "No processed data for this user",
    })


def get_all_skill_intel():
    """Return all skill intelligence data."""
    return list(_SKILL_INTEL.values())
