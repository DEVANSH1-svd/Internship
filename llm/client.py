import os
from pathlib import Path
from openai import OpenAI

PROMPT_VERSION = "v1"
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / f"enrich-{PROMPT_VERSION}.md"


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def get_client() -> OpenAI:
    return OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
    )


def call_model(user_input: dict) -> str:
    """Calls the model with the system prompt and the user's data as a
    separate message. Returns the raw text response (not yet parsed/validated —
    that happens in Stage 3)."""
    client = get_client()
    system_prompt = load_prompt()

    response = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": str(user_input)}
        ]
    )

    return response.choices[0].message.content


def call_model_for_repair(user_input: dict, broken_output: str, validation_error: str) -> str:
    """Sends the model its own broken output plus the validation error,
    asking for exactly one corrected version."""
    client = get_client()
    system_prompt = load_prompt()

    repair_message = (
        f"Your previous answer was rejected for this reason: {validation_error}\n\n"
        f"Your previous answer was: {broken_output}\n\n"
        "Return only corrected JSON matching the schema. No explanation, no markdown fence."
    )

    response = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": str(user_input)},
            {"role": "assistant", "content": broken_output},
            {"role": "user", "content": repair_message}
        ]
    )

    return response.choices[0].message.content
