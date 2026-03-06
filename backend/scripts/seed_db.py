"""
Dummy seed data for testing.
Run: python -m scripts.seed_db
This will insert test data into the database.
Use --dry-run to just print the data without inserting.
"""

import sys
import json
from datetime import datetime, timedelta

DRY_RUN = "--dry-run" in sys.argv

# ── Helpers ──────────────────────────────────────────────
now = datetime.utcnow()

def ts(days_ago=0):
    return (now - timedelta(days=days_ago)).isoformat()

# ── 1. Users ─────────────────────────────────────────────
USERS = [
    {"id": 1, "name": "Aarav Sharma",   "email": "aarav@example.com",   "password": "hashed_pw_1"},
    {"id": 2, "name": "Priya Patel",    "email": "priya@example.com",   "password": "hashed_pw_2"},
    {"id": 3, "name": "Rohan Mehta",    "email": "rohan@example.com",   "password": "hashed_pw_3"},
    {"id": 4, "name": "Sneha Gupta",    "email": "sneha@example.com",   "password": "hashed_pw_4"},
    {"id": 5, "name": "Vikram Singh",   "email": "vikram@example.com",  "password": "hashed_pw_5"},
]

# ── 2. User Profiles ────────────────────────────────────
USER_PROFILES = [
    {
        "id": 1, "user_id": 1, "phone": "9876543210", "location": "Ahmedabad",
        "current_role": "Data Entry Operator", "years_of_experience": 3.0,
        "education": "B.Com from Gujarat University",
        "preferences_json": {"learning_mode": "online", "hours_per_week": 10},
        "profile_json": {"summary": "Experienced in manual data processing and Excel."},
    },
    {
        "id": 2, "user_id": 2, "phone": "9123456780", "location": "Mumbai",
        "current_role": "Junior Accountant", "years_of_experience": 5.0,
        "education": "M.Com from Mumbai University",
        "preferences_json": {"learning_mode": "hybrid", "hours_per_week": 8},
        "profile_json": {"summary": "Handles bookkeeping and GST filings for SMEs."},
    },
    {
        "id": 3, "user_id": 3, "phone": "9988776655", "location": "Bangalore",
        "current_role": "Customer Support Executive", "years_of_experience": 2.0,
        "education": "BBA from Christ University",
        "preferences_json": {"learning_mode": "online", "hours_per_week": 12},
        "profile_json": {"summary": "Works in voice-based tech support for a SaaS product."},
    },
    {
        "id": 4, "user_id": 4, "phone": "9012345678", "location": "Pune",
        "current_role": "Content Writer", "years_of_experience": 4.0,
        "education": "BA English from Pune University",
        "preferences_json": {"learning_mode": "offline", "hours_per_week": 6},
        "profile_json": {"summary": "Writes blog posts, social media copy, and SEO content."},
    },
    {
        "id": 5, "user_id": 5, "phone": "9871234560", "location": "Delhi",
        "current_role": "Warehouse Supervisor", "years_of_experience": 7.0,
        "education": "Diploma in Supply Chain Management",
        "preferences_json": {"learning_mode": "online", "hours_per_week": 5},
        "profile_json": {"summary": "Manages inventory and logistics for an e-commerce warehouse."},
    },
]

