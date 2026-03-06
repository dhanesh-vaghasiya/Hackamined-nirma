from datetime import datetime
from app import db

def utcnow():
    return datetime.utcnow()

# ==========================================
# 1. USER & PROFILE MANAGEMENT
# ==========================================

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    profile = db.relationship("UserProfile", backref="user", uselist=False, lazy=True, cascade="all, delete-orphan")
    processed_outputs = db.relationship("ProcessedUserOutput", backref="user", lazy=True, cascade="all, delete-orphan")
    chat_sessions = db.relationship("ChatSession", backref="user", lazy=True, cascade="all, delete-orphan")
    reskilling_plans = db.relationship("ReskillingPlan", backref="user", lazy=True, cascade="all, delete-orphan")
    career_analyses = db.relationship("CareerAnalysis", backref="user", lazy=True, cascade="all, delete-orphan")

class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    location = db.Column(db.String(120), nullable=True)
    current_role = db.Column(db.String(120), nullable=True)
    years_of_experience = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=True) # Changed from String(120) to Text to allow 100-200 word inputs
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)


# ==========================================
# 2. WORKER INTELLIGENCE (NLP Extraction)
# ===================================F=======

class ProcessedUserOutput(db.Model):
    """Stores the normalized profile extracted from user input via LLM."""
    __tablename__ = "processed_user_outputs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    job_title = db.Column(db.String(150), nullable=True, index=True)
    city = db.Column(db.String(120), nullable=True, index=True)
    experience_years = db.Column(db.Float, nullable=True)
    domain = db.Column(db.String(120), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)

    # Replaced JSON with Explicit Child Relationships
    skills = db.relationship("ProcessedSkill", backref="processed_output", lazy=True, cascade="all, delete-orphan")
    tools = db.relationship("ProcessedTool", backref="processed_output", lazy=True, cascade="all, delete-orphan")
    tasks = db.relationship("ProcessedTask", backref="processed_output", lazy=True, cascade="all, delete-orphan")
    aspirations = db.relationship("ProcessedAspiration", backref="processed_output", lazy=True, cascade="all, delete-orphan")

class ProcessedSkill(db.Model):
    __tablename__ = "processed_skills"
    id = db.Column(db.Integer, primary_key=True)
    output_id = db.Column(db.Integer, db.ForeignKey("processed_user_outputs.id"), nullable=False)
    skill_name = db.Column(db.String(120), nullable=False)

class ProcessedTool(db.Model):
    __tablename__ = "processed_tools"
    id = db.Column(db.Integer, primary_key=True)
    output_id = db.Column(db.Integer, db.ForeignKey("processed_user_outputs.id"), nullable=False)
    tool_name = db.Column(db.String(120), nullable=False)

class ProcessedTask(db.Model):
    __tablename__ = "processed_tasks"
    id = db.Column(db.Integer, primary_key=True)
    output_id = db.Column(db.Integer, db.ForeignKey("processed_user_outputs.id"), nullable=False)
    task_name = db.Column(db.Text, nullable=False)

class ProcessedAspiration(db.Model):
    __tablename__ = "processed_aspirations"
    id = db.Column(db.Integer, primary_key=True)
    output_id = db.Column(db.Integer, db.ForeignKey("processed_user_outputs.id"), nullable=False)
    aspiration_name = db.Column(db.String(150), nullable=False)


# ==========================================
# 3. CAREER ANALYSIS & RISK (From career_analysis.json)
# ==========================================

class CareerAnalysis(db.Model):
    """Replaces JSON dumping for the AI Risk Analysis algorithm output"""
    __tablename__ = "career_analyses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(50), nullable=False) # e.g., 'LOW', 'HIGH'
    base_value = db.Column(db.Float, nullable=True) # From explainability
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    feature_contributions = db.relationship("FeatureContribution", backref="analysis", lazy=True, cascade="all, delete-orphan")
    recommendations = db.relationship("CareerRecommendation", backref="analysis", lazy=True, cascade="all, delete-orphan")

class FeatureContribution(db.Model):
    __tablename__ = "feature_contributions"
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey("career_analyses.id"), nullable=False)
    feature_name = db.Column(db.String(100), nullable=False) # e.g., 'avg_trend', 'automation_risk'
    contribution_value = db.Column(db.Float, nullable=False)

