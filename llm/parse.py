import json
import re


def strip_markdown_fence(text: str) -> str:
    """Models sometimes wrap JSON in a code fence like ```json ... ```.
    Strip that off if present, otherwise return the text unchanged."""
    match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    return text.strip()


def try_parse_json(text: str):
    """Attempts to parse text as JSON after stripping any markdown fence.
    Returns (parsed_dict, None) on success, or (None, error_message) on failure."""
    cleaned = strip_markdown_fence(text)
    try:
        return json.loads(cleaned), None
    except json.JSONDecodeError as e:
        return None, f"JSON decode error: {e}"
