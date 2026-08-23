import json
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path(__file__).parent.parent / "logs" / "quarantine.jsonl"


def log_quarantine(input_data: dict, raw_output: str, error: str, prompt_version: str):
    """Appends one JSON line recording a request that failed validation
    even after a repair attempt. Never overwrites previous entries."""
    LOG_PATH.parent.mkdir(exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input": input_data,
        "raw_output": raw_output,
        "error": error,
        "prompt_version": prompt_version
    }

    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
