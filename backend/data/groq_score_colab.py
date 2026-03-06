
"""
OASIS — Gemini AI Vulnerability Scorer (Google Colab)
=====================================================
Upload: unique_roles_to_score.csv  (single column: title_norm)
Output: ai_vulnerability_scored.csv

Steps in Colab:
    1. Upload this script + the CSV
    2. pip install google-generativeai
    3. Set your GEMINI_API_KEY
    4. Run — it processes in batches, auto-saves progress
    5. Download ai_vulnerability_scored.csv → bring back

Non-IT roles are auto-skipped by the prompt.
"""


import csv
import json
import os
import time
import google.generativeai as genai

# ─── CONFIG ───
GEMINI_API_KEY = ""  # <-- paste your key here, or set env var
MODEL = "gemini-1.5-pro-latest"  # or your preferred Gemini model
BATCH_SIZE = 25          # roles per Gemini call
SLEEP_BETWEEN = 2.0      # seconds between batches (rate limit safety)
MAX_RETRIES = 3
INPUT_FILE = "unique_roles_to_score.csv"
OUTPUT_FILE = "ai_vulnerability_scored.csv"
PROGRESS_FILE = "scoring_progress.json"  # tracks where we left off

# ─── PROMPT ───
def build_prompt(roles):
    lines = "\n".join(f"- {r}" for r in roles)
    return (
        "You are an AI workforce analyst scoring IT/tech job roles for AI automation vulnerability.\n\n"
        "RULES:\n"
        "1. Score ONLY IT/tech/software/data roles (0-100). Higher = more automatable by current AI.\n"
        "2. If a role is clearly NON-IT (e.g. chef, nurse, driver, mechanic, teacher, hotel staff, "
        "air hostess, accountant, CA, doctor, civil engineer, electrical engineer not in software), "
        'set score to -1 and reason to "non-IT role".\n'
        "3. Return ONLY valid JSON: {\"items\": [{\"role\": \"exact name\", \"score\": int, \"confidence\": float 0-1, \"reason\": \"max 20 words\"}]}\n\n"
        f"Roles:\n{lines}"
    )

# ─── GEMINI CALL ───
def score_batch(roles, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL)
    prompt = build_prompt(roles)
    for attempt in range(MAX_RETRIES):
        try:
            response = model.generate_content(prompt, generation_config={"temperature": 0.0})
            content = response.text
            parsed = json.loads(content)
            items = parsed.get("items", []) if isinstance(parsed, dict) else []
            result = {}
            for item in items:
                name = str(item.get("role", "")).strip().lower()
                if not name:
                    continue
                score = int(item.get("score", 50))
                conf = float(item.get("confidence", 0.5))
                reason = str(item.get("reason", ""))[:200]
                result[name] = {"score": score, "confidence": round(min(1.0, max(0.0, conf)), 2), "reason": reason}
            # fill missing roles from this batch
            for r in roles:
                key = r.strip().lower()
                if key not in result:
                    result[key] = {"score": 50, "confidence": 0.2, "reason": "missing from model response"}
            return result
        except Exception as e:
            print(f"  Gemini error: {e}")
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(SLEEP_BETWEEN * 2)

# ─── MAIN ───
def main():
    api_key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        print("ERROR: Set GEMINI_API_KEY at the top of the script or as env var")
        return

    # Load roles
    roles = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            r = row.get("title_norm", "").strip()
            if r:
                roles.append(r)

    print(f"Loaded {len(roles)} roles from {INPUT_FILE}")

    # Load progress (resume support)
    scored = {}
    start_batch = 0
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            progress = json.load(f)
            scored = progress.get("scored", {})
            start_batch = progress.get("next_batch", 0)
        print(f"Resuming from batch {start_batch} ({len(scored)} already scored)")

    # Batch processing
    total_batches = (len(roles) + BATCH_SIZE - 1) // BATCH_SIZE
    failed_batches = []

    for batch_idx in range(start_batch, total_batches):
        start = batch_idx * BATCH_SIZE
        end = min(len(roles), start + BATCH_SIZE)
        chunk = roles[start:end]

        # Skip already scored
        unseen = [r for r in chunk if r.lower() not in scored]
        if not unseen:
            continue

        print(f"Batch {batch_idx + 1}/{total_batches} — scoring {len(unseen)} roles ({start+1}-{end})")

        for attempt in range(MAX_RETRIES):
            try:
                result = score_batch(unseen, api_key)
                for k, v in result.items():
                    scored[k] = v
                break
            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code == 429:
                    wait = min(60, SLEEP_BETWEEN * (attempt + 2) * 3)
                    print(f"  Rate limited, waiting {wait:.0f}s...")
                    time.sleep(wait)
                else:
                    print(f"  HTTP error: {e}")
                    if attempt == MAX_RETRIES - 1:
                        failed_batches.append(batch_idx)
                    time.sleep(SLEEP_BETWEEN * 2)
            except Exception as e:
                print(f"  Error: {e}")
                if attempt == MAX_RETRIES - 1:
                    failed_batches.append(batch_idx)
                time.sleep(SLEEP_BETWEEN * 2)

        # Save progress every 5 batches
        if (batch_idx + 1) % 5 == 0 or batch_idx == total_batches - 1:
            with open(PROGRESS_FILE, "w") as f:
                json.dump({"scored": scored, "next_batch": batch_idx + 1}, f)
            print(f"  Progress saved: {len(scored)} scored")

        time.sleep(SLEEP_BETWEEN)

    # ─── Write output CSV ───
    print(f"\nWriting {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["job_title_norm", "ai_vulnerability_score", "confidence", "reason"])

        it_count = 0
        non_it_count = 0
        for role in roles:
            key = role.strip().lower()
            data = scored.get(key, {"score": 50, "confidence": 0.1, "reason": "unscored"})
            if data["score"] == -1:
                non_it_count += 1
                continue  # skip non-IT
            writer.writerow([key, data["score"], data["confidence"], data["reason"]])
            it_count += 1

    print(f"\nDONE!")
    print(f"  IT roles scored: {it_count}")
    print(f"  Non-IT skipped:  {non_it_count}")
    print(f"  Failed batches:  {len(failed_batches)}")
    if failed_batches:
        print(f"  Failed batch indices: {failed_batches}")
    print(f"\nDownload '{OUTPUT_FILE}' and bring it back.")

if __name__ == "__main__":
    main()
