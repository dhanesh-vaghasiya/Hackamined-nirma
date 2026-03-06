"""
AI Agent for roadmap generation.
Uses Groq LLM with tool-calling to:
  1. Gather user context & market data
  2. Recommend a skill
  3. Generate a roadmap (Roadman API)
  4. Structure the roadmap
  5. Map NPTEL courses
"""

import os
import json
import logging

import requests

from app.services.agent.tools.db_tools import (
    get_skill_trends,
    get_ai_vulnerability,
    get_skill_intel,
    get_related_skills,
    get_processed_output,
    get_all_skill_intel,
)
from app.services.agent.tools.nptel_tools import search_nptel_courses
from app.services.agent.tools.roadman_tools import generate_roadmap_via_api, list_available_roadmaps

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# ── Tool definitions for the LLM ─────────────────────────
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_skill_trends",
            "description": "Get current skill demand trends showing growing and declining skills with their growth rates.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ai_vulnerability",
            "description": "Get AI automation vulnerability score and risk assessment for a specific job role.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role": {"type": "string", "description": "The job role to assess"},
                    "city": {"type": "string", "description": "The city (optional)"},
                },
                "required": ["role"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_skill_intel",
            "description": "Get detailed intelligence about a specific skill including demand score, growth rate, salary impact, and AI relevance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill": {"type": "string", "description": "The skill name to look up"},
                },
                "required": ["skill"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_related_skills",
            "description": "Get skills related to a given role or skill.",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill_or_role": {"type": "string", "description": "A skill name or job role"},
                },
                "required": ["skill_or_role"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_skill_intel",
            "description": "Get intelligence data for all tracked skills in the system.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_nptel_courses",
            "description": "Search NPTEL courses by skill or topic. Returns course title, institution, duration, and URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Skill or topic to search for"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_roadmap",
            "description": "Fetch a learning roadmap from roadmap.sh for a skill. Returns a list of topics/subtopics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "skill": {"type": "string", "description": "The skill to generate a roadmap for"},
                },
                "required": ["skill"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_available_roadmaps",
            "description": "List all available roadmap slugs from roadmap.sh. Use this to find valid roadmap names.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

# ── Tool dispatcher ──────────────────────────────────────
TOOL_MAP = {
    "get_skill_trends": lambda _args: get_skill_trends(),
    "get_ai_vulnerability": lambda args: get_ai_vulnerability(args["role"], args.get("city", "")),
    "get_skill_intel": lambda args: get_skill_intel(args["skill"]),
    "get_related_skills": lambda args: get_related_skills(args["skill_or_role"]),
    "get_all_skill_intel": lambda _args: get_all_skill_intel(),
    "search_nptel_courses": lambda args: search_nptel_courses(args["query"]),
    "generate_roadmap": lambda args: generate_roadmap_via_api(args["skill"]),
    "list_available_roadmaps": lambda _args: list_available_roadmaps(),
}


def _call_groq(messages: list, tools: list | None = None, temperature: float = 0.3) -> dict:
    """Make a chat completion call to the Groq API."""
    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 4096,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    resp = requests.post(GROQ_API_URL, json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()


def _execute_tool_calls(tool_calls: list) -> list[dict]:
    """Execute tool calls requested by the LLM and return results."""
    results = []
    for tc in tool_calls:
        fn_name = tc["function"]["name"]
        fn_args = json.loads(tc["function"]["arguments"]) if tc["function"]["arguments"] else {}
        logger.info("Agent calling tool: %s(%s)", fn_name, fn_args)

        handler = TOOL_MAP.get(fn_name)
        if handler:
            result = handler(fn_args)
        else:
            result = {"error": f"Unknown tool: {fn_name}"}

        results.append({
            "role": "tool",
            "tool_call_id": tc["id"],
            "content": json.dumps(result, default=str),
        })
    return results


# ═══════════════════════════════════════════════════════════
# Main pipeline
# ═══════════════════════════════════════════════════════════

def run_roadmap_pipeline(user_profile: dict) -> dict:
    """
    Full agentic pipeline:
      1. Gather data via tools
      2. Recommend a skill
      3. Generate roadmap
      4. Structure roadmap
      5. Map NPTEL courses
    Returns a dict with all pipeline stages.
    """
    pipeline_result = {
        "user_profile": user_profile,
        "data_retrieved": {},
        "recommended_skill": None,
        "raw_roadmap": None,
        "structured_roadmap": None,
        "nptel_courses": [],
        "agent_reasoning": [],
    }

    job_title = user_profile.get("job_title", "Unknown")
    city = user_profile.get("city", "")
    experience = user_profile.get("experience", 0)
    description = user_profile.get("description", "")
    user_id = user_profile.get("user_id")

    # ── Step 0: Gather processed output if user_id exists ─
    processed = {}
    if user_id:
        processed = get_processed_output(user_id)
        pipeline_result["data_retrieved"]["processed_output"] = processed

    # ── Step 1: Agent gathers data & recommends a skill ──
    system_prompt = """You are an AI career advisor agent for the HackaMinded platform.
Your job is to analyze a worker's profile and market data to recommend ONE specific skill/technology they should learn next.

You have access to these tools:
- get_skill_trends(): Get growing and declining skill trends
- get_ai_vulnerability(role, city): Get AI automation risk for a role
- get_skill_intel(skill): Get demand, growth, salary impact for a skill
- get_related_skills(skill_or_role): Get related skills for a role or skill
- get_all_skill_intel(): Get data on all tracked skills

IMPORTANT: You MUST use the tools to gather data before making your recommendation.
Call at least 2-3 tools to gather context, then provide your recommendation.

After gathering data, respond with a JSON object (no markdown, no code fences):
{
  "recommended_skill": "SkillName",
  "reasoning": "Why this skill is recommended...",
  "risk_assessment": "Summary of AI risk for their role...",
  "growth_potential": "How this skill is growing..."
}"""

    user_msg = f"""Analyze this worker profile and recommend ONE skill to learn:

Job Title: {job_title}
City: {city}
Experience: {experience} years
Description: {description}

Their current skills: {json.dumps(processed.get('skills', []))}
Their current tools: {json.dumps(processed.get('tools', []))}
Their aspirations: {json.dumps(processed.get('aspirations', []))}

Use the available tools to gather market data, then recommend the single best skill for them to learn."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_msg},
    ]

    # Agent loop (max 5 iterations for tool calls)
    recommended_skill = None
    for _iteration in range(5):
        response = _call_groq(messages, tools=TOOL_DEFINITIONS)
        choice = response["choices"][0]
        assistant_msg = choice["message"]
        messages.append(assistant_msg)

        # If the LLM wants to call tools
        if assistant_msg.get("tool_calls"):
            tool_results = _execute_tool_calls(assistant_msg["tool_calls"])
            # Store retrieved data
            for tr in tool_results:
                try:
                    data = json.loads(tr["content"])
                    pipeline_result["data_retrieved"][tr["tool_call_id"]] = data
                except Exception:
                    pass
            messages.extend(tool_results)
            pipeline_result["agent_reasoning"].append({
                "step": "tool_call",
                "tools_called": [tc["function"]["name"] for tc in assistant_msg["tool_calls"]],
            })
            continue

        # LLM gave a final answer
        content = assistant_msg.get("content", "")
        pipeline_result["agent_reasoning"].append({"step": "recommendation", "raw": content})

        try:
            # Try to parse JSON from the response
            clean = content.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            recommendation = json.loads(clean)
            recommended_skill = recommendation.get("recommended_skill", "")
            pipeline_result["recommended_skill"] = recommendation
        except (json.JSONDecodeError, IndexError):
            # If JSON parsing fails, extract the skill name heuristically
            recommended_skill = _extract_skill_from_text(content)
            pipeline_result["recommended_skill"] = {
                "recommended_skill": recommended_skill,
                "reasoning": content,
            }
        break

    if not recommended_skill:
        recommended_skill = "Python"  # safe default
        pipeline_result["recommended_skill"] = {
            "recommended_skill": recommended_skill,
            "reasoning": "Default recommendation due to agent timeout.",
        }

    # ── Step 2: Generate roadmap via roadmap.sh ─────────
    raw_roadmap = generate_roadmap_via_api(recommended_skill)
    pipeline_result["raw_roadmap"] = raw_roadmap

    # ── Step 3: Structure the roadmap via LLM ───────────
    topics_list = raw_roadmap.get("topics", [])
    structure_prompt = f"""You are a learning roadmap structuring assistant.

A user wants to learn "{recommended_skill}". Here are all the topics from the official roadmap.sh roadmap:

{json.dumps(topics_list, indent=2)}

User context:
- Current role: {job_title}
- Experience: {experience} years
- City: {city}

Group these {len(topics_list)} topics into 4-6 logical learning stages (beginner → advanced).
Output a JSON object (no markdown, no code fences) with this structure:
{{
  "skill": "SkillName",
  "total_duration": "X weeks",
  "stages": [
    {{
      "stage_number": 1,
      "name": "Stage Name",
      "duration": "X weeks",
      "description": "What you'll learn",
      "topics": ["topic1", "topic2", "topic3"],
      "learning_outcomes": ["outcome1", "outcome2"]
    }}
  ]
}}"""

    structure_response = _call_groq([
        {"role": "system", "content": "You are a structured data formatter. Always respond with valid JSON."},
        {"role": "user", "content": structure_prompt},
    ], temperature=0.2)

    structure_content = structure_response["choices"][0]["message"].get("content", "")
    try:
        clean = structure_content.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        structured = json.loads(clean)
        pipeline_result["structured_roadmap"] = structured
    except (json.JSONDecodeError, IndexError):
        # Auto-structure topics into stages if LLM parsing fails
        chunk_size = max(1, len(topics_list) // 4)
        auto_stages = []
        for i in range(0, len(topics_list), chunk_size):
            chunk = topics_list[i:i + chunk_size]
            stage_num = (i // chunk_size) + 1
            auto_stages.append({
                "stage_number": stage_num,
                "name": f"Stage {stage_num}",
                "duration": "2-3 weeks",
                "description": f"Learn: {', '.join(chunk[:3])}...",
                "topics": chunk,
            })
        pipeline_result["structured_roadmap"] = {
            "skill": recommended_skill,
            "total_duration": f"{len(auto_stages) * 2}-{len(auto_stages) * 3} weeks",
            "stages": auto_stages,
            "note": "Auto-structured from roadmap.sh topics",
        }

    # ── Step 4: Map NPTEL courses to stages ─────────────
    stages = pipeline_result["structured_roadmap"].get("stages", [])
    all_courses = []

    # Search for the main skill
    main_courses = search_nptel_courses(recommended_skill, max_results=3)
    all_courses.extend(main_courses)

    # Search for stage-specific topics
    searched_queries = {recommended_skill.lower()}
    for stage in stages:
        topics = stage.get("topics", [])
        stage_name = stage.get("name", "")
        for query in [stage_name] + topics[:2]:
            q_lower = query.lower()
            if q_lower not in searched_queries and len(q_lower) > 2:
                searched_queries.add(q_lower)
                stage_courses = search_nptel_courses(query, max_results=2)
                all_courses.extend(stage_courses)

    # Deduplicate by URL
    seen_urls = set()
    unique_courses = []
    for c in all_courses:
        if c["url"] not in seen_urls:
            seen_urls.add(c["url"])
            unique_courses.append(c)

    pipeline_result["nptel_courses"] = unique_courses

    # ── Step 5: Generate final combined output via LLM ──
    final_prompt = f"""Create a final, polished learning roadmap summary for a user.

Skill to learn: {recommended_skill}
User's current role: {job_title} ({experience} years experience in {city})

Structured roadmap:
{json.dumps(pipeline_result['structured_roadmap'], indent=2)}

Available NPTEL courses:
{json.dumps(unique_courses, indent=2)}

Create a JSON response (no markdown, no code fences) with:
{{
  "title": "Your Learning Roadmap: SkillName",
  "summary": "A 2-3 sentence overview",
  "total_duration": "X weeks",
  "stages": [
    {{
      "stage_number": 1,
      "name": "Stage Name",
      "duration": "X weeks",
      "description": "Description",
      "topics": ["topic1", "topic2"],
      "recommended_courses": [
        {{
          "title": "Course Name",
          "institution": "IIT X",
          "duration": "Y weeks",
          "url": "https://..."
        }}
      ]
    }}
  ],
  "career_impact": "How this skill will help them"
}}

Map the NPTEL courses to the most relevant stages. Each stage should have 1-2 courses if available."""

    final_response = _call_groq([
        {"role": "system", "content": "You are a career roadmap expert. Always respond with valid JSON."},
        {"role": "user", "content": final_prompt},
    ], temperature=0.2)

    final_content = final_response["choices"][0]["message"].get("content", "")
    try:
        clean = final_content.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        final_roadmap = json.loads(clean)
        pipeline_result["final_roadmap"] = final_roadmap
    except (json.JSONDecodeError, IndexError):
        pipeline_result["final_roadmap"] = {
            "title": f"Learning Roadmap: {recommended_skill}",
            "summary": f"A structured path to learn {recommended_skill}.",
            "stages": pipeline_result["structured_roadmap"].get("stages", []),
            "nptel_courses": unique_courses,
            "note": "Final formatting by fallback",
        }

    return pipeline_result


def _extract_skill_from_text(text: str) -> str:
    """Heuristic extraction of a skill name from free-form text."""
    known_skills = [
        "Python", "Data Analytics", "Prompt Engineering", "Machine Learning",
        "SQL", "Power BI", "Cybersecurity", "Cloud Computing", "AI Literacy",
        "Financial Modelling", "Excel", "Tally", "Product Management",
        "UX Research", "Digital Marketing", "Deep Learning",
    ]
    text_lower = text.lower()
    for skill in known_skills:
        if skill.lower() in text_lower:
            return skill
    return "Python"
