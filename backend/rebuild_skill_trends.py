"""
Rebuild the skill_trends table from scratch using real IT skills
extracted from the cleaned jobs in the database.

Run: python rebuild_skill_trends.py
"""
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import create_app, db
from app.models import Job, SkillTrend, City

# ── Canonical IT skills whitelist ──────────────────────────────────────
# Each entry: (canonical_name, [regex patterns to match in title/desc])
IT_SKILLS = [
    # Programming Languages
    ("python", [r"\bpython\b"]),
    ("java", [r"\bjava\b(?!\s*script)"]),
    ("javascript", [r"\bjavascript\b", r"\bjs\b"]),
    ("typescript", [r"\btypescript\b", r"\bts\b"]),
    ("c++", [r"\bc\+\+\b", r"\bcpp\b"]),
    ("c#", [r"\bc#\b", r"\bc sharp\b", r"\bcsharp\b"]),
    ("golang", [r"\bgolang\b", r"\bgo lang\b"]),
    ("rust", [r"\brust\b"]),
    ("ruby", [r"\bruby\b"]),
    ("php", [r"\bphp\b"]),
    ("swift", [r"\bswift\b"]),
    ("kotlin", [r"\bkotlin\b"]),
    ("scala", [r"\bscala\b"]),
    ("perl", [r"\bperl\b"]),
    ("r programming", [r"\br programming\b", r"\br language\b"]),
    ("shell scripting", [r"\bshell\b", r"\bbash\b", r"\bpowershell\b"]),
    ("sql", [r"\bsql\b(?!\s*server)", r"\bplsql\b", r"\bpl.sql\b", r"\btsql\b"]),

    # Frontend Frameworks
    ("react", [r"\breact\b", r"\breactjs\b", r"\breact.js\b"]),
    ("angular", [r"\bangular\b", r"\bangularjs\b"]),
    ("vue.js", [r"\bvue\b", r"\bvuejs\b", r"\bvue.js\b"]),
    ("next.js", [r"\bnextjs\b", r"\bnext.js\b", r"\bnext js\b"]),
    ("svelte", [r"\bsvelte\b"]),
    ("html/css", [r"\bhtml\b", r"\bcss\b"]),
    ("tailwind", [r"\btailwind\b"]),
    ("bootstrap", [r"\bbootstrap\b"]),
    ("sass/scss", [r"\bsass\b", r"\bscss\b"]),

    # Backend Frameworks
    ("node.js", [r"\bnode\s?js\b", r"\bnode\.js\b", r"\bnodejs\b"]),
    ("django", [r"\bdjango\b"]),
    ("flask", [r"\bflask\b"]),
    ("spring boot", [r"\bspring\s?boot\b", r"\bspring\b"]),
    (".net", [r"\b\.net\b", r"\bdotnet\b", r"\bdot net\b", r"\basp\.net\b", r"\basp net\b"]),
    ("express.js", [r"\bexpress\b", r"\bexpressjs\b"]),
    ("fastapi", [r"\bfastapi\b"]),
    ("laravel", [r"\blaravel\b"]),
    ("rails", [r"\brails\b", r"\bruby on rails\b"]),

    # Cloud Platforms
    ("aws", [r"\baws\b", r"\bamazon web services\b"]),
    ("azure", [r"\bazure\b"]),
    ("gcp", [r"\bgcp\b", r"\bgoogle cloud\b"]),
    ("cloud computing", [r"\bcloud\b(?!.*engineer)"]),

    # DevOps & Infrastructure
    ("docker", [r"\bdocker\b"]),
    ("kubernetes", [r"\bkubernetes\b", r"\bk8s\b"]),
    ("terraform", [r"\bterraform\b"]),
    ("ansible", [r"\bansible\b"]),
    ("jenkins", [r"\bjenkins\b"]),
    ("ci/cd", [r"\bci.?cd\b", r"\bcontinuous integration\b", r"\bcontinuous delivery\b"]),
    ("git", [r"\bgit\b(?!hub)", r"\bgitlab\b", r"\bgithub\b", r"\bbitbucket\b"]),
    ("linux", [r"\blinux\b", r"\bubuntu\b", r"\bcentos\b", r"\bred hat\b"]),
    ("nginx", [r"\bnginx\b"]),
    ("devops", [r"\bdevops\b"]),

    # Databases
    ("mysql", [r"\bmysql\b"]),
    ("postgresql", [r"\bpostgresql\b", r"\bpostgres\b"]),
    ("mongodb", [r"\bmongodb\b", r"\bmongo\b"]),
    ("redis", [r"\bredis\b"]),
    ("elasticsearch", [r"\belasticsearch\b", r"\belastic\b"]),
    ("oracle db", [r"\boracle\b(?!.*apps)(?!.*fusion)(?!.*ebs)"]),
    ("sql server", [r"\bsql server\b", r"\bmssql\b"]),
    ("dynamodb", [r"\bdynamodb\b"]),
    ("cassandra", [r"\bcassandra\b"]),
    ("neo4j", [r"\bneo4j\b"]),

    # Data & Analytics
    ("machine learning", [r"\bmachine learning\b", r"\bml\b"]),
    ("deep learning", [r"\bdeep learning\b"]),
    ("data science", [r"\bdata scien\b"]),
    ("data engineering", [r"\bdata engineer\b"]),
    ("data analysis", [r"\bdata analy\b"]),
    ("artificial intelligence", [r"\bartificial intellig\b", r"\bai\b"]),
    ("nlp", [r"\bnlp\b", r"\bnatural language\b"]),
    ("computer vision", [r"\bcomputer vision\b", r"\bcv\b"]),
    ("tensorflow", [r"\btensorflow\b"]),
    ("pytorch", [r"\bpytorch\b"]),
    ("pandas", [r"\bpandas\b"]),
    ("numpy", [r"\bnumpy\b"]),
    ("spark", [r"\bspark\b", r"\bpyspark\b"]),
    ("hadoop", [r"\bhadoop\b"]),
    ("kafka", [r"\bkafka\b"]),
    ("tableau", [r"\btableau\b"]),
    ("power bi", [r"\bpower bi\b", r"\bpowerbi\b"]),
    ("etl", [r"\betl\b"]),
    ("snowflake", [r"\bsnowflake\b"]),
    ("databricks", [r"\bdatabricks\b"]),
    ("airflow", [r"\bairflow\b"]),
    ("generative ai", [r"\bgenerat.{0,4}\bai\b", r"\bllm\b", r"\bgpt\b", r"\blangchain\b"]),

    # Cybersecurity
    ("cybersecurity", [r"\bcyber\s?security\b", r"\binfosec\b", r"\binformation security\b"]),
    ("penetration testing", [r"\bpenetration test\b", r"\bpentest\b", r"\bethical hack\b"]),
    ("network security", [r"\bnetwork security\b", r"\bfirewall\b"]),
    ("siem", [r"\bsiem\b", r"\bsplunk\b", r"\bqradar\b"]),
    ("encryption", [r"\bencryption\b", r"\bcryptograph\b"]),
    ("vulnerability assessment", [r"\bvulnerability\b"]),
    ("soc", [r"\bsoc analyst\b", r"\bsecurity operations\b"]),

    # Enterprise / ERP
    ("sap", [r"\bsap\b"]),
    ("salesforce", [r"\bsalesforce\b"]),
    ("servicenow", [r"\bservicenow\b"]),
    ("workday", [r"\bworkday\b"]),
    ("dynamics 365", [r"\bdynamics\s?365\b"]),

    # Mobile
    ("android", [r"\bandroid\b"]),
    ("ios", [r"\bios\b"]),
    ("react native", [r"\breact native\b"]),
    ("flutter", [r"\bflutter\b"]),

    # Automation / RPA
    ("rpa", [r"\brpa\b", r"\buipath\b", r"\bautomation anywhere\b", r"\bblue prism\b"]),

    # Api / Architecture
    ("rest api", [r"\brest\s?api\b", r"\brestful\b"]),
    ("graphql", [r"\bgraphql\b"]),
    ("microservices", [r"\bmicroservice\b"]),

    # Testing
    ("selenium", [r"\bselenium\b"]),
    ("jira", [r"\bjira\b"]),
    ("agile/scrum", [r"\bagile\b", r"\bscrum\b"]),

    # Embedded / IoT
    ("embedded systems", [r"\bembedded\b", r"\bfirmware\b"]),
    ("iot", [r"\biot\b", r"\binternet of things\b"]),
    ("fpga", [r"\bfpga\b"]),
    ("vlsi", [r"\bvlsi\b"]),

    # Blockchain
    ("blockchain", [r"\bblockchain\b", r"\bweb3\b", r"\bsolidity\b"]),

    # SAS / BI
    ("sas", [r"\bsas\b"]),
    ("business intelligence", [r"\bbusiness intelligence\b", r"\bbi\b"]),

    # Networking
    ("networking", [r"\bnetwork engineer\b", r"\bnetworking\b", r"\bcisco\b", r"\bccna\b", r"\bccnp\b"]),

    # Mainframe
    ("mainframe", [r"\bmainframe\b", r"\bcobol\b"]),
]