# ── 3. Processed User Outputs ───────────────────────────
PROCESSED_USER_OUTPUTS = [
    {
        "id": 1, "user_id": 1, "source": "profile_analysis", "output_type": "skill_extraction",
        "input_json": {"text": "I do data entry in Excel and some basic Tally work."},
        "output_json": {
            "skills": ["Excel", "Tally", "Data Entry", "Typing"],
            "tools": ["MS Excel", "Tally ERP"],
            "tasks": ["Manual data entry", "Invoice processing", "Spreadsheet maintenance"],
        },
        "model_name": "skill_extractor", "model_version": "1.0",
    },
    {
        "id": 2, "user_id": 2, "source": "profile_analysis", "output_type": "skill_extraction",
        "input_json": {"text": "I handle bookkeeping, GST returns, and use Tally and QuickBooks."},
        "output_json": {
            "skills": ["Accounting", "GST Filing", "Bookkeeping", "Tally", "QuickBooks"],
            "tools": ["Tally ERP", "QuickBooks", "MS Excel"],
            "tasks": ["GST return filing", "Ledger maintenance", "Bank reconciliation"],
        },
        "model_name": "skill_extractor", "model_version": "1.0",
    },
    {
        "id": 3, "user_id": 3, "source": "profile_analysis", "output_type": "aspiration_detection",
        "input_json": {"text": "I want to move into product management or UX research."},
        "output_json": {
            "aspirations": ["Product Management", "UX Research"],
            "confidence": 0.85,
        },
        "model_name": "aspiration_detector", "model_version": "1.0",
    },
    {
        "id": 4, "user_id": 4, "source": "profile_analysis", "output_type": "skill_extraction",
        "input_json": {"text": "I write SEO blogs, social media posts, and use WordPress and Canva."},
        "output_json": {
            "skills": ["SEO Writing", "Content Marketing", "Copywriting", "WordPress", "Canva"],
            "tools": ["WordPress", "Canva", "Google Analytics"],
            "tasks": ["Blog writing", "Social media content creation", "Keyword research"],
        },
        "model_name": "skill_extractor", "model_version": "1.0",
    },
    {
        "id": 5, "user_id": 5, "source": "profile_analysis", "output_type": "skill_extraction",
        "input_json": {"text": "I manage warehouse inventory with WMS, handle dispatches."},
        "output_json": {
            "skills": ["Inventory Management", "Logistics", "WMS", "Supply Chain"],
            "tools": ["WMS Software", "SAP", "Excel"],
            "tasks": ["Stock auditing", "Dispatch coordination", "Vendor communication"],
        },
        "model_name": "skill_extractor", "model_version": "1.0",
    },
]

# ── 4. Trend Snapshots ──────────────────────────────────
TREND_SNAPSHOTS = [
    {
        "id": 1, "metric_name": "ai_automation_risk_by_role", "timeframe": "Q1-2026",
        "generated_by": "trend_engine", "model_version": "2.0",
        "trend_json": {
            "Data Entry Operator": 0.89,
            "Junior Accountant": 0.72,
            "Customer Support Executive": 0.65,
            "Content Writer": 0.58,
            "Warehouse Supervisor": 0.41,
        },
        "metadata_json": {"sample_size": 15000, "region": "India"},
    },
    {
        "id": 2, "metric_name": "top_growing_skills", "timeframe": "2025-2026",
        "generated_by": "trend_engine", "model_version": "2.0",
        "trend_json": {
            "Prompt Engineering": 142, "AI Literacy": 118, "Data Analytics": 95,
            "Cloud Computing": 88, "Cybersecurity": 76,
        },
        "metadata_json": {"unit": "percent_growth_yoy"},
    },
    {
        "id": 3, "metric_name": "reskilling_completion_rate", "timeframe": "2025",
        "generated_by": "analytics_pipeline", "model_version": "1.5",
        "trend_json": {"online": 0.62, "hybrid": 0.74, "offline": 0.81},
        "metadata_json": {"total_learners": 8500},
    },
]