class CareerRecommendation(db.Model):
    __tablename__ = "career_recommendations"
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey("career_analyses.id"), nullable=False)
    recommendation_type = db.Column(db.String(50), nullable=False) # 'next_step', 'current_city', 'fallback'
    role = db.Column(db.String(150), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    recommendation_score = db.Column(db.Float, nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    reasoning_summary = db.Column(db.Text, nullable=True)

    missing_skills = db.relationship("MissingSkill", backref="recommendation", lazy=True, cascade="all, delete-orphan")

class MissingSkill(db.Model):
    __tablename__ = "missing_skills"
    id = db.Column(db.Integer, primary_key=True)
    recommendation_id = db.Column(db.Integer, db.ForeignKey("career_recommendations.id"), nullable=False)
    skill_name = db.Column(db.String(120), nullable=False)


# ==========================================
# 4. MARKET INTELLIGENCE (From job_trends.json)
# ==========================================

class JobTrendSummary(db.Model):
    """Replaces TrendSnapshot: Handles main job summary"""
    __tablename__ = "job_trend_summaries"

    id = db.Column(db.Integer, primary_key=True)
    job_title = db.Column(db.String(255), nullable=False, index=True)
    location = db.Column(db.String(150), nullable=True, index=True)
    trend_score = db.Column(db.Float, default=0.0)
    latest_count = db.Column(db.Integer, default=0)
    total_count = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    monthly_data = db.relationship("JobTrendMonthlyData", backref="summary", lazy=True, cascade="all, delete-orphan")
    
    # Ensuring no duplicates when upserting
    __table_args__ = (db.UniqueConstraint('job_title', 'location', name='uix_job_location'),)

class JobTrendMonthlyData(db.Model):
    """The Time-Series Data for Dashboard Charts"""
    __tablename__ = "job_trend_monthly_data"

    id = db.Column(db.Integer, primary_key=True)
    summary_id = db.Column(db.Integer, db.ForeignKey("job_trend_summaries.id"), nullable=False)
    trend_month = db.Column(db.String(10), nullable=False) # Stored as "YYYY-MM"
    post_count = db.Column(db.Integer, default=0)


# ==========================================
# 5. SKILL MARKET DATA (From skill_market_2020_present.json)
# ==========================================

class SkillMarketIntel(db.Model):
    """Replaces the old SkillIntel JSON dumps with exact analytical columns"""
    __tablename__ = "skill_market_intel"

    id = db.Column(db.Integer, primary_key=True)
    skill_name = db.Column(db.String(255), unique=True, nullable=False, index=True)
    first_month = db.Column(db.String(10), nullable=True) # "YYYY-MM"
    latest_month = db.Column(db.String(10), nullable=True)
    first_demand = db.Column(db.Integer, default=0)
    latest_demand = db.Column(db.Integer, default=0)
    total_demand = db.Column(db.Integer, default=0)
    percent_change = db.Column(db.Float, default=0.0)
    market_direction = db.Column(db.String(50), nullable=True) # 'increasing', 'stable', 'decreasing'
    market_summary = db.Column(db.Text, nullable=True)
    last_updated = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)


# ==========================================
# 6. AI VULNERABILITY INDEX
# ==========================================

class JobAIVulnerability(db.Model):
    """AI Disruption Data"""
    __tablename__ = "job_ai_vulnerabilities"

    id = db.Column(db.Integer, primary_key=True)
    job_role = db.Column(db.String(150), unique=True, nullable=False, index=True)
    vulnerability_score = db.Column(db.Float, nullable=False, index=True)
    risk_level = db.Column(db.String(50), nullable=True, index=True)
    explanation = db.Column(db.Text, nullable=True)
    computed_at = db.Column(db.DateTime, default=utcnow, nullable=False)

# ==========================================
# 7. RESKILLING & COURSES
# ==========================================

class ReskillingPlan(db.Model):
    __tablename__ = "reskilling_plans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    plan_type = db.Column(db.String(50), nullable=False, index=True)
    target_role = db.Column(db.String(120), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    target_skills = db.relationship("ReskillingPlanSkill", backref="plan", lazy=True, cascade="all, delete-orphan")
    weekly_items = db.relationship("RoadmapWeekItem", backref="plan", lazy=True, cascade="all, delete-orphan")

class ReskillingPlanSkill(db.Model):
    __tablename__ = "reskilling_plan_skills"
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("reskilling_plans.id"), nullable=False)
    skill_name = db.Column(db.String(120), nullable=False)

class RoadmapWeekItem(db.Model):
    __tablename__ = "roadmap_week_items"

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("reskilling_plans.id"), nullable=False, index=True)
    week_number = db.Column(db.Integer, nullable=False)
    course_name = db.Column(db.String(200), nullable=True)
    provider = db.Column(db.String(120), nullable=True) # e.g., NPTEL, SWAYAM
    link = db.Column(db.String(500), nullable=True)
    learning_objective = db.Column(db.Text, nullable=True) # Replaces JSON details
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)


# ==========================================
# 8. CHATBOT SESSIONS (Layer 2 Memory)
# ==========================================

class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(160), nullable=True)
    started_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    last_message_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)

    messages = db.relationship("ChatMessage", backref="session", lazy=True, cascade="all, delete-orphan")

class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False) # 'user', 'assistant', 'system'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

class City(db.Model):
    __tablename__ = "cities"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=False)
    state = db.Column(db.Text)
    tier = db.Column(db.Integer)

    # relationship
    jobs = db.relationship("Job", back_populates="city", cascade="all, delete")


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.Text)
    city_id = db.Column(db.Integer, db.ForeignKey("cities.id"))
    description = db.Column(db.Text)
    posted_date = db.Column(db.Date)
    scraped_at = db.Column(db.TIMESTAMP, default=utcnow, nullable=False)

    # relationship
    city = db.relationship("City", back_populates="jobs")