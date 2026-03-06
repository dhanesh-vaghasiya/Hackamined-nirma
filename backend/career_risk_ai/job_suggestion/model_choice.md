# Model Choice

## Best Choice For This Project
- Ranking model: `LightGBM LambdaMART`
- Representation model: `sentence-transformers/all-MiniLM-L6-v2`

This module is now configured in strict mode to use these models only.

This is the best fit here because your task is a top-k ranking problem with mixed tabular + semantic features and a need for stable results on small-to-medium datasets.

## Primary Model Stack
1. Role Representation Model:
- `sentence-transformers/all-MiniLM-L6-v2`
- Purpose: Convert role text and user-skill context into semantic embeddings.

2. Recommendation Ranking Model:
- `LightGBM LambdaMART` (learning-to-rank)
- Purpose: Rank candidate roles by transition quality and opportunity.

3. Transition Feasibility Classifier:
- `LightGBMClassifier`
- Purpose: Filter out unrealistic role jumps and keep recommendations to realistic next-step moves.

## Why This Combination
- Embeddings capture semantic similarity (adjacent roles, not random roles).
- LambdaMART is strong for top-k ranking tasks (top 2 to 3 suggestions).
- Supports mixed feature types: numeric trend features, overlap features, and embedding-based similarity.

## Dependency Requirement
- `lightgbm` must be installed.
- `sentence-transformers` must be installed.

## Candidate Features for Ranking
- user_role_to_candidate_role_embedding_similarity
- skill_overlap_ratio
- skill_gap_count
- city_role_demand_score
- city_role_trend_score
- experience_alignment_score
- risk_level_signal

## Candidate Features for Transition Gate
- user_role_to_candidate_role_embedding_similarity
- transferable_skill_ratio
- estimated_upskill_effort
- experience_alignment_score

## Inference Policy
- Generate candidate roles from dataset roles only.
- Run transition feasibility gate first.
- Score all candidates in current city.
- Return `best_current_city_role`.
- Score all accepted candidates across all cities and return `best_overall_role`.
- Return top 2 to 3 accepted candidates as `next_step_roles`.
- If fewer than 2 confident recommendations exist, score fallback cities and add best alternatives.
