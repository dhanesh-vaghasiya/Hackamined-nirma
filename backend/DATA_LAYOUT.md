# Unified Backend Data Layout

All generated and required data files are centralized under:

- `backend/data/csv`: all CSV files
- `backend/data/json`: all JSON files

## Environment variables

These are auto-configured by `app.data_paths.configure_data_environment()` when backend starts.

- `HACKMIND_DATA_ROOT`
- `HACKMIND_CSV_DIR`
- `HACKMIND_JSON_DIR`

You can override them manually if needed.

## Integrated modules

- Legacy `userInputHandler` standalone processors are no longer required for backend runtime.
- `career_risk_ai` is vendored at `backend/career_risk_ai` and loaded locally by backend services.
- Runtime API flow no longer depends on workspace-level `career_risk_ai` folder.

## New API route

`POST /api/career/analyze`

- Input: same payload as `/api/user-input/analyze-profile`
- Output: normalized profile + risk + explainability + role suggestions
- Also writes `career_analysis.json` to `backend/data/json`
