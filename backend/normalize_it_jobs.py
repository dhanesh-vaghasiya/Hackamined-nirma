"""
Utility to filter job titles — keeps only IT / tech-related roles.
Used by seed_database.py to filter non-IT jobs during seeding.
"""
from __future__ import annotations

import re

# Keywords that indicate an IT / tech job
_IT_KEYWORDS = {
    # Core tech roles
    "software", "developer", "engineer", "programmer", "coding",
    "frontend", "backend", "fullstack", "full stack", "full-stack",
    "devops", "sre", "site reliability",
    # Data & AI
    "data", "machine learning", "ml", "deep learning", "ai ",
    "artificial intelligence", "nlp", "computer vision",
    "data scientist", "data analyst", "data engineer",
    "analytics", "business intelligence", "bi ",
    # Web & mobile
    "web", "mobile", "android", "ios", "react", "angular", "vue",
    "node", "django", "flask", "spring", "laravel",
    # Cloud & infra
    "cloud", "aws", "azure", "gcp", "kubernetes", "docker",
    "infrastructure", "platform", "sysadmin", "system admin",
    "network", "linux", "unix",
    # Security
    "security", "cybersecurity", "cyber security", "infosec",
    "penetration", "ethical hacking", "soc ",
    # Database
    "database", "dba", "sql", "mongodb", "postgres", "mysql",
    "oracle", "redis",
    # QA & testing
    "qa", "quality assurance", "test", "automation test",
    "selenium", "manual testing",
    # Design & product
    "ui", "ux", "ui/ux", "product", "scrum", "agile",
    "project manager",
    # IT general
    "it ", "information technology", "technical", "tech lead",
    "architect", "consultant", "support engineer",
    "helpdesk", "help desk", "service desk",
    # Languages / frameworks as titles
    "java", "python", "javascript", ".net", "dotnet", "c++",
    "golang", "rust", "scala", "ruby", "php", "swift", "kotlin",
    "typescript", "salesforce", "sap", "erp",
    # Embedded & hardware-adjacent
    "embedded", "firmware", "iot", "robotics", "vlsi", "fpga",
    # Telecom & electronics (IT-adjacent)
    "telecom", "wireless",
    # Broad catches
    "computing", "cyber", "blockchain", "crypto",
    "api", "microservice",
}

# Titles that should always be excluded even if they match a keyword
_EXCLUDE = {
    "security guard", "security officer", "physical security",
    "network marketing", "product sales",
}


def is_it_job(title_norm: str) -> bool:
    """Return True if the normalised (lower-case) title looks like an IT job."""
    if not title_norm:
        return False
    t = title_norm.strip().lower()
    # Check exclusions first
    for ex in _EXCLUDE:
        if ex in t:
            return False
    # Check for any IT keyword
    for kw in _IT_KEYWORDS:
        if kw in t:
            return True
    return False