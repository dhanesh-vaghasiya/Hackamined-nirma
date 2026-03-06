"""
Scraper Soak / Endurance Test
─────────────────────────────
Sends scrape requests at a regular interval (default every 5 min)
and records response time, success/failure, jobs added, and store
growth over many iterations.

Usage:
    python -m tests.scraper_soak_test                         # defaults
    python -m tests.scraper_soak_test --rounds 20 --interval 300
    python -m tests.scraper_soak_test --rounds 10 --interval 60 --url http://localhost:5000

Results are printed live and saved to  tests/soak_results.csv
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime, timedelta

import requests

# ── defaults ────────────────────────────────────────────────
DEFAULT_BASE_URL = "http://localhost:5000"
DEFAULT_ROUNDS = 12          # total scrape requests to fire
DEFAULT_INTERVAL = 300       # seconds between requests (5 min)
REQUEST_TIMEOUT = 180        # max wait per scrape request (3 min)

# keyword sets rotated across rounds to simulate varied usage
KEYWORD_SETS = [
    ["developer"],
    ["analyst"],
    ["engineer"],
    ["designer"],
    ["manager"],
    ["developer", "analyst"],
    ["engineer", "designer"],
    ["developer", "engineer", "manager"],
]

RESULTS_FILE = os.path.join(os.path.dirname(__file__), "soak_results.csv")

# ── helpers ─────────────────────────────────────────────────

def _banner(msg: str) -> None:
    width = 60
    print(f"\n{'═' * width}")
    print(f"  {msg}")
    print(f"{'═' * width}\n")


def _fetch_stats(base: str) -> dict | None:
    try:
        r = requests.get(f"{base}/api/scraper/stats", timeout=10)
        if r.ok:
            return r.json().get("data", {})
    except Exception:
        pass
    return None


def _run_scrape(base: str, keywords: list[str], max_rows: int = 20) -> dict:
    """Fire one POST /api/scraper/scrape and return a summary dict."""
    payload = {"keywords": keywords, "max_rows": max_rows}
    start = time.perf_counter()
    error_msg = None
    status_code = None
    data = {}

    try:
        resp = requests.post(
            f"{base}/api/scraper/scrape",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        status_code = resp.status_code
        body = resp.json()
        if body.get("success"):
            data = body.get("data", {})
        else:
            error_msg = body.get("message", "unknown error")
    except requests.Timeout:
        error_msg = "request timed out"
    except requests.ConnectionError:
        error_msg = "connection refused – is the server running?"
    except Exception as exc:
        error_msg = str(exc)

    elapsed = time.perf_counter() - start

    return {
        "ok": error_msg is None,
        "status_code": status_code,
        "elapsed_s": round(elapsed, 2),
        "jobs_added": data.get("jobs_added", 0),
        "total_in_store": data.get("total_jobs_in_store", 0),
        "error": error_msg,
        "keywords": ", ".join(keywords),
    }


# ── main loop ──────────────────────────────────────────────

def run_soak_test(base_url: str, rounds: int, interval: int) -> None:
    _banner("Scraper Soak Test")
    print(f"  Server        : {base_url}")
    print(f"  Rounds        : {rounds}")
    print(f"  Interval      : {interval}s  ({interval / 60:.1f} min)")
    est = timedelta(seconds=interval * (rounds - 1))
    print(f"  Est. duration : {est}  (+ scrape time)")
    print()

    # check server is reachable
    stats = _fetch_stats(base_url)
    if stats is None:
        print("[ERROR] Cannot reach the server. Start it first (python run.py).")
        sys.exit(1)
    print(f"  Server online  – store has {stats.get('total_jobs', '?')} jobs, "
          f"{stats.get('total_scrape_runs', '?')} prior runs\n")

    # prepare CSV log
    csv_fields = [
        "round", "timestamp", "keywords", "status_code",
        "elapsed_s", "jobs_added", "total_in_store", "ok", "error",
    ]
    with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()

    results: list[dict] = []

    for i in range(1, rounds + 1):
        kws = KEYWORD_SETS[(i - 1) % len(KEYWORD_SETS)]
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"[Round {i}/{rounds}]  {ts}  keywords={kws}")
        result = _run_scrape(base_url, kws)
        result["round"] = i
        result["timestamp"] = ts

        tag = "OK" if result["ok"] else "FAIL"
        print(f"  -> {tag}  status={result['status_code']}  "
              f"time={result['elapsed_s']}s  "
              f"jobs_added={result['jobs_added']}  "
              f"store_total={result['total_in_store']}")
        if result["error"]:
            print(f"     error: {result['error']}")

        results.append(result)

        # append to CSV incrementally
        with open(RESULTS_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=csv_fields)
            writer.writerow({k: result.get(k, "") for k in csv_fields})

        # wait before next round (skip wait after last round)
        if i < rounds:
            print(f"  ... waiting {interval}s until next round\n")
            time.sleep(interval)

    # ── summary ─────────────────────────────────────────────
    _banner("Soak Test Summary")
    total = len(results)
    passed = sum(1 for r in results if r["ok"])
    failed = total - passed
    times = [r["elapsed_s"] for r in results if r["ok"]]
    jobs_total = sum(r["jobs_added"] for r in results)

    print(f"  Rounds       : {total}")
    print(f"  Passed       : {passed}")
    print(f"  Failed       : {failed}")
    print(f"  Total jobs   : {jobs_total}")
    if times:
        print(f"  Avg time     : {sum(times)/len(times):.2f}s")
        print(f"  Min time     : {min(times):.2f}s")
        print(f"  Max time     : {max(times):.2f}s")

    # check for degradation: compare first-half vs second-half avg times
    if len(times) >= 4:
        mid = len(times) // 2
        first_half = times[:mid]
        second_half = times[mid:]
        avg1 = sum(first_half) / len(first_half)
        avg2 = sum(second_half) / len(second_half)
        delta_pct = ((avg2 - avg1) / avg1) * 100 if avg1 > 0 else 0
        print(f"\n  Degradation check:")
        print(f"    First-half avg  : {avg1:.2f}s")
        print(f"    Second-half avg : {avg2:.2f}s")
        print(f"    Change          : {delta_pct:+.1f}%")
        if delta_pct > 30:
            print("    [WARNING] Response times degraded >30% – possible resource leak")
        else:
            print("    [OK] No significant degradation detected")

    # final store stats
    final_stats = _fetch_stats(base_url)
    if final_stats:
        print(f"\n  Final store   : {final_stats.get('total_jobs', '?')} jobs, "
              f"{final_stats.get('total_scrape_runs', '?')} total runs")

    print(f"\n  Full results  : {RESULTS_FILE}")
    print()


# ── CLI ─────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper soak / endurance test")
    parser.add_argument("--url", default=DEFAULT_BASE_URL, help="Backend base URL")
    parser.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS, help="Number of scrape requests")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help="Seconds between requests")
    args = parser.parse_args()

    run_soak_test(args.url, args.rounds, args.interval)
