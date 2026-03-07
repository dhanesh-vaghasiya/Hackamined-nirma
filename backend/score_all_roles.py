"""
Batch Groq AI Vulnerability Scorer
===================================
Scores ALL unique IT job roles from the jobs table using Groq LLM.
- Skips non-IT roles (Groq classifies them; we discard)
- Re-scores fallback heuristic entries (confidence=0.25)
- Scores previously unscored roles
- Upserts into ai_vulnerability_scores table
- Handles rate limits with exponential backoff
"""

import json
import os
import sys
import time
import math
import re
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
import requests
from dotenv import load_dotenv

load_dotenv()

# ── Config ──
DB_URL = os.getenv("DATABASE_URL", "")
GROQ_KEY = os.getenv("GROQ_API_KEY", "")
MODEL = "llama-3.3-70b-versatile"
BATCH_SIZE = 25          # roles per Groq call
BASE_SLEEP = 2.0         # seconds between calls
MAX_RETRIES = 4          # retries per batch on rate limit
SKIP_ALREADY_SCORED = True  # skip roles with confidence > 0.5 (real Groq scores)


def get_db():
    """Parse SQLAlchemy URL to psycopg2 params."""
    url = DB_URL.replace("postgresql+psycopg2://", "")
    userpass, hostdb = url.split("@")
    user, password = userpass.split(":")
    host_port, dbname = hostdb.split("/")
    host = host_port.split(":")[0]
    port = int(host_port.split(":")[1]) if ":" in host_port else 5432
    return psycopg2.connect(host=host, port=port, dbname=dbname,
                            user=user, password=password)


def fetch_all_roles(conn):
    """Get all unique role names from jobs table."""
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT title_norm FROM jobs WHERE title_norm IS NOT NULL ORDER BY title_norm")
        return [r[0] for r in cur.fetchall()]


