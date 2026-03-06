from app.services.user_input.models.skill_model import semantic_skill_model
from app.services.user_input.utils.skill_dictionary import SKILLS, TOOLS


def _unique_preserve_order(items):
    seen = set()
    ordered = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def extract_skills(cleaned_text):
    if not cleaned_text:
        return []

    dictionary_skills = [skill for skill in SKILLS if skill in cleaned_text]
    semantic_skills = semantic_skill_model.extract_semantic_skills(cleaned_text, SKILLS)

    return _unique_preserve_order(dictionary_skills + semantic_skills)


def extract_tools(cleaned_text):
    if not cleaned_text:
        return []

    found_tools = [tool.upper() if tool == "crm" else tool for tool in TOOLS if tool in cleaned_text]
    return _unique_preserve_order(found_tools)
