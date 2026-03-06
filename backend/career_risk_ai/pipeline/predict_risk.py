from pathlib import Path

import joblib

from paths import model_path

def predict_risk(features):
    risk_model_path = model_path("risk_model.pkl")
    model = joblib.load(risk_model_path)

    risk = model.predict([features])[0]

    return risk