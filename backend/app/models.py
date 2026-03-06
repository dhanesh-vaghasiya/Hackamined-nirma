from datetime import datetime

from app import db


def utcnow():
    return datetime.utcnow()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    profile = db.relationship(
        "UserProfile",
        backref="user",
        uselist=False,
        lazy=True,
        cascade="all, delete-orphan",
    )
    processed_outputs = db.relationship(
        "ProcessedUserOutput",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
    )
    chat_sessions = db.relationship(
        "ChatSession",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
    )
    reskilling_plans = db.relationship(
        "ReskillingPlan",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<User {self.email}>"


class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    phone = db.Column(db.String(30), nullable=True)
    location = db.Column(db.String(120), nullable=True)
    current_role = db.Column(db.String(120), nullable=True)
    years_of_experience = db.Column(db.Float, nullable=True)
    education = db.Column(db.String(160), nullable=True)
    preferences_json = db.Column(db.JSON, nullable=True)
    profile_json = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class ProcessedUserOutput(db.Model):
    __tablename__ = "processed_user_outputs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    source = db.Column(db.String(80), nullable=True)
    output_type = db.Column(db.String(80), nullable=False, index=True)
    input_json = db.Column(db.JSON, nullable=True)
    output_json = db.Column(db.JSON, nullable=False)
    model_name = db.Column(db.String(120), nullable=True)
    model_version = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)


class TrendSnapshot(db.Model):
    __tablename__ = "trend_snapshots"

    id = db.Column(db.Integer, primary_key=True)
    metric_name = db.Column(db.String(120), nullable=False, index=True)
    timeframe = db.Column(db.String(80), nullable=True)
    generated_by = db.Column(db.String(120), nullable=True)
    model_version = db.Column(db.String(80), nullable=True)
    trend_json = db.Column(db.JSON, nullable=False)
    metadata_json = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)


class SkillIntel(db.Model):
    __tablename__ = "skill_intel"

    id = db.Column(db.Integer, primary_key=True)
    skill_name = db.Column(db.String(120), nullable=False, index=True)
    timeframe = db.Column(db.String(80), nullable=True, index=True)
    demand_score = db.Column(db.Float, nullable=True)
    growth_rate = db.Column(db.Float, nullable=True)
    salary_impact = db.Column(db.Float, nullable=True)
    ai_relevance_score = db.Column(db.Float, nullable=True)
    intelligence_json = db.Column(db.JSON, nullable=False)
    source = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)


class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(160), nullable=True)
    started_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    last_message_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)

    messages = db.relationship(
        "ChatMessage",
        backref="session",
        lazy=True,
        cascade="all, delete-orphan",
    )


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    message_json = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)


class ReskillingPlan(db.Model):
    __tablename__ = "reskilling_plans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    plan_type = db.Column(db.String(30), nullable=False, index=True)
    target_role = db.Column(db.String(120), nullable=True)
    selected_skills_json = db.Column(db.JSON, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    roadmap_json = db.Column(db.JSON, nullable=False)
    created_by = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)

    weekly_items = db.relationship(
        "RoadmapWeekItem",
        backref="plan",
        lazy=True,
        cascade="all, delete-orphan",
    )


class RoadmapWeekItem(db.Model):
    __tablename__ = "roadmap_week_items"

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("reskilling_plans.id"), nullable=False, index=True)
    week_number = db.Column(db.Integer, nullable=False, index=True)
    course_name = db.Column(db.String(200), nullable=True)
    provider = db.Column(db.String(120), nullable=True)
    link = db.Column(db.String(500), nullable=True)
    details_json = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)


class JobAIVulnerability(db.Model):
    __tablename__ = "job_ai_vulnerabilities"

    id = db.Column(db.Integer, primary_key=True)
    job_role = db.Column(db.String(150), nullable=False, index=True)
    vulnerability_score = db.Column(db.Float, nullable=False, index=True)
    risk_level = db.Column(db.String(20), nullable=True, index=True)
    model_version = db.Column(db.String(80), nullable=True)
    explanation = db.Column(db.Text, nullable=True)
    factors_json = db.Column(db.JSON, nullable=True)
    source = db.Column(db.String(120), nullable=True)
    computed_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)