# ── 5. Skill Intel ───────────────────────────────────────
SKILL_INTEL = [
    {
        "id": 1, "skill_name": "Python", "timeframe": "2026",
        "demand_score": 92.0, "growth_rate": 18.5, "salary_impact": 30.0, "ai_relevance_score": 95.0,
        "intelligence_json": {"top_industries": ["IT", "Finance", "Healthcare"], "job_postings_count": 45000},
        "source": "naukri_scraper",
    },
    {
        "id": 2, "skill_name": "Prompt Engineering", "timeframe": "2026",
        "demand_score": 88.0, "growth_rate": 142.0, "salary_impact": 25.0, "ai_relevance_score": 99.0,
        "intelligence_json": {"top_industries": ["AI/ML", "Marketing", "Education"], "job_postings_count": 12000},
        "source": "naukri_scraper",
    },
    {
        "id": 3, "skill_name": "Excel", "timeframe": "2026",
        "demand_score": 75.0, "growth_rate": -5.0, "salary_impact": 8.0, "ai_relevance_score": 30.0,
        "intelligence_json": {"top_industries": ["Finance", "Admin", "Retail"], "job_postings_count": 62000},
        "source": "naukri_scraper",
    },
    {
        "id": 4, "skill_name": "Data Analytics", "timeframe": "2026",
        "demand_score": 90.0, "growth_rate": 35.0, "salary_impact": 28.0, "ai_relevance_score": 85.0,
        "intelligence_json": {"top_industries": ["IT", "E-commerce", "BFSI"], "job_postings_count": 38000},
        "source": "naukri_scraper",
    },
    {
        "id": 5, "skill_name": "Cybersecurity", "timeframe": "2026",
        "demand_score": 85.0, "growth_rate": 28.0, "salary_impact": 35.0, "ai_relevance_score": 60.0,
        "intelligence_json": {"top_industries": ["IT", "Banking", "Government"], "job_postings_count": 22000},
        "source": "naukri_scraper",
    },
    {
        "id": 6, "skill_name": "Tally", "timeframe": "2026",
        "demand_score": 55.0, "growth_rate": -12.0, "salary_impact": 5.0, "ai_relevance_score": 15.0,
        "intelligence_json": {"top_industries": ["Finance", "SME", "Retail"], "job_postings_count": 28000},
        "source": "naukri_scraper",
    },
]

# ── 6. Chat Sessions & Messages ─────────────────────────
CHAT_SESSIONS = [
    {"id": 1, "user_id": 1, "title": "Career guidance for data entry"},
    {"id": 2, "user_id": 2, "title": "Upskilling path for accountants"},
    {"id": 3, "user_id": 3, "title": "Transition to product management"},
]

CHAT_MESSAGES = [
    {"id": 1, "session_id": 1, "role": "user",      "content": "Is data entry at risk from AI?", "message_json": None},
    {"id": 2, "session_id": 1, "role": "assistant",  "content": "Yes, data entry is among the most AI-automatable roles. Consider learning Python or data analytics to pivot.", "message_json": {"confidence": 0.92}},
    {"id": 3, "session_id": 1, "role": "user",      "content": "What courses should I start with?", "message_json": None},
    {"id": 4, "session_id": 1, "role": "assistant",  "content": "Start with Google Data Analytics Certificate on Coursera, then move to Python basics on freeCodeCamp.", "message_json": {"sources": ["coursera", "freecodecamp"]}},
    {"id": 5, "session_id": 2, "role": "user",      "content": "Will AI replace accountants?", "message_json": None},
    {"id": 6, "session_id": 2, "role": "assistant",  "content": "Routine bookkeeping is at high risk, but advisory and compliance roles are safer. Learning Power BI and financial modelling helps.", "message_json": {"confidence": 0.88}},
    {"id": 7, "session_id": 3, "role": "user",      "content": "How do I move from customer support to product management?", "message_json": None},
    {"id": 8, "session_id": 3, "role": "assistant",  "content": "Leverage your customer empathy. Learn product frameworks (RICE, MoSCoW), take a PM course, and build a side-project case study.", "message_json": {"confidence": 0.80}},
]

# ── 7. Reskilling Plans & Roadmap Items ──────────────────
RESKILLING_PLANS = [
    {
        "id": 1, "user_id": 1, "plan_type": "career_pivot", "target_role": "Data Analyst",
        "selected_skills_json": ["Python", "SQL", "Data Visualization", "Statistics"],
        "summary": "12-week plan to transition from data entry to a junior data analyst role.",
        "roadmap_json": {
            "total_weeks": 12,
            "phases": ["Foundations", "Intermediate", "Projects & Portfolio"],
        },
        "created_by": "ai_planner",
    },
    {
        "id": 2, "user_id": 2, "plan_type": "upskill", "target_role": "Financial Analyst",
        "selected_skills_json": ["Power BI", "Financial Modelling", "Advanced Excel", "SQL"],
        "summary": "8-week plan to upgrade from junior accountant to financial analyst.",
        "roadmap_json": {
            "total_weeks": 8,
            "phases": ["Tool Mastery", "Analytical Thinking", "Case Studies"],
        },
        "created_by": "ai_planner",
    },
    {
        "id": 3, "user_id": 3, "plan_type": "career_pivot", "target_role": "Product Manager",
        "selected_skills_json": ["Product Thinking", "User Research", "SQL", "Wireframing"],
        "summary": "16-week guided plan to move from support to product management.",
        "roadmap_json": {
            "total_weeks": 16,
            "phases": ["PM Foundations", "User Research", "Execution & Launch"],
        },
        "created_by": "ai_planner",
    },
]

