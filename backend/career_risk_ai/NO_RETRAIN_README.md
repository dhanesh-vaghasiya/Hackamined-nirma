# No-Retrain Update Flow

Use this when new scraped data arrives and you want to:
- keep existing trained model weights
- refresh demand/trend data
- refresh `job_trends.json`
- run inference with latest market snapshot

## Command
From project root:

```bash
python run_realtime_update_no_retrain.py --max-rows 150 --location "" --keywords "developer,analyst,engineer,designer,manager"
```

## What this does
1. Scrapes new realtime jobs and saves `data/recent_scrapper_data.csv`
2. Merges old + new into `data/jobs.csv`
3. Rebuilds `data/skill_demand.csv`
4. Rebuilds `data/job_trends.json`
5. Runs risk + job-suggestion inference using existing `.pkl` models

## What this does NOT do
- It does **not** retrain:
  - `models/risk_model.pkl`
  - `models/job_suggestion/job_suggestion_models.pkl`

So old learned weights are preserved.
