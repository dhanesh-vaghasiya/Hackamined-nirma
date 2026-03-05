from app.services.user_input.config import TASK_KEYWORDS


STOP_TOKENS = {
    "and",
    "or",
    "but",
    "i",
    "we",
    "they",
    "want",
    "interested",
    "looking",
}


def _unique_preserve_order(items):
    seen = set()
    ordered = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _normalize_task_phrase(phrase):
    if "customer complaint" in phrase:
        return "customer complaint resolution"
    if phrase.startswith("train") and "agent" in phrase:
        return "agent training"
    if phrase.startswith("manage") and ("team" in phrase or "voice support" in phrase):
        return "team supervision"
    return phrase


def extract_tasks(cleaned_text):
    if not cleaned_text:
        return []

    tokens = cleaned_text.split()
    phrases = []

    for index, token in enumerate(tokens):
        if token not in TASK_KEYWORDS:
            continue

        if token == "support":
            previous_token = tokens[index - 1] if index > 0 else ""
            next_token = tokens[index + 1] if index + 1 < len(tokens) else ""
            if previous_token in {"voice", "customer"} and next_token in {"team", "teams"}:
                continue

        phrase_tokens = [token]
        for offset in range(1, 6):
            next_index = index + offset
            if next_index >= len(tokens):
                break
            next_token = tokens[next_index]
            if next_token in STOP_TOKENS:
                break
            if next_token in TASK_KEYWORDS and not (token == "manage" and next_token == "support"):
                break
            phrase_tokens.append(next_token)

        phrase = " ".join(phrase_tokens).strip()
        phrases.append(_normalize_task_phrase(phrase))

    return _unique_preserve_order(phrases)