ROADMAP_WEEK_ITEMS = [
    # Plan 1 – Data Analyst
    {"id": 1,  "plan_id": 1, "week_number": 1, "course_name": "Python for Everybody",         "provider": "Coursera",      "link": "https://coursera.org/python-for-everybody", "details_json": {"hours": 10}},
    {"id": 2,  "plan_id": 1, "week_number": 2, "course_name": "SQL Basics",                    "provider": "Khan Academy",  "link": "https://khanacademy.org/sql",                "details_json": {"hours": 8}},
    {"id": 3,  "plan_id": 1, "week_number": 3, "course_name": "Intro to Data Visualization",   "provider": "freeCodeCamp",  "link": "https://freecodecamp.org/dataviz",           "details_json": {"hours": 10}},
    {"id": 4,  "plan_id": 1, "week_number": 5, "course_name": "Statistics Fundamentals",        "provider": "Udemy",         "link": "https://udemy.com/statistics-101",            "details_json": {"hours": 12}},
    {"id": 5,  "plan_id": 1, "week_number": 8, "course_name": "Pandas & NumPy Deep Dive",      "provider": "DataCamp",      "link": "https://datacamp.com/pandas-numpy",           "details_json": {"hours": 10}},
    {"id": 6,  "plan_id": 1, "week_number": 10,"course_name": "Capstone: EDA Project",          "provider": "Self-paced",    "link": None,                                          "details_json": {"hours": 15}},
    # Plan 2 – Financial Analyst
    {"id": 7,  "plan_id": 2, "week_number": 1, "course_name": "Power BI Essentials",            "provider": "Microsoft Learn", "link": "https://learn.microsoft.com/powerbi",       "details_json": {"hours": 8}},
    {"id": 8,  "plan_id": 2, "week_number": 3, "course_name": "Financial Modelling 101",        "provider": "CFI",             "link": "https://corporatefinanceinstitute.com/fm",  "details_json": {"hours": 10}},
    {"id": 9,  "plan_id": 2, "week_number": 5, "course_name": "Advanced Excel for Finance",     "provider": "Udemy",           "link": "https://udemy.com/advanced-excel-finance",  "details_json": {"hours": 8}},
    {"id": 10, "plan_id": 2, "week_number": 7, "course_name": "SQL for Business Analytics",     "provider": "Coursera",        "link": "https://coursera.org/sql-business",         "details_json": {"hours": 10}},
    # Plan 3 – Product Manager
    {"id": 11, "plan_id": 3, "week_number": 1, "course_name": "Intro to Product Management",    "provider": "Udemy",           "link": "https://udemy.com/intro-pm",                "details_json": {"hours": 8}},
    {"id": 12, "plan_id": 3, "week_number": 4, "course_name": "User Research Methods",          "provider": "Coursera",        "link": "https://coursera.org/user-research",        "details_json": {"hours": 10}},
    {"id": 13, "plan_id": 3, "week_number": 8, "course_name": "SQL for PMs",                    "provider": "DataCamp",        "link": "https://datacamp.com/sql-pm",               "details_json": {"hours": 6}},
    {"id": 14, "plan_id": 3, "week_number": 12,"course_name": "Wireframing with Figma",         "provider": "Skillshare",      "link": "https://skillshare.com/figma",              "details_json": {"hours": 8}},
]

