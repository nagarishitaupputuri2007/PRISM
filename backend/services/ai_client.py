# backend/utils/ai_client.py
# PRISM 2.7 — Enterprise AI Infrastructure Layer

"""
Centralized AI client for PRISM.

Responsibilities:
- AI provider communication
- retry handling
- timeout protection
- deterministic generation
- JSON extraction
- structured logging
- response validation
- observability instrumentation

This layer DOES NOT:
- contain business logic
- contain orchestration
- validate schemas

Those responsibilities belong to:
- engines/
- routers/
- validators/
"""

import json
import os
import re
import time
from typing import Any

from dotenv import load_dotenv

from groq import Groq
from groq import (
    APIConnectionError,
    APIStatusError,
    RateLimitError
)

from backend.core.logging import (
    get_logger
)

from backend.core.metrics import (
    increment_counter,
    record_duration
)


# =========================================================
# LOGGER
# =========================================================

LOGGER = get_logger(__name__)


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# AI CONFIGURATION
# =========================================================

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

MODEL_NAME = (
    "llama-3.3-70b-versatile"
)

TEMPERATURE = 0.0

MAX_RETRIES = 3

INITIAL_RETRY_DELAY = 1.5

MAX_OUTPUT_TOKENS = 4096

REQUEST_TIMEOUT_SECONDS = 60


# =========================================================
# API KEY VALIDATION
# =========================================================

if not GROQ_API_KEY:

    raise ValueError(
        "Missing GROQ_API_KEY in environment variables"
    )

LOGGER.info(
    "GROQ_API_KEY loaded successfully"
)


# =========================================================
# GROQ CLIENT INITIALIZATION
# =========================================================

CLIENT = Groq(
    api_key=GROQ_API_KEY
)

LOGGER.info(
    f"Groq client initialized "
    f"with model: {MODEL_NAME}"
)


# =========================================================
# JSON CLEANER
# =========================================================

def clean_json_response(
    text: str
) -> str:
    """
    Remove markdown wrappers
    from AI responses.
    """

    cleaned = text.strip()

    if cleaned.startswith(
        "```json"
    ):

        cleaned = cleaned.removeprefix(
            "```json"
        )

    elif cleaned.startswith(
        "```"
    ):

        cleaned = cleaned.removeprefix(
            "```"
        )

    if cleaned.endswith(
        "```"
    ):

        cleaned = cleaned.removesuffix(
            "```"
        )

    return cleaned.strip()


# =========================================================
# JSON RECOVERY
# =========================================================

def extract_json_object(
    text: str
) -> str:
    """
    Recover JSON object from malformed output.
    """

    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL
    )

    if not match:

        raise ValueError(
            "No JSON object found in AI response"
        )

    return match.group(0)


# =========================================================
# RESPONSE VALIDATION
# =========================================================

def validate_ai_response(
    response_text: str
) -> None:
    """
    Validate AI response quality.
    """

    if not response_text:

        raise ValueError(
            "AI returned empty response"
        )

    if len(
        response_text.strip()
    ) < 2:

        raise ValueError(
            "AI response too short"
        )


# =========================================================
# AI COMPLETION EXECUTION
# =========================================================

def execute_completion(
    prompt: str
) -> str:
    """
    Execute AI completion request
    with retry protection.
    """

    retry_delay = (
        INITIAL_RETRY_DELAY
    )

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        request_start = (
            time.perf_counter()
        )

        try:

            LOGGER.info(
                f"Sending Groq request "
                f"(attempt {attempt}/{MAX_RETRIES})"
            )

            increment_counter(
                "ai_requests_total"
            )

            response = (
                CLIENT.chat.completions.create(
                    model=MODEL_NAME,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_OUTPUT_TOKENS,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ]
                )
            )

            raw_output = (
                response
                .choices[0]
                .message
                .content
            )

            validate_ai_response(
                raw_output
            )

            request_duration = (
                time.perf_counter()
                - request_start
            )

            record_duration(
                "ai_request_duration_seconds",
                request_duration
            )

            LOGGER.info(
                f"Groq response received "
                f"in {request_duration:.2f}s"
            )

            LOGGER.info(
                f"AI output preview: "
                f"{raw_output[:200]}"
            )

            return raw_output

        # =================================================
        # RETRYABLE FAILURES
        # =================================================

        except (
            RateLimitError,
            APIConnectionError,
            APIStatusError
        ) as error:

            increment_counter(
                "ai_retryable_failures_total"
            )

            LOGGER.warning(
                f"Retryable AI error "
                f"(attempt {attempt}): "
                f"{error}"
            )

            if attempt >= MAX_RETRIES:

                LOGGER.error(
                    "Max retries exhausted"
                )

                increment_counter(
                    "ai_failed_requests_total"
                )

                raise

            LOGGER.info(
                f"Retrying in "
                f"{retry_delay:.1f}s"
            )

            time.sleep(
                retry_delay
            )

            retry_delay *= 2

        # =================================================
        # NON-RETRYABLE FAILURE
        # =================================================

        except Exception:

            increment_counter(
                "ai_failed_requests_total"
            )

            LOGGER.exception(
                "[ai_client] Completion failed"
            )

            raise

    raise RuntimeError(
        "AI request failed unexpectedly"
    )


# =========================================================
# GENERATE TEXT RESPONSE
# =========================================================

def generate_text_response(
    prompt: str
) -> str:
    """
    Generate raw AI response text.
    """

    return execute_completion(
        prompt
    )


# =========================================================
# GENERATE JSON RESPONSE
# =========================================================

def generate_json_response(
    prompt: str
) -> dict[str, Any]:
    """
    Generate structured JSON output
    from AI response.
    """

    try:

        raw_output = (
            generate_text_response(
                prompt
            )
        )

        cleaned_output = (
            clean_json_response(
                raw_output
            )
        )

        LOGGER.info(
            f"Cleaned JSON preview: "
            f"{cleaned_output[:200]}"
        )

        try:

            parsed_output = json.loads(
                cleaned_output
            )

        # =================================================
        # RECOVERY ATTEMPT
        # =================================================

        except json.JSONDecodeError:

            LOGGER.warning(
                "Initial JSON parsing failed. "
                "Attempting recovery."
            )

            increment_counter(
                "ai_json_recovery_attempts_total"
            )

            recovered_json = (
                extract_json_object(
                    cleaned_output
                )
            )

            parsed_output = json.loads(
                recovered_json
            )

        if not isinstance(
            parsed_output,
            dict
        ):

            raise ValueError(
                "AI response is not a JSON object"
            )

        LOGGER.info(
            "Structured JSON generated successfully"
        )

        increment_counter(
            "ai_json_success_total"
        )

        return parsed_output

    except json.JSONDecodeError:

        increment_counter(
            "ai_json_parse_failures_total"
        )

        LOGGER.exception(
            "[ai_client] JSON parsing failed"
        )

        raise

    except Exception:

        increment_counter(
            "ai_json_generation_failures_total"
        )

        LOGGER.exception(
            "[ai_client] JSON generation failed"
        )

        raise