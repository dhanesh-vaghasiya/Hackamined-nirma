import json

from job_suggestion.recommend import recommend_next_roles
from job_suggestion.train import train_job_suggestion_models
from pipeline.job_trends_export import export_job_trends_json
from pipeline.preflight_analysis import run_preflight
from pipeline.prepare_jobs_dataset import build_jobs_dataset_from_sources
from pipeline.demand_dataset import build_demand_dataset
from pipeline.trend_model import compute_trends
from pipeline.feature_generator import generate_features
from pipeline.train_risk_model import train_model
from pipeline.predict_risk import predict_risk
from pipeline.explainability import explain_prediction

user = {
    "normalized_job_title":"Junior Python Developer",
    "city":"Bhavnagar",
    "experience_years":5,
    "skills":["crm","analytics","data analysis"],
    "tasks":[
        "customer complaint resolution",
        "team supervision"
    ]
}

print("Building merged jobs dataset from old + recent scraped sources...")
dataset_info = build_jobs_dataset_from_sources()
print(json.dumps(dataset_info, indent=2))

print("Running training preflight analysis...")
preflight = run_preflight()
print(json.dumps(preflight["summary"], indent=2))

risk_cfg = preflight["summary"]["recommended"]["risk"]
sug_cfg = preflight["summary"]["recommended"]["job_suggestion"]

print("Building demand dataset...")
build_demand_dataset()

print("Learning market trends...")
trends = compute_trends()

print("Training risk model...")
train_model(max_roles=risk_cfg["max_roles"], max_cities=risk_cfg["max_cities"])

print("Training job suggestion models...")
suggestion_train_info = train_job_suggestion_models(
    max_roles=sug_cfg["max_roles"],
    max_cities=sug_cfg["max_cities"],
    fallback_city_count=sug_cfg["fallback_city_count"],
)
print(json.dumps(suggestion_train_info, indent=2))

print("Exporting job trend JSON...")
trend_export_info = export_job_trends_json()
print(json.dumps(trend_export_info, indent=2))

print("Generating features...")
features = generate_features(user,trends)

print("Predicting risk...")

risk = predict_risk(features)
explanation = explain_prediction(features)

result = {
    "risk_score":float(risk),
    "risk_level":"HIGH" if risk>0.6 else "MEDIUM" if risk>0.4 else "LOW",
    "features_used":features,
    "explainability": explanation,
}

print(result)

print("\nGenerating job suggestions...")
suggestion_user = {
    "current_role": user["normalized_job_title"],
    "city": user["city"],
    "skills": user["skills"],
    "experience_years": user["experience_years"],
    "risk_level": result["risk_level"],
}
recommendations = recommend_next_roles(user_profile=suggestion_user, top_k=3)
print(json.dumps(recommendations, indent=2))