# Pre-compile regexes
_SKILL_PATTERNS: list[tuple[str, list[re.Pattern]]] = [
    (name, [re.compile(p, re.IGNORECASE) for p in patterns])
    for name, patterns in IT_SKILLS
]


def extract_skills(text: str) -> set[str]:
    """Extract canonical IT skill names from text."""
    found = set()
    for skill_name, patterns in _SKILL_PATTERNS:
        for pat in patterns:
            if pat.search(text):
                found.add(skill_name)
                break
    return found


def rebuild():
    app = create_app()
    with app.app_context():
        # ── Clear existing skill_trends ──
        old_count = db.session.query(SkillTrend).count()
        print(f"Deleting {old_count} old skill_trends rows...")
        db.session.query(SkillTrend).delete()
        db.session.commit()

        # ── Get all jobs with dates ──
        print("Loading jobs from database...")
        jobs = (
            db.session.query(Job.title_norm, Job.description, Job.posted_date, Job.city_id)
            .filter(Job.posted_date.isnot(None))
            .all()
        )
        print(f"  → {len(jobs)} jobs with dates loaded")

        # ── Extract skills per (month, city) ──
        # Structure: {(skill, city_id, period): demand_count}
        skill_demand: dict[tuple[str, int | None, date], int] = defaultdict(int)

        for i, (title_norm, desc, posted_date, city_id) in enumerate(jobs):
            # Combine title and description for skill detection
            text = (title_norm or "") + " " + (desc or "")
            skills = extract_skills(text)
            # Round date to first-of-month
            period = posted_date.replace(day=1)
            for skill in skills:
                skill_demand[(skill, city_id, period)] += 1

            if (i + 1) % 10000 == 0:
                print(f"  ... processed {i+1}/{len(jobs)} jobs")

        print(f"  → {len(skill_demand)} skill-city-period combinations found")

        # ── Compute change_pct between periods ──
        # Group by (skill, city_id) across periods
        skill_by_period: dict[tuple[str, int | None], dict[date, int]] = defaultdict(dict)
        for (skill, city_id, period), demand in skill_demand.items():
            skill_by_period[(skill, city_id)][period] = demand

        # Get sorted unique periods
        all_periods = sorted(set(p for _, _, p in skill_demand.keys()))
        period_index = {p: i for i, p in enumerate(all_periods)}

        # ── Insert into database ──
        print("Inserting new skill_trends...")
        insert_count = 0
        for (skill, city_id), periods in skill_by_period.items():
            for period, demand in periods.items():
                # Find previous period's demand for change_pct
                idx = period_index[period]
                prev_demand = 0
                if idx > 0:
                    prev_period = all_periods[idx - 1]
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

                if insert_count % 10000 == 0:
                    db.session.flush()
                    print(f"  ... inserted {insert_count} rows")

        db.session.commit()
        print(f"\n✓ Rebuilt skill_trends: {insert_count} rows")

        # ── Show top skills ──
        print("\nTop 30 skills by total demand:")
        top = (
            db.session.query(
                SkillTrend.skill_name,
                db.func.sum(SkillTrend.demand_count).label("total"),
            )
            .group_by(SkillTrend.skill_name)
            .order_by(db.func.sum(SkillTrend.demand_count).desc())
            .limit(30)
            .all()
        )
        for skill, total in top:
            print(f"  {total:>8}  {skill}")


if __name__ == "__main__":
    rebuild()
