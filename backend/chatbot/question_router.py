def detect_question_type(question):

    q = question.lower()

    if "risk" in q:
        return "risk"

    if "safer" in q or "safe job" in q:
        return "safe_jobs"

    if "3 months" in q:
        return "career_path"

    if "how many" in q:
        return "job_count"

    return "general"    