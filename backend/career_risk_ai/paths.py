from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def _detect_backend_root() -> Path:
    for parent in PROJECT_ROOT.parents:
        if (parent / "app").exists() and (parent / "run.py").exists():
            return parent
    # Fallback for non-standard layouts.
    return PROJECT_ROOT.parent


BACKEND_ROOT = _detect_backend_root()
PROJECT_ROOT_PARENT = BACKEND_ROOT.parent
WORKSPACE_ROOT = PROJECT_ROOT_PARENT.parent

_DATA_ROOT = Path(os.getenv("HACKMIND_DATA_ROOT", BACKEND_ROOT / "data"))
_CSV_DIR = Path(os.getenv("HACKMIND_CSV_DIR", _DATA_ROOT / "csv"))
_JSON_DIR = Path(os.getenv("HACKMIND_JSON_DIR", _DATA_ROOT / "json"))

LEGACY_DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"


def ensure_data_dirs() -> None:
    _CSV_DIR.mkdir(parents=True, exist_ok=True)
    _JSON_DIR.mkdir(parents=True, exist_ok=True)


def csv_dir() -> Path:
    ensure_data_dirs()
    return _CSV_DIR


def json_dir() -> Path:
    ensure_data_dirs()
    return _JSON_DIR


def csv_path(name: str) -> Path:
    ensure_data_dirs()
    return _CSV_DIR / name


def json_path(name: str) -> Path:
    ensure_data_dirs()
    return _JSON_DIR / name


def model_path(*parts: str) -> Path:
    return MODELS_DIR.joinpath(*parts)


def resolve_csv_input(name: str) -> Path:
    """Return preferred CSV input location with legacy fallback."""
    preferred = csv_path(name)
    if preferred.exists():
        return preferred

    legacy = LEGACY_DATA_DIR / name
    if legacy.exists():
        return legacy

    return preferred


def resolve_json_input(name: str) -> Path:
    preferred = json_path(name)
    if preferred.exists():
        return preferred

    legacy = LEGACY_DATA_DIR / name
    if legacy.exists():
        return legacy

    return preferred