def fetch_already_scored(conn):
    """Get roles already scored with real Groq confidence (>0.5)."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT job_title_norm FROM ai_vulnerability_scores WHERE confidence > 0.5"
        )
        return {r[0] for r in cur.fetchall()}


def build_prompt(roles):
    """Prompt that scores IT roles and marks non-IT ones."""
    lines = "\n".join(f"- {r}" for r in roles)
    return (
        "You are an AI workforce analyst. For each job role below, determine:\n"
        "1. Is this an IT/Tech/Software/Data/Digital role? (is_it: true/false)\n"
        "2. If IT: rate AI automation vulnerability 0-100. Higher = more likely to be automated by AI.\n"
        "   Consider: Can AI tools (code generators, chatbots, RPA, ML models) replace core tasks?\n"
        "3. Provide a brief reason (max 15 words).\n\n"
        "Return ONLY valid JSON: {\"items\": [{\"role\": \"exact name\", \"is_it\": true/false, "
        "\"score\": 0-100, \"reason\": \"...\"}]}\n"
        "For non-IT roles, set score to -1.\n\n"
        f"Roles:\n{lines}"
    )


def call_groq(roles, attempt=0):
    """Call Groq API for a batch of roles. Returns parsed items list."""
    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "Respond strictly in JSON."},
            {"role": "user", "content": build_prompt(roles)},
        ],
    }

    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers, json=payload, timeout=90,
    )

    if resp.status_code == 429:
        if attempt >= MAX_RETRIES:
            raise RuntimeError(f"Rate limited after {MAX_RETRIES} retries")
        wait = min(60, BASE_SLEEP * (2 ** (attempt + 1)))
        retry_after = resp.headers.get("retry-after")
        if retry_after:
            wait = max(wait, float(retry_after))
        print(f"    Rate limited. Waiting {wait:.0f}s (attempt {attempt+1}/{MAX_RETRIES})...")
        time.sleep(wait)
        return call_groq(roles, attempt + 1)

    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    return parsed.get("items", []) if isinstance(parsed, dict) else []


def upsert_scores(conn, scored_rows):
    """Upsert scored roles into ai_vulnerability_scores."""
    if not scored_rows:
        return
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
        psycopg2.extras.execute_batch(cur, sql, scored_rows, page_size=100)
    conn.commit()


def delete_non_it_scores(conn, non_it_roles):
    """Remove non-IT roles from scores table."""
    if not non_it_roles:
        return
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM ai_vulnerability_scores WHERE job_title_norm = ANY(%s)",
            (list(non_it_roles),)
        )
        deleted = cur.rowcount
    conn.commit()
    if deleted:
        print(f"  Cleaned {deleted} non-IT entries from DB")


def main():
    if not GROQ_KEY:
        print("ERROR: GROQ_API_KEY not set in .env")
        sys.exit(1)

    conn = get_db()
    print("Connected to PostgreSQL")

    # 1. Get all unique roles
    all_roles = fetch_all_roles(conn)
    print(f"Total unique roles in jobs table: {len(all_roles)}")

    # 2. Get already properly scored roles (skip these)
    already_scored = fetch_already_scored(conn) if SKIP_ALREADY_SCORED else set()
    print(f"Already Groq-scored (confidence > 0.5): {len(already_scored)}")

    # 3. Filter to roles that need scoring
    to_score = [r for r in all_roles if r not in already_scored]
    print(f"Roles to score: {len(to_score)}")

    total_batches = math.ceil(len(to_score) / BATCH_SIZE)
    print(f"Batches of {BATCH_SIZE}: {total_batches}")
    print("=" * 60)

    now = datetime.now(timezone.utc)
    stats = {"scored": 0, "non_it": 0, "failed": 0, "batches": 0}
    non_it_all = set()

    for batch_idx in range(total_batches):
        start = batch_idx * BATCH_SIZE
        end = min(len(to_score), start + BATCH_SIZE)
        chunk = to_score[start:end]

        print(f"\n[{batch_idx+1}/{total_batches}] Scoring roles {start+1}-{end}...")

        try:
            items = call_groq(chunk)

            # Map results by normalized role name
            result_map = {}
            for item in items:
                name = str(item.get("role", "")).strip().lower()
                name = re.sub(r"\s+", " ", name)
                result_map[name] = item

            scored_rows = []
            batch_non_it = set()

            for role in chunk:
                result = result_map.get(role)
                if not result:
                    # Try fuzzy match
                    for k, v in result_map.items():
                        if role in k or k in role:
                            result = v
                            break

                if not result:
                    stats["failed"] += 1
                    continue

                is_it = result.get("is_it", True)
                score = int(result.get("score", -1))

                if not is_it or score == -1:
                    batch_non_it.add(role)
                    stats["non_it"] += 1
                    continue

                score = max(0, min(100, score))
                reason = str(result.get("reason", "")).strip()[:240]

                scored_rows.append({
                    "job_title_norm": role,
                    "score": score,
                    "confidence": 0.85,
                    "reason": reason,
                    "computed_at": now,
                })
                stats["scored"] += 1

            # Upsert IT scores
            upsert_scores(conn, scored_rows)

            # Clean non-IT from DB
            if batch_non_it:
                non_it_all.update(batch_non_it)
                delete_non_it_scores(conn, batch_non_it)

            stats["batches"] += 1
            it_count = len(scored_rows)
            skip_count = len(batch_non_it)
            print(f"  -> {it_count} IT scored, {skip_count} non-IT skipped")

        except Exception as exc:
            print(f"  ERROR: {exc}")
            stats["failed"] += len(chunk)

        # Rate limit pacing
        time.sleep(BASE_SLEEP)

    print("\n" + "=" * 60)
    print(f"DONE!")
    print(f"  Batches completed: {stats['batches']}/{total_batches}")
    print(f"  IT roles scored:   {stats['scored']}")
    print(f"  Non-IT skipped:    {stats['non_it']}")
    print(f"  Failed/missing:    {stats['failed']}")

    # Final count
    with conn.cursor() as cur:
        cur.execute("SELECT count(*), round(avg(score)::numeric, 1) FROM ai_vulnerability_scores")
        total, avg = cur.fetchone()
        print(f"  DB total scores:   {total} (avg: {avg})")

    conn.close()


if __name__ == "__main__":
    main()
