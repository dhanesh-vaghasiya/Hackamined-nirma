MODEL_NAME = "all-MiniLM-L6-v2"
SKILL_SIMILARITY_THRESHOLD = 0.5

TASK_KEYWORDS = [
    "manage",
    "handle",
    "train",
    "analyze",
    "monitor",
    "support",
    "coordinate",
    "lead",
]

ASPIRATION_PATTERNS = [
    "want to move into",
    "interested in",
    "looking to transition",
    "looking to transition into",
    "want to learn",
    "want to work in",
]

JOB_TITLE_MAPPING = {
    "senior executive bpo": "BPO Team Lead",
    "call center supervisor": "BPO Team Lead",
    "voice process lead": "BPO Team Lead",
}

DOMAIN_KEYWORDS = {
    "customer support": [
        "customer",
        "support",
        "call center",
        "complaint",
        "voice support",
        "crm",
    ],
    "analytics": ["analytics", "data", "dashboard", "reporting", "sql"],
    "sales": ["sales", "lead generation", "pipeline", "revenue"],
    "marketing": ["marketing", "campaign", "seo", "content"],
}
