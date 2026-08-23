import os
import time
import random
from pathlib import Path
from openai import OpenAI, APITimeoutError, RateLimitError, APIStatusError

PROMPT_VERSION = "v1"
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / f"enrich-{PROMPT_VERSION}.md"

TIMEOUT_SECONDS = 30.0
MAX_RETRIES = 2


def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def get_client() -> OpenAI:
    return OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
        timeout=TIMEOUT_SECONDS,
        max_retries=0,  # we implement our own retry policy below, not the SDK's default
    )


def _call_with_retries(client, messages):
    """Calls the model with our own retry policy:
    retry on timeout/429/5xx with exponential backoff + jitter,
    never retry on 400/401/403."""
    last_exception = None

    for attempt in range(MAX_RETRIES + 1):
        start = time.monotonic()
        try:
            response = client.chat.completions.create(
                model=os.environ["LLM_MODEL"],
                temperature=0.2,
                messages=messages,
            )
            duration_ms = round((time.monotonic() - start) * 1000, 1)
            return response, duration_ms

        except APITimeoutError as e:
            last_exception = e
            reason = "timeout"
        except RateLimitError as e:
            last_exception = e
            reason = "429 rate limited"
        except APIStatusError as e:
            if 400 <= e.status_code < 500 and e.status_code != 429:
                # 400/401/403/etc - permanent failure, never retry
                raise
            last_exception = e
            reason = f"{e.status_code} server error"

        if attempt < MAX_RETRIES:
            backoff = (2 ** attempt) + random.uniform(0, 0.5)
            print(f"RETRY {attempt + 1}/{MAX_RETRIES} after {reason}, waiting {backoff:.1f}s")
            time.sleep(backoff)

    raise last_exception


def call_model(user_input: dict) -> tuple[str, dict]:
    """Calls the model with the system prompt and the user's data as a
    separate message. Returns (raw_text, call_metadata) where metadata
    includes token counts and duration for cost logging."""
    client = get_client()
    system_prompt = load_prompt()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": str(user_input)}
    ]

    response, duration_ms = _call_with_retries(client, messages)

    metadata = {
        "prompt_version": PROMPT_VERSION,
        "model": os.environ["LLM_MODEL"],
        "input_tokens": response.usage.prompt_tokens if response.usage else None,
        "output_tokens": response.usage.completion_tokens if response.usage else None,
        "duration_ms": duration_ms,
        "repaired": False,
    }

    return response.choices[0].message.content, metadata


def call_model_for_repair(user_input: dict, broken_output: str, validation_error: str) -> tuple[str, dict]:
    """Sends the model its own broken output plus the validation error,
    asking for exactly one corrected version."""
    client = get_client()
    system_prompt = load_prompt()

    repair_message = (
        f"Your previous answer was rejected for this reason: {validation_error}\n\n"
        f"Your previous answer was: {broken_output}\n\n"
        "Return only corrected JSON matching the schema. No explanation, no markdown fence."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": str(user_input)},
        {"role": "assistant", "content": broken_output},
        {"role": "user", "content": repair_message}
    ]

    response, duration_ms = _call_with_retries(client, messages)

    metadata = {
        "prompt_version": PROMPT_VERSION,
        "model": os.environ["LLM_MODEL"],
        "input_tokens": response.usage.prompt_tokens if response.usage else None,
        "output_tokens": response.usage.completion_tokens if response.usage else None,
        "duration_ms": duration_ms,
        "repaired": True,
    }

    return response.choices[0].message.content, metadata