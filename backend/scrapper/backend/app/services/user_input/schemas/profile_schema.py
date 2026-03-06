REQUIRED_FIELDS = ["job_title", "city", "experience", "writeup"]


def validate_profile_input(data):
    if not isinstance(data, dict):
        return False, ["Request body must be a JSON object"]

    errors = []
    for field in REQUIRED_FIELDS:
        value = data.get(field)
        if value is None:
            errors.append(f"Missing required field: {field}")
            continue
        if isinstance(value, str) and not value.strip():
            errors.append(f"Field cannot be empty: {field}")

    writeup = data.get("writeup", "")
    if isinstance(writeup, str) and writeup.strip() and len(writeup.split()) < 20:
        errors.append(
            "Write-up is too short. Please provide more detail (ideally 100-200 words)."
        )

    return len(errors) == 0, errors


def normalize_experience(experience):
    try:
        return int(experience)
    except (TypeError, ValueError):
        return 0