# ── 8. Job AI Vulnerabilities ────────────────────────────
JOB_AI_VULNERABILITIES = [
    {
        "id": 1, "job_role": "Data Entry Operator", "vulnerability_score": 0.89,
        "risk_level": "high", "model_version": "2.0",
        "explanation": "Highly repetitive, rule-based tasks easily automated by OCR and RPA.",
        "factors_json": {"repetitiveness": 0.95, "cognitive_complexity": 0.15, "human_interaction": 0.10},
        "source": "ai_risk_model",
    },
    {
        "id": 2, "job_role": "Junior Accountant", "vulnerability_score": 0.72,
        "risk_level": "high", "model_version": "2.0",
        "explanation": "Bookkeeping and routine filings are automatable; advisory work is safer.",
        "factors_json": {"repetitiveness": 0.80, "cognitive_complexity": 0.40, "human_interaction": 0.30},
        "source": "ai_risk_model",
    },
    {
        "id": 3, "job_role": "Customer Support Executive", "vulnerability_score": 0.65,
        "risk_level": "medium", "model_version": "2.0",
        "explanation": "Chatbots handle L1 queries; complex escalations still need humans.",
        "factors_json": {"repetitiveness": 0.60, "cognitive_complexity": 0.45, "human_interaction": 0.75},
        "source": "ai_risk_model",
    },
    {
        "id": 4, "job_role": "Content Writer", "vulnerability_score": 0.58,
        "risk_level": "medium", "model_version": "2.0",
        "explanation": "AI generates generic content; creative strategy and brand voice remain human.",
        "factors_json": {"repetitiveness": 0.40, "cognitive_complexity": 0.65, "human_interaction": 0.50},
        "source": "ai_risk_model",
    },
    {
        "id": 5, "job_role": "Warehouse Supervisor", "vulnerability_score": 0.41,
        "risk_level": "low", "model_version": "2.0",
        "explanation": "Physical oversight, team management, and exception handling are hard to automate.",
        "factors_json": {"repetitiveness": 0.35, "cognitive_complexity": 0.55, "human_interaction": 0.80},
        "source": "ai_risk_model",
    },
    {
        "id": 6, "job_role": "Software Developer", "vulnerability_score": 0.32,
        "risk_level": "low", "model_version": "2.0",
        "explanation": "AI assists coding but design decisions, debugging, and architecture remain human-driven.",
        "factors_json": {"repetitiveness": 0.20, "cognitive_complexity": 0.90, "human_interaction": 0.55},
        "source": "ai_risk_model",
    },
]

# ═══════════════════════════════════════════════════════════
# Print / Insert
# ═══════════════════════════════════════════════════════════
ALL_DATA = {
    "users": USERS,
    "user_profiles": USER_PROFILES,
    "processed_user_outputs": PROCESSED_USER_OUTPUTS,
    "trend_snapshots": TREND_SNAPSHOTS,
    "skill_intel": SKILL_INTEL,
    "chat_sessions": CHAT_SESSIONS,
    "chat_messages": CHAT_MESSAGES,
    "reskilling_plans": RESKILLING_PLANS,
    "roadmap_week_items": ROADMAP_WEEK_ITEMS,
    "job_ai_vulnerabilities": JOB_AI_VULNERABILITIES,
}

if DRY_RUN:
    print("=== DRY RUN — no database changes ===\n")
    for table, rows in ALL_DATA.items():
        print(f"📋 {table}: {len(rows)} rows")
        for row in rows:
            print(f"   {json.dumps(row, default=str, indent=None)}")
        print()
    print("✅ Seed data preview complete. Pass without --dry-run to insert into DB.")
    sys.exit(0)

# ── Actual DB insert ─────────────────────────────────────
from app import create_app, db
from app.models import (
    User, UserProfile, ProcessedUserOutput,
    TrendSnapshot, SkillIntel,
    ChatSession, ChatMessage,
    ReskillingPlan, RoadmapWeekItem,
    JobAIVulnerability,
)

MODEL_MAP = {
    "users": User,
    "user_profiles": UserProfile,
    "processed_user_outputs": ProcessedUserOutput,
    "trend_snapshots": TrendSnapshot,
    "skill_intel": SkillIntel,
    "chat_sessions": ChatSession,
    "chat_messages": ChatMessage,
    "reskilling_plans": ReskillingPlan,
    "roadmap_week_items": RoadmapWeekItem,
    "job_ai_vulnerabilities": JobAIVulnerability,
}

app = create_app()

with app.app_context():
    for table_name, rows in ALL_DATA.items():
        model = MODEL_MAP[table_name]
        for row in rows:
            obj = model(**row)
            db.session.add(obj)
        print(f"✅ Inserted {len(rows)} rows into {table_name}")
    db.session.commit()
    print("\n🎉 All seed data inserted successfully!")
