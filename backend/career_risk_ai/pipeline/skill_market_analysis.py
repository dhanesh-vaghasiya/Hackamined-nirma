from __future__ import annotations

import json
import math
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import pandas as pd
import requests

from paths import json_path, resolve_csv_input


SKILL_SPLIT_RE = re.compile(r"[,/|;]\s*")


@dataclass
class GroqConfig:
    api_key: str
    model: str = "llama-3.3-70b-versatile"
    timeout_seconds: int = 90


def _extract_skills(text: str) -> List[str]:
    value = str(text or "").strip()
    if not value:
        return []

    lowered = value.lower()
    marker = "required skills:"
    if marker in lowered:
        idx = lowered.find(marker)
        value = value[idx + len(marker):]

    skills = []
    for token in SKILL_SPLIT_RE.split(value):
        candidate = re.sub(r"\s+", " ", token.strip().lower())
        if not candidate:
            continue
        if len(candidate) > 40:
            continue
        if candidate in {"n/a", "nan", "none"}:
            continue
        skills.append(candidate)

    # Unique order
    seen = set()
    out = []
    for s in skills:
        if s not in seen:
            out.append(s)
            seen.add(s)
    return out[:20]


def _build_skill_monthly_demand(jobs_df: pd.DataFrame) -> pd.DataFrame:
    base = jobs_df.copy()
    base["posted_date"] = pd.to_datetime(base["posted_date"], errors="coerce")
    base = base.dropna(subset=["posted_date", "description"])
    base = base[base["posted_date"] >= pd.Timestamp("2020-01-01")]
    base["month"] = base["posted_date"].dt.to_period("M").astype(str)

    base["skills"] = base["description"].fillna("").astype(str).apply(_extract_skills)
    exploded = base.explode("skills")
    exploded = exploded.dropna(subset=["skills"])
    exploded = exploded[exploded["skills"].astype(str).str.len() > 0]

    demand = (
        exploded.groupby(["skills", "month"], as_index=False)
        .size()
        .rename(columns={"size": "demand"})
        .sort_values(["skills", "month"])
    )
    return demand


def _compute_skill_stats(skill_df: pd.DataFrame) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []

    for skill, part in skill_df.groupby("skills"):
        ordered = part.sort_values("month")
        first_month = str(ordered.iloc[0]["month"])
        latest_month = str(ordered.iloc[-1]["month"])
        first_demand = float(ordered.iloc[0]["demand"])
        latest_demand = float(ordered.iloc[-1]["demand"])
        total_demand = float(ordered["demand"].sum())

        if first_demand > 0:
            pct_change = ((latest_demand - first_demand) / first_demand) * 100.0
        else:
            pct_change = 100.0 if latest_demand > 0 else 0.0

        if pct_change > 5:
            direction = "increasing"
        elif pct_change < -5:
            direction = "decreasing"
        else:
            direction = "stable"

        rows.append(
            {
                "skill": str(skill),
                "first_month": first_month,
                "latest_month": latest_month,
                "first_demand": int(first_demand),
                "latest_demand": int(latest_demand),
                "total_demand": int(total_demand),
                "percent_change": round(float(pct_change), 2),
                "market_direction": direction,
            }
        )

    return rows


def _prompt_batch(skills_batch: List[Dict[str, object]]) -> str:
    return (
        "You are given skill demand trend stats from 2020 to current date. "
        "Return ONLY valid JSON with key 'items' where each item has: "
        "skill, market_summary (max 20 words), confidence (0-1). "
        "Do not change percent values.\n"
        f"Input: {json.dumps(skills_batch, ensure_ascii=True)}"
    )


def _groq_enrich_batch(batch: List[Dict[str, object]], cfg: GroqConfig) -> Dict[str, Dict[str, object]]:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": cfg.model,
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "Respond strictly in JSON."},
            {"role": "user", "content": _prompt_batch(batch)},
        ],
    }

    response = requests.post(url, headers=headers, json=payload, timeout=cfg.timeout_seconds)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    parsed = json.loads(content)

    out: Dict[str, Dict[str, object]] = {}
    for item in parsed.get("items", []):
        skill = str(item.get("skill", "")).strip().lower()
        if not skill:
            continue
        out[skill] = {
            "market_summary": str(item.get("market_summary", "")).strip()[:240],
            "confidence": max(0.0, min(1.0, float(item.get("confidence", 0.5)))),
        }

    return out


