import re

from app.services.user_input.config import ASPIRATION_PATTERNS


def _normalize_target(target):
    target = target.strip().lower()
    target = re.sub(
        r"^(want to move into|interested in|looking to transition(?: into)?|want to learn|want to work in)\s+",
        "",
        target,
    )
    target = re.sub(r"\b(role|roles|domain|field|career)\b", "", target).strip()
    target = re.sub(r"\s+", " ", target)
    return target


def _unique_preserve_order(items):
    seen = set()
    ordered = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def detect_aspirations(raw_text):
    if not raw_text:
        return []

    lowered = raw_text.lower()
    aspirations = []

    for phrase in ASPIRATION_PATTERNS:
        pattern = re.compile(
            rf"{re.escape(phrase)}\s+([a-z0-9 ,/&-]+?)(?:\.|,|;|$)",
            re.IGNORECASE,
        )
        for match in pattern.finditer(lowered):
            segment = match.group(1)
            parts = re.split(r"\bor\b|\band\b|,|/", segment)
            for part in parts:
                normalized = _normalize_target(part)
                if normalized:
                    aspirations.append(normalized)

    return _unique_preserve_order(aspirations)
