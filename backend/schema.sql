-- ============================================================
-- OASIS — Workforce Intelligence Platform
-- Database Schema (PostgreSQL)
-- ============================================================

-- Drop existing tables in reverse dependency order
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS reskilling_path_steps CASCADE;
DROP TABLE IF EXISTS reskilling_paths CASCADE;
DROP TABLE IF EXISTS risk_assessments CASCADE;
DROP TABLE IF EXISTS worker_profiles CASCADE;
DROP TABLE IF EXISTS skill_trends CASCADE;
DROP TABLE IF EXISTS job_skills CASCADE;
DROP TABLE IF EXISTS ai_vulnerability_scores CASCADE;
DROP TABLE IF EXISTS jobs CASCADE;
DROP TABLE IF EXISTS courses CASCADE;
DROP TABLE IF EXISTS cities CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ── 1. CITIES ──────────────────────────────────────────────
CREATE TABLE cities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    state VARCHAR(100),
    tier SMALLINT CHECK (tier BETWEEN 1 AND 3)
);
CREATE INDEX idx_cities_name ON cities(name);

-- ── 2. USERS ───────────────────────────────────────────────
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_users_email ON users(email);

-- ── 3. JOBS (scraped postings) ─────────────────────────────
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(300) NOT NULL,
    title_norm VARCHAR(300),
    company VARCHAR(200),
    city_id INTEGER REFERENCES cities(id),
    location_raw VARCHAR(200),
    description TEXT,
    source VARCHAR(50) DEFAULT 'naukri',
    posted_date DATE,
    scraped_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_jobs_title_norm ON jobs(title_norm);
CREATE INDEX idx_jobs_city ON jobs(city_id);
CREATE INDEX idx_jobs_posted ON jobs(posted_date);

-- ── 4. JOB_SKILLS (extracted per-posting) ──────────────────
CREATE TABLE job_skills (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    skill_name VARCHAR(100) NOT NULL
);
CREATE INDEX idx_job_skills_job ON job_skills(job_id);
CREATE INDEX idx_job_skills_name ON job_skills(skill_name);

-- ── 5. AI_VULNERABILITY_SCORES (per normalized role + city)─
CREATE TABLE ai_vulnerability_scores (
    id SERIAL PRIMARY KEY,
    job_title_norm VARCHAR(300) NOT NULL,
    city_id INTEGER REFERENCES cities(id),
    score SMALLINT NOT NULL CHECK (score BETWEEN 0 AND 100),
    confidence REAL DEFAULT 0.5,
    reason TEXT,
    computed_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(job_title_norm, city_id)
);
CREATE INDEX idx_vuln_role ON ai_vulnerability_scores(job_title_norm);
CREATE INDEX idx_vuln_city ON ai_vulnerability_scores(city_id);

-- ── 6. SKILL_TRENDS (aggregated demand by period) ──────────
CREATE TABLE skill_trends (
    id SERIAL PRIMARY KEY,
    skill_name VARCHAR(100) NOT NULL,
    city_id INTEGER REFERENCES cities(id),
    period DATE NOT NULL,
    demand_count INTEGER DEFAULT 0,
    change_pct REAL DEFAULT 0.0,
    UNIQUE(skill_name, city_id, period)
);
CREATE INDEX idx_skill_trends_skill ON skill_trends(skill_name);
CREATE INDEX idx_skill_trends_period ON skill_trends(period);

-- ── 7. COURSES (NPTEL, SWAYAM, PMKVY, etc.) ───────────────
CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    title VARCHAR(300) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    institution VARCHAR(200),
    url TEXT,
    duration_weeks SMALLINT,
    is_free BOOLEAN DEFAULT TRUE,
    skills_covered TEXT[],
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_courses_provider ON courses(provider);
CREATE INDEX idx_courses_skills ON courses USING GIN(skills_covered);

-- ── 8. WORKER_PROFILES ────────────────────────────────────
CREATE TABLE worker_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    job_title VARCHAR(200) NOT NULL,
    job_title_norm VARCHAR(200),
    city_id INTEGER REFERENCES cities(id),
    experience_years SMALLINT DEFAULT 0,
    writeup TEXT NOT NULL,
    extracted_skills TEXT[],
    extracted_tasks TEXT[],
    aspirations TEXT[],
    domain VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_wp_user ON worker_profiles(user_id);

-- ── 9. RISK_ASSESSMENTS ───────────────────────────────────
CREATE TABLE risk_assessments (
    id SERIAL PRIMARY KEY,
    worker_profile_id INTEGER REFERENCES worker_profiles(id) ON DELETE CASCADE,
    score SMALLINT NOT NULL CHECK (score BETWEEN 0 AND 100),
    risk_level VARCHAR(10) NOT NULL CHECK (risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    hiring_trend_pct REAL,
    ai_mention_pct REAL,
    peer_percentile REAL,
    factors TEXT[],
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_ra_profile ON risk_assessments(worker_profile_id);

-- ── 10. RESKILLING_PATHS ──────────────────────────────────
CREATE TABLE reskilling_paths (
    id SERIAL PRIMARY KEY,
    risk_assessment_id INTEGER REFERENCES risk_assessments(id) ON DELETE CASCADE,
    target_role VARCHAR(200) NOT NULL,
    target_role_hiring_count INTEGER DEFAULT 0,
    total_weeks SMALLINT DEFAULT 8,
    hours_per_week SMALLINT DEFAULT 10,
    confidence REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE reskilling_path_steps (
    id SERIAL PRIMARY KEY,
    reskilling_path_id INTEGER REFERENCES reskilling_paths(id) ON DELETE CASCADE,
    step_order SMALLINT NOT NULL,
    week_start SMALLINT NOT NULL,
    week_end SMALLINT NOT NULL,
    course_id INTEGER REFERENCES courses(id),
    title VARCHAR(300) NOT NULL,
    provider VARCHAR(100),
    skill_focus VARCHAR(200),
    notes TEXT
);

-- ── 11. CHAT_MESSAGES (conversation history) ──────────────
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    worker_profile_id INTEGER REFERENCES worker_profiles(id),
    role VARCHAR(10) NOT NULL CHECK (role IN ('user','assistant')),
    content TEXT NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_chat_user ON chat_messages(user_id);
CREATE INDEX idx_chat_profile ON chat_messages(worker_profile_id);