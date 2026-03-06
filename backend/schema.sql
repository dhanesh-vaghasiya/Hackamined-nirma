CREATE TABLE cities (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    state TEXT,
    tier INTEGER
);

CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    title TEXT,
    company TEXT,
    city_id INTEGER REFERENCES cities(id),
    description TEXT,
    job_url TEXT UNIQUE,
    posted_date DATE,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE job_skills (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    skill_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE worker_profiles (
    id SERIAL PRIMARY KEY,
    title TEXT,
    city_id INTEGER REFERENCES cities(id),
    experience_years INTEGER,
    writeup TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE risk_scores (
    id SERIAL PRIMARY KEY,
    role TEXT,
    city_id INTEGER REFERENCES cities(id),
    score INTEGER,
    computed_at TIMESTAMP
);

CREATE TABLE skill_trends (
    id SERIAL PRIMARY KEY,
    skill_id INTEGER REFERENCES skills(id),
    city_id INTEGER REFERENCES cities(id),
    demand_score INTEGER,
    period_start DATE,
    period_end DATE
);