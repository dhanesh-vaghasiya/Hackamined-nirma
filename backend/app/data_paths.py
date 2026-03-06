from __future__ import annotations

import os
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.getenv("HACKMIND_DATA_ROOT", BACKEND_ROOT / "data"))
CSV_DIR = Path(os.getenv("HACKMIND_CSV_DIR", DATA_ROOT / "csv"))
JSON_DIR = Path(os.getenv("HACKMIND_JSON_DIR", DATA_ROOT / "json"))


def ensure_data_dirs() -> None:
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    JSON_DIR.mkdir(parents=True, exist_ok=True)


def configure_data_environment() -> None:
    ensure_data_dirs()
    os.environ.setdefault("HACKMIND_DATA_ROOT", str(DATA_ROOT))
    os.environ.setdefault("HACKMIND_CSV_DIR", str(CSV_DIR))
    os.environ.setdefault("HACKMIND_JSON_DIR", str(JSON_DIR))
