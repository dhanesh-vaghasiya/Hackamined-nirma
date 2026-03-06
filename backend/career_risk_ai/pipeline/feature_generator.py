import pandas as pd

from paths import resolve_csv_input

def generate_features(user, trends):

    skill_scores = []

    for s in user["skills"]:
        skill_scores.append(trends.get(s.lower(),0))

    avg_trend = sum(skill_scores)/len(skill_scores)

    location_df = pd.read_csv(resolve_csv_input("jobs.csv"))

    loc_jobs = location_df[location_df["location"] == user["city"]]

    location_score = len(loc_jobs) / len(location_df)

    automation_map = {
        "data entry":0.9,
        "copy paste":0.9,
        "customer complaint resolution":0.5,
        "team supervision":0.3
    }

    auto_scores = []

    for t in user["tasks"]:
        auto_scores.append(automation_map.get(t.lower(),0.3))

    automation_risk = sum(auto_scores)/len(auto_scores)

    return [
        avg_trend,
        location_score,
        automation_risk,
        user["experience_years"]
    ]