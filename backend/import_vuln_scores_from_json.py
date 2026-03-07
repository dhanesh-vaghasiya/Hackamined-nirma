"""
Import AI Vulnerability Scores from scoring_progress (1).json
============================================================
This script loads scores from the JSON file and upserts them into the ai_vulnerability_scores table.
Only roles present in the JSON will be shown in the dashboard/API.

Usage:
  1. Place this script in backend/
  2. Ensure scoring_progress (1).json is in backend/data/json/
  3. Activate your venv and set DATABASE_URL (or .env)
  4. Run: python import_vuln_scores_from_json.py
"""

import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "")
# Patch: allow SQLAlchemy-style URLs by removing '+psycopg2'
if DB_URL.startswith("postgresql+psycopg2://"):
    DB_URL = DB_URL.replace("postgresql+psycopg2://", "postgresql://", 1)
JSON_PATH = os.path.join("data", "json", "scoring_progress (1).json")

if not DB_URL:
    print("ERROR: DATABASE_URL not set in .env")
    sys.exit(1)

if not os.path.exists(JSON_PATH):
    print(f"ERROR: {JSON_PATH} not found")
    sys.exit(1)

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)
    scored = data.get("scored", {})

print(f"Loaded {len(scored)} roles from {JSON_PATH}")

conn = psycopg2.connect(DB_URL)

# Remove all existing scores (optional: comment out if you want to keep old ones)
with conn.cursor() as cur:
    cur.execute("DELETE FROM ai_vulnerability_scores WHERE city_id IS NULL")
    print(f"Cleared old vulnerability scores (city_id IS NULL)")
conn.commit()

# Upsert new scores
rows = []
now = datetime.utcnow()
for role, v in scored.items():
    score = int(v.get("score", 50))
    conf = float(v.get("confidence", 0.5))
    reason = str(v.get("reason", ""))[:500]
    if score == -1:
        continue  # skip non-IT
    rows.append({
        "job_title_norm": role,
        "score": score,
        "confidence": conf,
        "reason": reason,
        "computed_at": now,
    })

if not rows:
    print("No IT roles to import.")
    sys.exit(0)

sql = """
    INSERT INTO ai_vulnerability_scores (job_title_norm, city_id, score, confidence, reason, computed_at)
    VALUES (%(job_title_norm)s, NULL, %(score)s, %(confidence)s, %(reason)s, %(computed_at)s)
    ON CONFLICT (job_title_norm, city_id)
    DO UPDATE SET score = EXCLUDED.score,
                  confidence = EXCLUDED.confidence,
                  reason = EXCLUDED.reason,
                  computed_at = EXCLUDED.computed_at
"""

with conn.cursor() as cur:
    psycopg2.extras.execute_batch(cur, sql, rows, page_size=100)
conn.commit()
print(f"Imported {len(rows)} IT roles into ai_vulnerability_scores.")
conn.close()
