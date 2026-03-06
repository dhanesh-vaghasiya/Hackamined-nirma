"""
One-off script: normalize a scraper CSV and load it into the SQL database.

Usage:
    cd backend
    python -m scripts.import_csv <path_to_csv>

Example:
    python -m scripts.import_csv ../naukri_jobs_data.csv
"""

import sys
from datetime import date

from app import create_app
from app.services.scraper.normalizer import normalize_and_store_csv


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.import_csv <csv_path>")
        sys.exit(1)

    csv_path = sys.argv[1]
    # Current date used as reference for relative dates like "1 week ago"
    reference = date(2026, 3, 6)

    app = create_app()
    with app.app_context():
        summary = normalize_and_store_csv(csv_path, reference_date=reference)
        print("Normalization complete:")
        for k, v in summary.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
