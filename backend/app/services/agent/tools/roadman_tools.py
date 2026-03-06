"""
Roadmap.sh API tool.
Uses me.py to fetch real roadmaps from roadmap.sh public API.
"""

import logging
import sys
import os

# Add backend root to path so we can import me.py
_backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

from me import fetch_available_roadmaps, fetch_roadmap  # noqa: E402

logger = logging.getLogger(__name__)

# ── Skill → roadmap.sh slug mapping ─────────────────────
# Maps common skill names to their roadmap.sh slugs.
# The agent can also call list_available_roadmaps() to discover slugs.
_SKILL_TO_SLUG = {
    "python": "python",
    "data analytics": "data-analyst",
    "data analyst": "data-analyst",
    "sql": "sql",
    "postgresql": "postgresql-dba",
    "cybersecurity": "cyber-security",
    "cyber security": "cyber-security",
    "machine learning": "mlops",
    "ai": "ai-data-scientist",
    "ai literacy": "ai-data-scientist",
    "data science": "ai-data-scientist",
    "prompt engineering": "prompt-engineering",
    "cloud computing": "aws",
    "aws": "aws",
    "devops": "devops",
    "docker": "docker",
    "kubernetes": "kubernetes",
    "javascript": "javascript",
    "typescript": "typescript",
    "react": "react",
    "angular": "angular",
    "vue": "vue",
    "node.js": "nodejs",
    "nodejs": "nodejs",
    "java": "java",
    "spring boot": "spring-boot",
    "golang": "golang",
    "go": "golang",
    "rust": "rust",
    "c++": "cpp",
    "frontend": "frontend",
    "backend": "backend",
    "full stack": "full-stack",
    "blockchain": "blockchain",
    "flutter": "flutter",
    "react native": "react-native",
    "android": "android",
    "ios": "ios",
    "git": "git-github",
    "github": "git-github",
    "linux": "linux",
    "mongodb": "mongodb",
    "redis": "redis",
    "graphql": "graphql",
    "system design": "system-design",
    "software architecture": "software-architect",
    "software design": "software-design-architecture",
    "api design": "api-design",
    "ux design": "ux-design",
    "product management": "product-manager",
    "technical writing": "technical-writer",
    "computer science": "computer-science",
}


def _find_slug(skill: str) -> str | None:
    """Find the roadmap.sh slug for a given skill name."""
    skill_lower = skill.lower().strip()

    # Direct match
    if skill_lower in _SKILL_TO_SLUG:
        return _SKILL_TO_SLUG[skill_lower]

    # Partial match
    for key, slug in _SKILL_TO_SLUG.items():
        if key in skill_lower or skill_lower in key:
            return slug

    # Try using the skill as a slug directly
    return skill_lower.replace(" ", "-")


def list_available_roadmaps() -> list[str]:
    """Fetch all available roadmap slugs from roadmap.sh."""
    try:
        slugs = fetch_available_roadmaps()
        return slugs
    except Exception as e:
        logger.warning("Failed to fetch available roadmaps: %s", e)
        return []


def generate_roadmap_via_api(skill: str) -> dict:
    """
    Fetch a real roadmap from roadmap.sh for a given skill.
    Returns the roadmap topics as a structured dict.
    """
    slug = _find_slug(skill)
    logger.info("Fetching roadmap for skill='%s' → slug='%s'", skill, slug)

    # Try fetching the roadmap
    topics = []
    used_slug = slug
    try:
        topics = fetch_roadmap(slug)
    except Exception as e:
        logger.warning("fetch_roadmap('%s') failed: %s", slug, e)

    # If no topics, try fetching the available list and find best match
    if not topics:
        try:
            available = fetch_available_roadmaps()
            # Try exact match first
            if slug in available:
                topics = fetch_roadmap(slug)
            else:
                # Fuzzy match: find slug containing the skill keyword
                skill_lower = skill.lower().replace(" ", "-")
                for avail_slug in available:
                    if skill_lower in avail_slug or avail_slug in skill_lower:
                        topics = fetch_roadmap(avail_slug)
                        used_slug = avail_slug
                        break
        except Exception as e:
            logger.warning("Fallback roadmap fetch failed: %s", e)

    if topics:
        return {
            "source": "roadmap_sh_api",
            "skill": skill,
            "slug": used_slug,
            "topics": topics,
            "topic_count": len(topics),
        }

    # Final fallback if API is completely unreachable
    return {
        "source": "fallback",
        "skill": skill,
        "slug": used_slug,
        "topics": [
            f"Introduction to {skill}",
            f"Core concepts of {skill}",
            f"{skill} fundamentals",
            f"Hands-on {skill} practice",
            f"Intermediate {skill}",
            f"Advanced {skill} topics",
            f"{skill} projects and portfolio",
        ],
        "topic_count": 7,
        "note": "Fallback topics — roadmap.sh API was unavailable",
    }
