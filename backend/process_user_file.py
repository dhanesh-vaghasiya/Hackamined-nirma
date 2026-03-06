import json
import os
from pathlib import Path

from app.services.user_input.services.profile_builder import build_profile


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    default_json_dir = base_dir / "data" / "json"
    json_dir = Path(os.getenv("HACKMIND_JSON_DIR", default_json_dir))
    json_dir.mkdir(parents=True, exist_ok=True)

    input_path = json_dir / "user_input.json"
    output_path = json_dir / "processed_output.json"

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. Create user_input.json first."
        )

    with input_path.open("r", encoding="utf-8") as infile:
        data = json.load(infile)

    profile = build_profile(data)

    with output_path.open("w", encoding="utf-8") as outfile:
        json.dump(profile, outfile, indent=2)

    print(f"Processed profile written to {output_path}")


if __name__ == "__main__":
    main()
