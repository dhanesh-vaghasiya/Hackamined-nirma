# Architecture: Dataset-Driven Job Suggestion

## Inputs
- User profile:
  - current_role
  - city
  - skills
  - experience_years
  - risk_level (from existing risk model output, passed as input only)
- Dataset:
  - `data/jobs.csv`
  - `data/skill_demand.csv`

## Stage 1: Build Role Profiles
- Aggregate jobs by `job_title`.
- Extract role-skill profile from descriptions and parsed skills.
- Create role representation vectors from text and skills.

## Stage 2: Build City-Role Opportunity Signals
- Aggregate demand by (`job_title`, `location`, `posted_date`).
- Estimate near-term opportunity score per (`job_title`, `location`) using trend features.

## Stage 3: Learn Transition Feasibility
- For each user and candidate role:
  - skill overlap score
  - skill gap size
  - experience alignment
  - role demand trend score
  - city opportunity score
  - risk-aware adjustment signal
- Train a ranking model to produce `recommendation_score`.

## Stage 3.5: Adjacent-Move Gate (Model-Driven)
- Before final ranking output, apply a learned transition feasibility gate to prevent unrealistic direct switches.
- Candidate role is accepted only when:
  - semantic role similarity is above learned threshold, and
  - skill gap is within learned tolerance for profile type.
- This keeps recommendations as "next move" roles instead of distant role jumps.

## Stage 4: Decision Layer
- Rank candidates for current city first.
- Produce `best_current_city_role` from current city candidate pool.
- Produce `best_overall_role` from all city candidate pool.
- Return `next_step_roles` (2 to 3) from highest-scoring realistic transitions.
- Return top 2 to 3 current-city roles if score and confidence pass threshold.
- If current city has weak options, add top fallback roles from other cities.

## Non-Goals
- No hardcoded role transitions like `A -> B`.
- No manual city priority lists outside model + threshold policy.

## Why This Fits Your Ask
- Uses dataset-derived features only.
- Produces adjacent role recommendations instead of unrealistic direct role switches.
- Handles city-first, then fallback city behavior.
- Exposes both best local role and best overall role.
- Keeps recommendation quality tied to learned model scores.
