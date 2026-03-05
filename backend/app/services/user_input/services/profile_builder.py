from app.services.user_input.config import DOMAIN_KEYWORDS, JOB_TITLE_MAPPING
from app.services.user_input.schemas.profile_schema import (
    normalize_experience,
    validate_profile_input,
)
from app.services.user_input.services.preprocessing import preprocess_text
from app.services.user_input.services.skill_extractor import extract_skills, extract_tools
from app.services.user_input.services.task_extractor import extract_tasks
from app.services.user_input.services.aspiration_detector import detect_aspirations


def _normalize_job_title(job_title):
    if not isinstance(job_title, str):
        return "Unknown"
    normalized = JOB_TITLE_MAPPING.get(job_title.strip().lower())
    return normalized if normalized else job_title.strip().title()


def _infer_domain(cleaned_text, skills, tasks):
    combined_text = " ".join([cleaned_text] + skills + tasks)
    best_domain = "general operations"
    best_score = 0

    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in combined_text)
        if score > best_score:
            best_score = score
            best_domain = domain

    return best_domain


def build_profile(data):
    is_valid, errors = validate_profile_input(data)
    if not is_valid:
        raise ValueError("; ".join(errors))

    writeup = data.get("writeup", "")
    preprocessed = preprocess_text(writeup)
    cleaned_text = preprocessed["cleaned_text"]

    skills = extract_skills(cleaned_text)
    tools = extract_tools(cleaned_text)
    tasks = extract_tasks(cleaned_text)
    aspirations = detect_aspirations(writeup)
    domain = _infer_domain(cleaned_text, skills, tasks)

    profile = {
        "normalized_job_title": _normalize_job_title(data.get("job_title", "")),
        "city": data.get("city", ""),
        "experience_years": normalize_experience(data.get("experience")),
        "skills": skills,
        "tools": tools,
        "tasks": tasks,
        "aspirations": aspirations,
        "domain": domain,
    }

    return profile
