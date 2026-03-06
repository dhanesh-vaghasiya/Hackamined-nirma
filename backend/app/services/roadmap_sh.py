"""Fetch structured roadmaps from roadmap.sh with fuzzy role-to-slug matching."""

from __future__ import annotations

import logging
import re
from functools import lru_cache

import requests

log = logging.getLogger(__name__)

_ROADMAP_SH_LIST_URL = "https://roadmap.sh/api/v1-list-official-roadmaps"
_ROADMAP_SH_DETAIL_URL = "https://roadmap.sh/api/v1-official-roadmap/{slug}"
_TIMEOUT = 20

# ── Manual mappings: common role keywords → roadmap.sh slug ──────────────
# These catch roles that don't map obviously from their name.
_ROLE_KEYWORD_TO_SLUG = {
    "frontend": "frontend",
    "front end": "frontend",
    "front-end": "frontend",
    "ui developer": "frontend",
    "ui engineer": "frontend",
    "backend": "backend",
    "back end": "backend",
    "back-end": "backend",
    "full stack": "full-stack",
    "fullstack": "full-stack",
    "full-stack": "full-stack",
    "devops": "devops",
    "devsecops": "devsecops",
    "data scientist": "ai-data-scientist",
    "data science": "ai-data-scientist",
    "data analyst": "data-analyst",
    "data engineer": "data-engineer",
    "machine learning": "machine-learning",
    "ml engineer": "machine-learning",
    "mlops": "mlops",
    "ai engineer": "ai-engineer",
    "android": "android",
    "ios developer": "ios",
    "ios": "ios",
    "react native": "react-native",
    "flutter": "flutter",
    "react developer": "react",
    "react": "react",
    "angular": "angular",
    "vue": "vue",
    "node": "nodejs",
    "nodejs": "nodejs",
    "node.js": "nodejs",
    "python developer": "python",
    "python": "python",
    "java developer": "java",
    "java": "java",
    "golang": "golang",
    "go developer": "golang",
    "rust": "rust",
    "php": "php",
    "laravel": "laravel",
    "django": "django",
    "spring boot": "spring-boot",
    "spring": "spring-boot",
    "typescript": "typescript",
    "javascript": "javascript",
    "cybersecurity": "cyber-security",
    "cyber security": "cyber-security",
    "security analyst": "cyber-security",
    "security engineer": "cyber-security",
    "cloud engineer": "aws",
    "aws": "aws",
    "kubernetes": "kubernetes",
    "docker": "docker",
    "terraform": "terraform",
    "system design": "system-design",
    "software architect": "software-architect",
    "qa": "qa",
    "qa engineer": "qa",
    "quality assurance": "qa",
    "tester": "qa",
    "test engineer": "qa",
    "product manager": "product-manager",
    "ux designer": "ux-design",
    "ux": "ux-design",
    "ui/ux": "ux-design",
    "technical writer": "technical-writer",
    "engineering manager": "engineering-manager",
    "blockchain": "blockchain",
    "dba": "postgresql-dba",
    "database administrator": "postgresql-dba",
    "sql": "sql",
    "mongodb": "mongodb",
    "prompt engineer": "prompt-engineering",
    "game developer": "game-developer",
    "game dev": "game-developer",
    "bi analyst": "bi-analyst",
    "business intelligence": "bi-analyst",
    "nextjs": "nextjs",
    "next.js": "nextjs",
    "graphql": "graphql",
    "redis": "redis",
    "api design": "api-design",
    "css": "css",
    "html": "html",
    "c++": "cpp",
    "cpp": "cpp",
    "ruby": "ruby",
    "rails": "ruby-on-rails",
    "swift": "swift-ui",
    "kotlin": "kotlin",
    "linux": "linux",
    "shell": "shell-bash",
    "bash": "shell-bash",
    "computer science": "computer-science",
    "dsa": "datastructures-and-algorithms",
    "data structures": "datastructures-and-algorithms",
    "elasticsearch": "elasticsearch",
    "cloudflare": "cloudflare",
    "git": "git-github",
    "devrel": "devrel",
}


@lru_cache(maxsize=1)
def get_available_slugs() -> list[str]:
    """Fetch and cache all available roadmap.sh slugs."""
    try:
        resp = requests.get(_ROADMAP_SH_LIST_URL, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list):
            return []
        return sorted(
            item.get("slug")
            for item in data
            if isinstance(item, dict) and item.get("slug")
        )
    except Exception as exc:
        log.warning("Failed to fetch roadmap.sh slug list: %s", exc)
        return []


