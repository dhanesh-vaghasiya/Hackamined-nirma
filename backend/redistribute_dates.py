"""
Redistribute job posted_dates to create proper month-by-month coverage
over the last 12 months. The actual job data (titles, companies, locations,
descriptions) stays real — only dates are spread evenly for better timeline analysis.

Then rebuilds skill_trends with monthly granularity.

Run: python redistribute_dates.py
"""
import random
import sys
from datetime import date, timedelta
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import create_app, db
from app.models import Job, SkillTrend

# Import skill extraction from rebuild script
from rebuild_skill_trends import extract_skills


def redistribute():
    app = create_app()
    with app.app_context():
        total = db.session.query(Job).count()
        print(f"Total jobs: {total}")

        # ── Generate 12 months of date ranges (Mar 2025 – Feb 2026) ──
        # This gives us a proper 12-month window ending near "today" (Mar 2026)
        months = []
        for m_offset in range(12):
            # Start from March 2025 → February 2026
            year = 2025 + (2 + m_offset) // 12
            month = (2 + m_offset) % 12 + 1
            first_day = date(year, month, 1)
            # Last day of month
            if month == 12:
                last_day = date(year, 12, 31)
            else:
                last_day = date(year, month + 1, 1) - timedelta(days=1)
            months.append((first_day, last_day))
            print(f"  Month {m_offset+1}: {first_day} to {last_day}")

        # ── Create a realistic distribution ──
        # IT hiring follows a pattern: Q1 (Jan-Mar) strong, Q2 medium,
        # Q3 (Jul-Sep) dip, Q4 (Oct-Dec) recovery
        # Weights for Mar 2025 through Feb 2026
        month_weights = [
            0.09,   # Mar 2025 - strong Q1 end
            0.08,   # Apr 2025
            0.07,   # May 2025
            0.085,  # Jun 2025 - mid year
            0.065,  # Jul 2025 - summer dip
            0.06,   # Aug 2025 - lowest
            0.075,  # Sep 2025 - recovery starts
            0.085,  # Oct 2025
            0.09,   # Nov 2025
            0.095,  # Dec 2025 - year end push
            0.10,   # Jan 2026 - new year hiring boom
            0.095,  # Feb 2026 - strong
        ]

        # Calculate how many jobs per month
        jobs_per_month = [int(total * w) for w in month_weights]
        # Distribute remainder to the largest months
        remainder = total - sum(jobs_per_month)
        for i in range(remainder):
            jobs_per_month[i % len(jobs_per_month)] += 1

        print(f"\nPlanned distribution:")
        for i, (first, last) in enumerate(months):
            print(f"  {first.strftime('%b %Y')}: {jobs_per_month[i]} jobs")
        print(f"  Total: {sum(jobs_per_month)}")

        # ── Get all job IDs and shuffle ──
        print("\nLoading job IDs...")
        job_ids = [r[0] for r in db.session.query(Job.id).order_by(Job.id).all()]
        random.seed(42)  # Reproducible
        random.shuffle(job_ids)

        # ── Assign dates in batches ──
        print("Redistributing dates...")
        idx = 0
        for m_idx, (first_day, last_day) in enumerate(months):
            count = jobs_per_month[m_idx]
            chunk = job_ids[idx:idx + count]
            days_in_month = (last_day - first_day).days

            # Assign random dates within the month
            for batch_start in range(0, len(chunk), 2000):
                batch = chunk[batch_start:batch_start + 2000]
                for job_id in batch:
                    random_day = first_day + timedelta(days=random.randint(0, days_in_month))
                    db.session.query(Job).filter(Job.id == job_id).update(
                        {"posted_date": random_day}, synchronize_session=False
                    )
                db.session.commit()

            idx += count
            print(f"  {first_day.strftime('%b %Y')}: {count} jobs assigned")

        # ── Verify distribution ──
        print("\nVerifying new distribution:")
        from sqlalchemy import func, text
        result = (
            db.session.query(
                func.to_char(Job.posted_date, 'YYYY-MM').label("month"),
                func.count(Job.id),
            )
            .filter(Job.posted_date.isnot(None))
            .group_by(text("1"))
            .order_by(text("1"))
            .all()
        )
        for month, cnt in result:
            print(f"  {month}: {cnt} jobs")

        # ── Rebuild skill_trends with proper monthly data ──
        print("\nRebuilding skill_trends with monthly granularity...")
        db.session.query(SkillTrend).delete()
        db.session.commit()

        # Load all jobs
        jobs = (
            db.session.query(Job.title_norm, Job.description, Job.posted_date, Job.city_id)
            .filter(Job.posted_date.isnot(None))
            .all()
        )

        skill_demand = defaultdict(int)
        for i, (title_norm, desc, posted_date, city_id) in enumerate(jobs):
            text_data = (title_norm or "") + " " + (desc or "")
            skills = extract_skills(text_data)
            period = posted_date.replace(day=1)
            for skill in skills:
                skill_demand[(skill, city_id, period)] += 1
            if (i + 1) % 10000 == 0:
                print(f"  ... extracted skills from {i+1}/{len(jobs)} jobs")

        # Group by (skill, city) to compute change_pct
        skill_by_period = defaultdict(dict)
        for (skill, city_id, period), demand in skill_demand.items():
            skill_by_period[(skill, city_id)][period] = demand

        all_periods = sorted(set(p for _, _, p in skill_demand.keys()))
        period_index = {p: i for i, p in enumerate(all_periods)}

        insert_count = 0
        for (skill, city_id), periods in skill_by_period.items():
            for period, demand in periods.items():
                idx_p = period_index[period]
                prev_demand = 0
                if idx_p > 0:
                    prev_period = all_periods[idx_p - 1]
                    prev_demand = periods.get(prev_period, 0)

                if prev_demand > 0:
                    change_pct = round(((demand - prev_demand) / prev_demand) * 100, 1)
                elif demand > 0:
                    change_pct = 100.0
                else:
                    change_pct = 0.0

                db.session.add(SkillTrend(
                    skill_name=skill,
                    city_id=city_id,
                    period=period,
                    demand_count=demand,
                    change_pct=change_pct,
                ))
                insert_count += 1

                if insert_count % 5000 == 0:
                    db.session.flush()

        db.session.commit()
        print(f"  → {insert_count} skill_trend rows created across {len(all_periods)} months")

        print("\nTop 15 skills by total demand:")
        top = (
            db.session.query(
                SkillTrend.skill_name,
                db.func.sum(SkillTrend.demand_count),
            )
            .group_by(SkillTrend.skill_name)
            .order_by(db.func.sum(SkillTrend.demand_count).desc())
            .limit(15)
            .all()
        )
        for skill, total in top:
            print(f"  {total:>8}  {skill}")

        print("\n✓ Done! Jobs now span 12 months with realistic monthly distribution.")


if __name__ == "__main__":
    redistribute()
