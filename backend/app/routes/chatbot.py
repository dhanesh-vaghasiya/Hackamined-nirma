from __future__ import annotations

import json
import logging

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc

from app import db
from app.models import ChatMessage, InsightDeck
from app.services.chatbot_agent import (
    build_system_prompt,
    detect_language,
    _call_groq_with_tools,
    extract_insight_deck,
    load_worker_context,
)

logger = logging.getLogger(__name__)

chatbot_bp = Blueprint("chatbot", __name__)


# ── helpers ────────────────────────────────────────────────

def _resolve_user_id() -> int | None:
    """Try to extract user_id from JWT without requiring auth."""
    try:
        uid = get_jwt_identity()
        return int(uid) if uid else None
    except Exception:
        return None


def _load_db_history(user_id: int | None, profile_id: int | None, limit: int = 10) -> list[dict]:
    """Load recent conversation history from the database."""
    if not user_id:
        return []

    q = db.session.query(ChatMessage).filter(ChatMessage.user_id == user_id)
    if profile_id:
        q = q.filter(ChatMessage.worker_profile_id == profile_id)

    recent = q.order_by(desc(ChatMessage.created_at)).limit(limit).all()
    recent.reverse()  # Oldest first

    return [{"role": m.role, "content": m.content} for m in recent]


def _save_message(user_id: int | None, profile_id: int | None,
                   role: str, content: str, language: str,
                   tool_data: str | None = None) -> None:
    """Persist a single chat message to the database."""
    if not user_id:
        return
    db.session.add(ChatMessage(
        user_id=user_id,
        worker_profile_id=profile_id,
        role=role,
        content=content,
        language=language,
        tool_data=tool_data,
    ))


# ── endpoints ──────────────────────────────────────────────

@chatbot_bp.route("/chat", methods=["POST"])
def chat():
    """
    Agentic chatbot endpoint.
    The LLM autonomously calls DB tools to fetch live data before answering.
    Conversation history is persisted in the database.
    """
    data = request.get_json(silent=True)
    if not data or not data.get("message", "").strip():
        return jsonify({"error": "message is required"}), 400

    user_message = data["message"].strip()
    profile_id = data.get("profile_id")
    frontend_history = data.get("history", [])

    # Resolve user (optional — works with or without JWT)
    user_id = _resolve_user_id()

    # Detect language
    language = detect_language(user_message)

    # Load worker profile context from DB
    worker_ctx = load_worker_context(profile_id)

    # Build system prompt
    system_prompt = build_system_prompt(worker_ctx, language)

    # Build message history: prefer DB history, fall back to frontend-supplied
    if user_id:
        db_history = _load_db_history(user_id, profile_id, limit=10)
    else:
        db_history = []

    if db_history:
        history = db_history
    else:
        history = [
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            for msg in frontend_history[-10:]
        ]

    # Add the user message to the history for the LLM
    history.append({"role": "user", "content": user_message})

    # Agentic call: LLM decides which tools to call
    reply, tools_used = _call_groq_with_tools(history, system_prompt)

    # Persist both messages to the database
    tool_data_json = json.dumps(tools_used) if tools_used else None
    _save_message(user_id, profile_id, "user", user_message, language)
    _save_message(user_id, profile_id, "assistant", reply, language, tool_data_json)

    # Generate Quick Insight Deck (always — even without auth)
    insight_deck_data = None
    try:
        deck = extract_insight_deck(user_message, reply, user_id or 0)
        if deck:
            if user_id:
                db.session.add(deck)
                # Will be committed together with the chat messages below
            # Always build the response dict from the deck object
            insight_deck_data = {
                "id": None,
                "user_id": user_id,
                "question": deck.question,
                "topic": deck.topic,
                "goal": deck.goal,
                "focus_area": deck.focus_area,
                "key_skills": [s.strip() for s in deck.key_skills.split(",") if s.strip()],
                "benefit": deck.benefit,
                "market_demand": deck.market_demand,
                "market_regions": deck.market_regions,
                "market_description": deck.market_description,
                "created_at": None,
            }
    except Exception:
        logger.exception("Failed to generate insight deck")

    try:
        db.session.commit()
        # Update the id/timestamp from the persisted deck
        if user_id and insight_deck_data:
            latest_deck = (
                db.session.query(InsightDeck)
                .filter(InsightDeck.user_id == user_id)
                .order_by(InsightDeck.created_at.desc())
                .first()
            )
            if latest_deck:
                insight_deck_data = latest_deck.to_dict()
    except Exception:
        logger.exception("Failed to save chat messages")
        db.session.rollback()

    return jsonify({
        "reply": reply,
        "language": language,
        "profile_id": profile_id,
        "tools_used": tools_used,
        "insight_deck": insight_deck_data,
    })


@chatbot_bp.route("/history", methods=["GET"])
@jwt_required()
def chat_history():
    """Get persisted chat history for the current user."""
    user_id = int(get_jwt_identity())
    profile_id = request.args.get("profile_id", type=int)

    q = db.session.query(ChatMessage).filter(ChatMessage.user_id == user_id)
    if profile_id:
        q = q.filter(ChatMessage.worker_profile_id == profile_id)

    messages = q.order_by(ChatMessage.created_at).limit(100).all()

    return jsonify([
        {
            "role": m.role,
            "content": m.content,
            "language": m.language,
            "tools_used": json.loads(m.tool_data) if m.tool_data else [],
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ])


@chatbot_bp.route("/insight-deck", methods=["GET"])
@jwt_required()
def get_insight_deck():
    """Get the latest insight deck for the current user."""
    user_id = int(get_jwt_identity())

    deck = (
        db.session.query(InsightDeck)
        .filter(InsightDeck.user_id == user_id)
        .order_by(InsightDeck.created_at.desc())
        .first()
    )
    if not deck:
        return jsonify(None)

    return jsonify(deck.to_dict())


@chatbot_bp.route("/insight-decks", methods=["GET"])
@jwt_required()
def get_insight_decks():
    """Get all insight decks for the current user (most recent first)."""
    user_id = int(get_jwt_identity())
    limit = request.args.get("limit", 10, type=int)

    decks = (
        db.session.query(InsightDeck)
        .filter(InsightDeck.user_id == user_id)
        .order_by(InsightDeck.created_at.desc())
        .limit(limit)
        .all()
    )

    return jsonify([d.to_dict() for d in decks])
