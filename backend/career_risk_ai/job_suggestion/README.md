# Job Suggestion Module

This module is isolated from the existing `pipeline/` and is intended to recommend the next 2 to 3 target jobs for a user based only on dataset signals.

## Goal
- Suggest adjacent next-step roles (not a direct jump to unrelated roles).
- Prefer roles available in the user's current city.
- If high-quality roles are not available in the current city, include fallback roles from other cities.
- Keep recommendation logic model-learned (not hardcoded role-mapping).

## Current Scope
- Architecture and contracts only.
- No integration with existing risk pipeline yet.
- No edits to existing files.

## Planned Output Shape
- `best_current_city_role`: single best role in current city right now.
- `best_overall_role`: single best role globally (any city) right now.
- `next_step_roles`: top 2 to 3 realistic role transitions from current profile.
- `current_city_recommendations`: top 2 to 3 roles in current city.
- `fallback_city_recommendations`: top roles in other cities only if needed.
- Each recommendation contains:
  - role
  - city
  - recommendation_score
  - confidence
  - missing_skills
  - reasoning_summary

See `architecture.md` and `model_choice.md` for details.
