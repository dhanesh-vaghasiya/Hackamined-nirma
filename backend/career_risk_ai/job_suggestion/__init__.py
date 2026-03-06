"""Job suggestion package for next-step role recommendations."""

from job_suggestion.recommend import recommend_next_roles
from job_suggestion.train import train_job_suggestion_models

__all__ = ["recommend_next_roles", "train_job_suggestion_models"]
