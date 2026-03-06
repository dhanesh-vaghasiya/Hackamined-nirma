from pathlib import Path

import joblib
import numpy as np
import shap

from paths import model_path


FEATURE_NAMES = [
    "avg_trend",
    "location_score",
    "automation_risk",
    "experience_years",
]


def explain_prediction(features, feature_names=None):
    """Return SHAP contributions for one prediction from the trained tree model."""
    risk_model_path = model_path("risk_model.pkl")

    model = joblib.load(risk_model_path)

    x = np.array([features], dtype=float)
    names = feature_names or FEATURE_NAMES

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(x)

    values = shap_values[0] if shap_values.ndim == 2 else shap_values
    expected = explainer.expected_value
    base_value = float(expected[0]) if isinstance(expected, np.ndarray) else float(expected)

    return {
        "base_value": base_value,
        "feature_contributions": {
            name: float(value) for name, value in zip(names, values)
        },
    }