def match_role_to_slug(role: str) -> str | None:
    """
    Map a user's target role to a roadmap.sh slug.

    Strategy:
    1. Check keyword mappings (handles "Java Frontend Developer" → "frontend")
    2. Check if any slug directly matches a word in the role
    3. Return None if no match (caller should fall back to Groq)
    """
    role_lower = role.lower().strip()
    available = get_available_slugs()
    available_set = set(available)

    # 1. Keyword mapping — check longest matches first
    sorted_keywords = sorted(_ROLE_KEYWORD_TO_SLUG.keys(), key=len, reverse=True)
    for keyword in sorted_keywords:
        if keyword in role_lower:
            slug = _ROLE_KEYWORD_TO_SLUG[keyword]
            if slug in available_set:
                return slug

    # 2. Slugify the role and try direct match
    role_slug = re.sub(r"[^a-z0-9]+", "-", role_lower).strip("-")
    if role_slug in available_set:
        return role_slug

    # 3. Try each word in the role as a slug
    words = re.findall(r"[a-z]+", role_lower)
    # Try longer words first (more specific)
    for word in sorted(words, key=len, reverse=True):
        if word in available_set and len(word) > 2:
            return word

    return None


def fetch_roadmap_topics(slug: str) -> dict | None:
    """
    Fetch a roadmap from roadmap.sh and return structured topic data.

    Returns:
    {
        "slug": "frontend",
        "source": "roadmap.sh",
        "sections": [
            {
                "title": "Internet",
                "type": "topic",
                "subtopics": ["How does the internet work?", "What is HTTP?", ...]
            },
            ...
        ]
    }
    """
    url = _ROADMAP_SH_DETAIL_URL.format(slug=slug)
    try:
        resp = requests.get(url, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        log.warning("Failed to fetch roadmap %s: %s", slug, exc)
        return None

    if data.get("error"):
        return None

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    if not nodes:
        return None

    # Build adjacency: source → [targets]
    children_map: dict[str, list[str]] = {}
    for edge in edges:
        src = edge.get("source")
        tgt = edge.get("target")
        if src and tgt:
            children_map.setdefault(src, []).append(tgt)

    # Index nodes by id
    node_by_id = {n["id"]: n for n in nodes}

    # Extract topics and subtopics with position-based ordering
    topics = []
    subtopics = []
    for n in nodes:
        ntype = n.get("type")
        label = n.get("data", {}).get("label")
        if not label:
            continue
        y_pos = n.get("position", {}).get("y", 0)
        # For subtopics nested in groups, add parent's position
        parent_id = n.get("parentId")
        if parent_id and parent_id in node_by_id:
            parent_y = node_by_id[parent_id].get("position", {}).get("y", 0)
            y_pos += parent_y
        if ntype == "topic":
            topics.append({"id": n["id"], "label": label, "y": y_pos, "subtopics": []})
        elif ntype == "subtopic":
            subtopics.append({"id": n["id"], "label": label, "y": y_pos})

    # Sort by vertical position (top → bottom = learning order)
    topics.sort(key=lambda t: t["y"])
    subtopics.sort(key=lambda s: s["y"])

    # Try to assign subtopics to nearest preceding topic by y-position
    topic_ids = {t["id"] for t in topics}
    # Build set of children per topic via edges
    topic_children: dict[str, list[str]] = {}
    for t in topics:
        # Collect all nodes reachable from this topic via edges
        tid = t["id"]
        direct_children = children_map.get(tid, [])
        for cid in direct_children:
            cnode = node_by_id.get(cid)
            if cnode and cnode.get("type") == "subtopic":
                topic_children.setdefault(tid, []).append(cid)

    subtopic_assigned = set()
    for t in topics:
        child_ids = set(topic_children.get(t["id"], []))
        for st in subtopics:
            if st["id"] in child_ids and st["id"] not in subtopic_assigned:
                t["subtopics"].append(st["label"])
                subtopic_assigned.add(st["id"])

    # Assign remaining subtopics to nearest topic by y-position
    for st in subtopics:
        if st["id"] in subtopic_assigned:
            continue
        best_topic = None
        best_dist = float("inf")
        for t in topics:
            dist = abs(st["y"] - t["y"])
            if dist < best_dist:
                best_dist = dist
                best_topic = t
        if best_topic:
            best_topic["subtopics"].append(st["label"])
            subtopic_assigned.add(st["id"])

    sections = []
    for t in topics:
        sections.append({
            "title": t["label"],
            "type": "topic",
            "subtopics": t["subtopics"],
        })

    return {
        "slug": slug,
        "source": "roadmap.sh",
        "total_topics": len(topics),
        "total_subtopics": len(subtopics),
        "sections": sections,
    }


def get_detailed_roadmap(role: str) -> dict | None:
    """
    Main entry point: try to match role to roadmap.sh and fetch it.
    Returns structured roadmap data or None if no match found.
    """
    slug = match_role_to_slug(role)
    if not slug:
        log.info("No roadmap.sh match for role '%s'", role)
        return None

    log.info("Matched role '%s' → roadmap.sh slug '%s'", role, slug)
    result = fetch_roadmap_topics(slug)
    if result:
        result["matched_from_role"] = role
    return result
