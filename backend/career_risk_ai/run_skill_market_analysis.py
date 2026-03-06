from __future__ import annotations

import json

from pipeline.skill_market_analysis import build_skill_market_json


if __name__ == "__main__":
    result = build_skill_market_json(
        batch_size=5000,
        sleep_between_calls=0.05,
    )
    print(json.dumps(result, indent=2))
