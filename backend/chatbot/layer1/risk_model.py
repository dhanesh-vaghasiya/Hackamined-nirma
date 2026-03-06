def predict_risk():

    result = {
        "risk_score": 0.7597,
        "risk_level": "HIGH",
        "features_used": [-0.0754, 0.2046, 0.4, 5],
        "explainability": {
            "base_value": 0.5202,
            "feature_contributions": {
                "avg_trend": 0.1769,
                "location_score": 0.1014,
                "automation_risk": -0.0334,
                "experience_years": -0.0054
            }
        }
    }

    worker_profile = {
        "role": "Data Entry Operator",
        "city": "Indore",
        "experience": 5
    }

    job_pipeline = {
        "BPO": 428,
        "Data Analyst": 96
    }

    return {
        "worker_profile": worker_profile,
        "risk_analysis": result,
        "job_pipeline": job_pipeline
    }