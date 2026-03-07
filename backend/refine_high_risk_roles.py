import os
import sys
import json
import time
import math
import psycopg2
import psycopg2.extras
import requests
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "")
if DB_URL.startswith("postgresql+psycopg2://"):
    DB_URL = DB_URL.replace("postgresql+psycopg2://", "postgresql://", 1)
GROQ_KEY = os.getenv("GROQ_API_KEY", "")
MODEL = "llama-3.3-70b-versatile"
BATCH_SIZE = 20

def get_db():
    return psycopg2.connect(DB_URL)

def get_high_risk_roles(conn):
    """Fetch roles that currently have a high AI risk score (>= 75) or are explicitly AI-related but scored high."""
    with conn.cursor() as cur:
        # We fetch top 150 highest risk roles to refine them, plus any role containing 'ai', 'data', 'cloud', 'ml' that is > 50
        cur.execute("""
            SELECT job_title_norm, score 
            FROM ai_vulnerability_scores 
            WHERE score >= 70 OR (score >= 50 AND job_title_norm ILIKE '%ai%')
            ORDER BY score DESC
            LIMIT 200
        """)
        return [r[0] for r in cur.fetchall()]

def build_prompt(roles):
    lines = "\n".join(f"- {r}" for r in roles)
    return (
        "You are an expert AI workforce analyst. Your job is to score how vulnerable the following IT job roles are to being REPLACED by AI or automation tools.\n"
        "Vulnerability Score (0-100):\n"
        "- 100 = Extremely high risk of full automation (e.g. basic data entry, simple manual QA, basic level 1 support).\n"
        "- 0 = Zero risk of automation.\n\n"
        "🚨 CRITICAL RULES 🚨\n"
        "1. Roles that involve BUILDING, MANAGING, or DEPLOYING AI/ML (e.g. 'AI Developer', 'Prompt Engineer', 'Deep Learning Engineer', 'Databricks', 'Data Scientist') "
        "are the ones CREATING the automation! They are at VERY LOW RISK. Score them 0-15.\n"
        "2. Senior architectural roles, hardware engineers, and physical network engineers (e.g. 'Cloud Architect', 'Network Engineer', 'Hardware Design') are LOW RISK (15-30).\n"
        "3. Highly automatable roles like 'Manual Tester', 'L1 Support', 'Basic HTML/CSS Coder', or generic 'Administrative/Data Entry' roles are HIGH RISK (80-100).\n"
        "4. Provide a brief 10-15 word reason.\n\n"
        "Return ONLY valid JSON in this exact format:\n"
        "{\"items\": [{\"role\": \"exact name from list\", \"score\": 0-100, \"reason\": \"...\"}]}\n\n"
        f"Roles to score:\n{lines}"
    )

def call_groq(roles):
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "You are a precise JSON-only API. Apply the rules strictly."},
            {"role": "user", "content": build_prompt(roles)},
        ],
    }

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers, json=payload, timeout=60,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return parsed.get("items", [])
    except Exception as e:
        print(f"Groq API error: {e}")
        return []

def upsert_scores(conn, scored_rows):
    if not scored_rows:
        return
    sql = """
        UPDATE ai_vulnerability_scores
        SET score = %(score)s, reason = %(reason)s, confidence = 0.95
        WHERE job_title_norm = %(role)s AND city_id IS NULL
    """
    with conn.cursor() as cur:
        psycopg2.extras.execute_batch(cur, sql, scored_rows)
    conn.commit()

def main():
    if not GROQ_KEY or not DB_URL:
        print("Missing API keys or DB URL.")
        sys.exit(1)

    conn = get_db()
    
    print("Fetching roles to refine...")
    roles = get_high_risk_roles(conn)
    print(f"Found {len(roles)} roles to refine.")

    batches = math.ceil(len(roles) / BATCH_SIZE)
    updated_count = 0

    for i in range(batches):
        chunk = roles[i*BATCH_SIZE : (i+1)*BATCH_SIZE]
        print(f"Scoring batch {i+1}/{batches} ({len(chunk)} roles)...")
        
        items = call_groq(chunk)
        if not items:
            print("  Failed to get scores for batch. Retrying in 5s...")
            time.sleep(5)
            items = call_groq(chunk)
            
        scored_rows = []
        for item in items:
            role_name = item.get("role")
            score = item.get("score")
            reason = item.get("reason", "")[:240]
            if role_name and score is not None:
                scored_rows.append({"role": role_name, "score": int(score), "reason": reason})

        if scored_rows:
            upsert_scores(conn, scored_rows)
            updated_count += len(scored_rows)
            print(f"  Updated {len(scored_rows)} roles.")
        
        time.sleep(2) # rate limit prevention

    print(f"\\nDone! Refined {updated_count} roles.")
    conn.close()

if __name__ == "__main__":
    main()
