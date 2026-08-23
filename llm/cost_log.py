import json
from pathlib import Path

LOG_PATH = Path(__file__).parent.parent / "logs" / "cost_log.jsonl"


def log_cost(metadata: dict):
    """Appends one structured JSON line per model call, per Stage 4's
    requirement: prompt version, model, token counts, duration, repair flag."""
    LOG_PATH.parent.mkdir(exist_ok=True)

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(metadata) + "\n")