def build_skill_market_json(
    jobs_csv_path: str | None = None,
    output_json_path: str | None = None,
    batch_size: int = 5000,
    sleep_between_calls: float = 0.15,
) -> Dict[str, object]:
    jobs_path = Path(jobs_csv_path) if jobs_csv_path else resolve_csv_input("jobs.csv")
    out_path = Path(output_json_path) if output_json_path else json_path("skill_market_2020_present.json")

    if not jobs_path.exists():
        raise RuntimeError(f"jobs.csv not found: {jobs_path}")

    jobs_df = pd.read_csv(jobs_path)
    demand_df = _build_skill_monthly_demand(jobs_df)
    stats = _compute_skill_stats(demand_df)

    checkpoint_path = out_path.with_suffix(".checkpoint.json")

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    use_groq = bool(api_key)
    cfg = GroqConfig(api_key=api_key) if use_groq else None

    enriched_map: Dict[str, Dict[str, object]] = {}
    failures: List[Dict[str, str]] = []

    # Resume support: load already-enriched skills from checkpoint.
    if checkpoint_path.exists():
        try:
            checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            for item in checkpoint.get("items", []):
                skill = str(item.get("skill", "")).strip().lower()
                if skill:
                    enriched_map[skill] = {
                        "market_summary": str(item.get("market_summary", "")).strip(),
                        "confidence": item.get("groq_confidence", 0.5) if item.get("groq_confidence") is not None else 0.5,
                    }
        except Exception:
            pass

    if use_groq and stats:
        remaining = [row for row in stats if row["skill"].lower() not in enriched_map]
        total_batches = int(math.ceil(len(stats) / max(batch_size, 1)))
        total_batches = int(math.ceil(len(remaining) / max(batch_size, 1))) if remaining else 0
        for i in range(total_batches):
            start = i * batch_size
            end = min(len(remaining), start + batch_size)
            chunk = remaining[start:end]
            print(f"Groq enrich batch {i + 1}/{total_batches} ({start + 1}-{end})")

            try:
                enriched = None
                last_err = None
                for attempt in range(3):
                    try:
                        enriched = _groq_enrich_batch(chunk, cfg)
                        break
                    except Exception as exc:
                        last_err = exc
                        time.sleep(1.2 * (attempt + 1))
                if enriched is None:
                    raise RuntimeError(str(last_err) if last_err else "Groq enrich failed")
                enriched_map.update(enriched)

                # Checkpoint after each successful batch.
                checkpoint_payload = {
                    "generated_at": pd.Timestamp.utcnow().isoformat(),
                    "items": [
                        {
                            **row,
                            "market_summary": enriched_map.get(row["skill"].lower(), {}).get("market_summary", ""),
                            "groq_confidence": enriched_map.get(row["skill"].lower(), {}).get("confidence", None),
                        }
                        for row in stats
                    ],
                }
                checkpoint_path.write_text(json.dumps(checkpoint_payload, indent=2), encoding="utf-8")
            except Exception as exc:
                for row in chunk:
                    failures.append({"skill": row["skill"], "error": str(exc)})
            time.sleep(sleep_between_calls)

    result_items = []
    for row in stats:
        skill_key = row["skill"].lower()
        extra = enriched_map.get(skill_key, {})
        result_items.append(
            {
                **row,
                "market_summary": extra.get("market_summary", ""),
                "groq_confidence": extra.get("confidence", None),
            }
        )

    payload = {
        "generated_at": pd.Timestamp.utcnow().isoformat(),
        "source": {
            "jobs_csv": str(jobs_path),
            "start_date": "2020-01-01",
        },
        "groq_used": use_groq,
        "model": cfg.model if cfg else None,
        "skill_count": len(result_items),
        "items": result_items,
        "failures": failures[:200],
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Final payload supersedes checkpoint.
    if checkpoint_path.exists():
        checkpoint_path.unlink(missing_ok=True)

    return {
        "output_json": str(out_path),
        "skill_count": len(result_items),
        "groq_used": use_groq,
        "failed_enrichment": len(failures),
    }


if __name__ == "__main__":
    info = build_skill_market_json()
    print(json.dumps(info, indent=2))
