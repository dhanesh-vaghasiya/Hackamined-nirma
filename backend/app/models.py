from app import db
from datetime import datetime


# ── 1. CITIES ────────────────────────────────────────────────
class City(db.Model):
    __tablename__ = "cities"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    state = db.Column(db.String(100))
    tier = db.Column(db.SmallInteger)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "state": self.state, "tier": self.tier}


# ── 2. USERS ─────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email, "created_at": self.created_at.isoformat()}


# ── 3. JOBS ──────────────────────────────────────────────────
class Job(db.Model):
    __tablename__ = "jobs"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    title_norm = db.Column(db.String(300))
    company = db.Column(db.String(200))
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"))
    location_raw = db.Column(db.String(200))
    description = db.Column(db.Text)
    source = db.Column(db.String(50), default="naukri")
    posted_date = db.Column(db.Date)
    scraped_at = db.Column(db.DateTime, default=datetime.utcnow)

    city = db.relationship("City", backref="jobs", lazy="joined")
    skills = db.relationship("JobSkill", backref="job", lazy="select", cascade="all, delete-orphan")


# ── 4. JOB_SKILLS ───────────────────────────────────────────
class JobSkill(db.Model):
    __tablename__ = "job_skills"
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id", ondelete="CASCADE"))
    skill_name = db.Column(db.String(100), nullable=False)


# ── 5. AI_VULNERABILITY_SCORES ──────────────────────────────
class AiVulnerabilityScore(db.Model):
    __tablename__ = "ai_vulnerability_scores"
    id = db.Column(db.Integer, primary_key=True)
    job_title_norm = db.Column(db.String(300), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"))
    score = db.Column(db.SmallInteger, nullable=False)
    confidence = db.Column(db.Float, default=0.5)
    reason = db.Column(db.Text)
    computed_at = db.Column(db.DateTime, default=datetime.utcnow)

    city = db.relationship("City", backref="vulnerability_scores", lazy="joined")

    __table_args__ = (db.UniqueConstraint("job_title_norm", "city_id"),)


# ── 6. SKILL_TRENDS ─────────────────────────────────────────
class SkillTrend(db.Model):
    __tablename__ = "skill_trends"
    id = db.Column(db.Integer, primary_key=True)
    skill_name = db.Column(db.String(100), nullable=False)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"))
    period = db.Column(db.Date, nullable=False)
    demand_count = db.Column(db.Integer, default=0)
    change_pct = db.Column(db.Float, default=0.0)

    city = db.relationship("City", backref="skill_trends", lazy="joined")

    __table_args__ = (db.UniqueConstraint("skill_name", "city_id", "period"),)


# ── 7. COURSES ───────────────────────────────────────────────
class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    provider = db.Column(db.String(50), nullable=False)
    institution = db.Column(db.String(200))
    url = db.Column(db.Text)
    duration_weeks = db.Column(db.SmallInteger)
    is_free = db.Column(db.Boolean, default=True)
    skills_covered = db.Column(db.ARRAY(db.Text))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ── 8. WORKER_PROFILES ──────────────────────────────────────
class WorkerProfile(db.Model):
    __tablename__ = "worker_profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"))
    job_title = db.Column(db.String(200), nullable=False)
    job_title_norm = db.Column(db.String(200))
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"))
    experience_years = db.Column(db.SmallInteger, default=0)
    writeup = db.Column(db.Text, nullable=False)
    extracted_skills = db.Column(db.ARRAY(db.Text))
    extracted_tasks = db.Column(db.ARRAY(db.Text))
    aspirations = db.Column(db.ARRAY(db.Text))
    domain = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="profiles", lazy="joined")
    city = db.relationship("City", backref="worker_profiles", lazy="joined")


# ── 9. RISK_ASSESSMENTS ─────────────────────────────────────
class RiskAssessment(db.Model):
    __tablename__ = "risk_assessments"
    id = db.Column(db.Integer, primary_key=True)
    worker_profile_id = db.Column(db.Integer, db.ForeignKey("worker_profiles.id", ondelete="CASCADE"))
    score = db.Column(db.SmallInteger, nullable=False)
    risk_level = db.Column(db.String(10), nullable=False)
    hiring_trend_pct = db.Column(db.Float)
    ai_mention_pct = db.Column(db.Float)
    peer_percentile = db.Column(db.Float)
    factors = db.Column(db.ARRAY(db.Text))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship("WorkerProfile", backref="risk_assessments", lazy="joined")


# ── 10. RESKILLING_PATHS ────────────────────────────────────
class ReskillingPath(db.Model):
    __tablename__ = "reskilling_paths"
    id = db.Column(db.Integer, primary_key=True)
    risk_assessment_id = db.Column(db.Integer, db.ForeignKey("risk_assessments.id", ondelete="CASCADE"))
    target_role = db.Column(db.String(200), nullable=False)
    target_role_hiring_count = db.Column(db.Integer, default=0)
    total_weeks = db.Column(db.SmallInteger, default=8)
    hours_per_week = db.Column(db.SmallInteger, default=10)
    confidence = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assessment = db.relationship("RiskAssessment", backref="reskilling_paths", lazy="joined")
    steps = db.relationship("ReskillingPathStep", backref="path", lazy="select", cascade="all, delete-orphan", order_by="ReskillingPathStep.step_order")


class ReskillingPathStep(db.Model):
    __tablename__ = "reskilling_path_steps"
    id = db.Column(db.Integer, primary_key=True)
    reskilling_path_id = db.Column(db.Integer, db.ForeignKey("reskilling_paths.id", ondelete="CASCADE"))
    step_order = db.Column(db.SmallInteger, nullable=False)
    week_start = db.Column(db.SmallInteger, nullable=False)
    week_end = db.Column(db.SmallInteger, nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"))
    title = db.Column(db.String(300), nullable=False)
    provider = db.Column(db.String(100))
    skill_focus = db.Column(db.String(200))
    notes = db.Column(db.Text)

    course = db.relationship("Course", backref="path_steps", lazy="joined")


# ── 11. CHAT_MESSAGES ───────────────────────────────────────
class ChatMessage(db.Model):
    __tablename__ = "chat_messages"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"))
    worker_profile_id = db.Column(db.Integer, db.ForeignKey("worker_profiles.id"))
    role = db.Column(db.String(10), nullable=False)
    content = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10), default="en")
    tool_data = db.Column(db.Text)  # JSON string of tools used by agent
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ── 12. INSIGHT_DECKS ───────────────────────────────────────
class InsightDeck(db.Model):
    __tablename__ = "insight_decks"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question = db.Column(db.Text, nullable=False)
    # Card 1: User Question Summary
    topic = db.Column(db.String(200), nullable=False)
    goal = db.Column(db.String(200), nullable=False)
    # Card 2: Key Takeaway
    focus_area = db.Column(db.String(300), nullable=False)
    key_skills = db.Column(db.Text, nullable=False)       # comma-separated
    benefit = db.Column(db.String(300), nullable=False)
    # Card 3: Market Snapshot
    market_demand = db.Column(db.String(300), nullable=False)
    market_regions = db.Column(db.String(300), nullable=False)
    market_description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "question": self.question,
            "topic": self.topic,
            "goal": self.goal,
            "focus_area": self.focus_area,
            "key_skills": [s.strip() for s in self.key_skills.split(",") if s.strip()],
            "benefit": self.benefit,
            "market_demand": self.market_demand,
            "market_regions": self.market_regions,
            "market_description": self.market_description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }