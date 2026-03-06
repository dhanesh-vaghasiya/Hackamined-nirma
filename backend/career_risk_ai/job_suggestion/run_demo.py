from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from job_suggestion.recommend import recommend_next_roles
    from job_suggestion.train import train_job_suggestion_models
except ModuleNotFoundError:
    # Allow running this file directly from inside `job_suggestion/`.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from job_suggestion.recommend import recommend_next_roles
    from job_suggestion.train import train_job_suggestion_models


if __name__ == "__main__":
    train_info = train_job_suggestion_models()
    print("Training complete:")
    print(json.dumps(train_info, indent=2))

    user_profile = {
        "current_role": "CRM Executive",
        "city": "Bhavnagar",
        "skills": ["crm", "analytics", "data analysis", "customer management"],
        "experience_years": 5,
        "risk_level": "HIGH",
    }

    result = recommend_next_roles(user_profile=user_profile, top_k=3)
    print("\nRecommendation output:")
    print(json.dumps(result, indent=2))
