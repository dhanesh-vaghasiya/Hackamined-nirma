from __future__ import annotations

import os
import re
import json

import requests
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, desc

from app import db
from app.models import (
    AiVulnerabilityScore,
    ChatMessage,
    City,
    Course,
    Job,
    RiskAssessment,
    SkillTrend,
    WorkerProfile,
)

chatbot_bp = Blueprint("chatbot", __name__)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


def _get_groq_key() -> str | None:
    return os.getenv("GROQ_API_KEY", "").strip() or None


def _detect_language(text: str) -> str:
    hindi_pattern = re.compile(r"[\u0900-\u097F]")
    if hindi_pattern.search(text):
        return "hi"
    return "en"


def _get_worker_context(profile_id: int | None) -> dict:
    """Gather worker profile + risk assessment context from DB."""
    if not profile_id:
        return {}

    wp = db.session.query(WorkerProfile).get(profile_id)
    if not wp:
        return {}

    city_name = wp.city.name if wp.city else "Unknown"

    # Latest risk assessment
    ra = (
        db.session.query(RiskAssessment)
        .filter(RiskAssessment.worker_profile_id == wp.id)
        .order_by(desc(RiskAssessment.created_at))
        .first()
    )

    # Hiring data for this role in this city
    hiring_count = 0
    if wp.city_id:
        hiring_count = (
            db.session.query(func.count(Job.id))
            .filter(Job.city_id == wp.city_id, Job.title_norm.ilike(f"%{wp.job_title_norm}%"))
            .scalar() or 0
        )

    # Top trending skills in city
    trending = (
        db.session.query(SkillTrend.skill_name, func.sum(SkillTrend.demand_count).label("d"))
        .filter(SkillTrend.city_id == wp.city_id)
        .group_by(SkillTrend.skill_name)
        .order_by(desc("d"))
        .limit(10)
        .all()
    ) if wp.city_id else []

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


def _get_market_context(query: str, city_name: str | None) -> dict:
    """Pull relevant market data for the query."""
    context = {}

    # Check if asking about specific job count
    bpo_match = re.search(r"(bpo|data entry|software|developer|analyst|engineer)", query.lower())
    city_match = re.search(r"(mumbai|pune|bengaluru|delhi|hyderabad|chennai|indore|jaipur|ahmedabad|kolkata|lucknow|bhopal|surat|nagpur)", query.lower())

    search_city = city_match.group(1) if city_match else city_name
    search_role = bpo_match.group(1) if bpo_match else None

    if search_role and search_city:
        city = db.session.query(City).filter(func.lower(City.name) == search_city.lower()).first()
        if city:
            count = (
                db.session.query(func.count(Job.id))
                .filter(Job.city_id == city.id, Job.title_norm.ilike(f"%{search_role}%"))
                .scalar() or 0
            )
            context["job_count"] = {"role": search_role, "city": search_city, "count": count}

    # Available courses
    courses = db.session.query(Course).limit(10).all()
    context["available_courses"] = [
        {"title": c.title, "provider": c.provider, "duration_weeks": c.duration_weeks, "url": c.url, "is_free": c.is_free}
        for c in courses
    ]

    return context


def _build_system_prompt(worker_ctx: dict, market_ctx: dict, language: str) -> str:
    lang_instruction = ""
    if language == "hi":
        lang_instruction = "IMPORTANT: The user is communicating in Hindi. You MUST respond entirely in Hindi (Devanagari script). Do NOT switch to English."

    prompt = f"""You are the OASIS Intelligence Assistant — an AI career advisor for Indian workers.
You help workers understand their AI displacement risk, find safer career paths, and get reskilling guidance.

{lang_instruction}

RULES:
1. Always cite specific data when answering. Never hallucinate numbers.
2. If you have worker profile context, reference their specific role, city, and risk score.
3. For reskilling recommendations, suggest real courses from NPTEL, SWAYAM, or PMKVY with week-by-week schedules.
4. For job count questions, use the exact numbers provided in context.
5. Explain risk scores by citing specific factors (hiring decline %, AI tool mentions, etc.)
6. Keep responses concise but actionable.
7. If asked in Hindi, respond fully in Hindi.

WORKER PROFILE CONTEXT:
{json.dumps(worker_ctx, indent=2, ensure_ascii=False) if worker_ctx else "No worker profile loaded yet."}

MARKET DATA CONTEXT:
{json.dumps(market_ctx, indent=2, ensure_ascii=False)}
"""
    return prompt


