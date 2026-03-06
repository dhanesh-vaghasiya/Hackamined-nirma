def build_prompt(layer1, question, qtype, hindi=False):

    profile = layer1["worker_profile"]
    risk = layer1["risk_analysis"]
    jobs = layer1["job_pipeline"]

    context = f"""
Worker Profile:
Role: {profile['role']}
City: {profile['city']}
Experience: {profile['experience']} years

Layer-1 Risk Data:
Risk Score: {risk['risk_score']}
Risk Level: {risk['risk_level']}

Explainability Signals:
Skill Trend Impact: {risk['explainability']['feature_contributions']['avg_trend']}
Location Demand Impact: {risk['explainability']['feature_contributions']['location_score']}
Automation Risk Impact: {risk['explainability']['feature_contributions']['automation_risk']}
Experience Impact: {risk['explainability']['feature_contributions']['experience_years']}

Job Pipeline:
BPO jobs in {profile['city']}: {jobs['BPO']}
Data Analyst jobs: {jobs['Data Analyst']}
"""

    if qtype == "risk":

        task = "Explain clearly why the risk score is high using the signals."

    elif qtype == "safe_jobs":

        task = "Suggest 3 safer jobs for this worker and explain why."

    elif qtype == "career_path":

        task = "Suggest career transitions that can be achieved within 3 months."

    elif qtype == "job_count":

        task = "Return the exact job count from the pipeline."

    else:

        task = "Answer the user's question using the data above."

    language = "Respond in Hindi." if hindi else ""

    prompt = f"""
You are the Skills Mirage Career Intelligence Assistant.

{context}

User Question:
{question}

Task:
{task}

Rules:
Use the data provided above.
Do not hallucinate numbers.

{language}
"""

    return prompt