def _call_groq(messages: list[dict], system_prompt: str) -> str:
    """Call Groq LLM API."""
    api_key = _get_groq_key()
    if not api_key:
        return _fallback_response(messages[-1]["content"] if messages else "")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "temperature": 0.7,
        "max_tokens": 1024,
    }

    try:
        resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        return _fallback_response(messages[-1]["content"] if messages else "")


def _fallback_response(query: str) -> str:
    """Provide a meaningful response without LLM API."""
    q = query.lower()

    if "risk" in q or "score" in q or "high" in q or "why" in q:
        return ("Your risk score is computed based on three signals: "
                "(1) AI vulnerability index for your role — how much of your work can be automated, "
                "(2) Hiring trends in your city — whether demand for your role is growing or declining, "
                "(3) Your experience level. "
                "To see specific factors, check the risk assessment panel in the Worker Portal.")

    if "path" in q or "reskill" in q or "month" in q or "course" in q or "learn" in q:
        return ("Based on available data, I recommend starting with: "
                "Week 1-4: NPTEL Data Basics (IIT Madras, free, 6 hrs/week), "
                "Week 5-8: SWAYAM AI Fundamentals (free, certificate available), "
                "Week 9-12: PMKVY Digital Marketing (government subsidised). "
                "These map directly to rising skill demands in your region.")

    if "job" in q or "bpo" in q or "hiring" in q or "how many" in q:
        return ("I can look up live job counts from our database. "
                "Please specify the role and city you're interested in, "
                "e.g., 'How many BPO jobs are in Pune right now?'")

    if re.search(r"[\u0900-\u097F]", q):
        return ("आपकी प्रोफ़ाइल के आधार पर, मैं NPTEL और SWAYAM के मुफ़्त कोर्स से शुरू करने की सलाह दूँगा। "
                "ये कोर्स आपके क्षेत्र में बढ़ती माँग वाले कौशलों से सीधे जुड़े हैं। "
                "कृपया अपना प्रोफ़ाइल भरें ताकि मैं आपको व्यक्तिगत मार्गदर्शन दे सकूँ।")

    return ("I'm the OASIS Intelligence Assistant. I can help you with: "
            "understanding your AI risk score, finding reskilling paths, "
            "checking job market data, and career transition guidance. "
            "What would you like to know?")


@chatbot_bp.route("/chat", methods=["POST"])
def chat():
    """AI chatbot endpoint — context-aware, supports English + Hindi."""
    data = request.get_json(silent=True)
    if not data or not data.get("message", "").strip():
        return jsonify({"error": "message is required"}), 400

    user_message = data["message"].strip()
    profile_id = data.get("profile_id")
    history = data.get("history", [])  # Previous messages for context

    # Detect language
    language = _detect_language(user_message)

    # Gather context
    worker_ctx = _get_worker_context(profile_id)
    market_ctx = _get_market_context(user_message, worker_ctx.get("city"))

    # Build LLM prompt
    system_prompt = _build_system_prompt(worker_ctx, market_ctx, language)

    # Build message history
    messages = []
    for msg in history[-8:]:  # Last 8 messages for context window
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    messages.append({"role": "user", "content": user_message})

    # Call LLM
    reply = _call_groq(messages, system_prompt)

    # Save to DB if user is authenticated
    user_id = None
    try:
        from flask_jwt_extended import get_jwt_identity
        user_id = get_jwt_identity()
    except Exception:
        pass

    if user_id:
        db.session.add(ChatMessage(
            user_id=int(user_id), worker_profile_id=profile_id,
            role="user", content=user_message, language=language,
        ))
        db.session.add(ChatMessage(
            user_id=int(user_id), worker_profile_id=profile_id,
            role="assistant", content=reply, language=language,
        ))
        db.session.commit()

    return jsonify({
        "reply": reply,
        "language": language,
        "profile_id": profile_id,
    })


@chatbot_bp.route("/history", methods=["GET"])
@jwt_required()
def chat_history():
    """Get chat history for current user."""
    user_id = int(get_jwt_identity())
    profile_id = request.args.get("profile_id", type=int)

    q = db.session.query(ChatMessage).filter(ChatMessage.user_id == user_id)
    if profile_id:
        q = q.filter(ChatMessage.worker_profile_id == profile_id)

    messages = q.order_by(ChatMessage.created_at).limit(50).all()
    return jsonify([
        {"role": m.role, "content": m.content, "language": m.language, "created_at": m.created_at.isoformat()}
        for m in messages
    ])
