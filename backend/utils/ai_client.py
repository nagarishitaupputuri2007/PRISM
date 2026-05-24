# backend/utils/ai_client.py
# PRISM 2.1 — Centralized AI Client (Groq)

import json
import logging
import os
from typing import Any

from dotenv import load_dotenv
from groq import Groq


# =========================================================
# LOGGING CONFIGURATION
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    )
)

LOGGER = logging.getLogger(__name__)


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# GROQ CONFIGURATION
# =========================================================

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY"
)

MODEL_NAME = "llama-3.3-70b-versatile"

TEMPERATURE = 0.2


# =========================================================
# API KEY VALIDATION
# =========================================================

if not GROQ_API_KEY:

    raise ValueError(
        "Missing GROQ_API_KEY in environment variables"
    )

LOGGER.info(
    f"GROQ_API_KEY loaded: {bool(GROQ_API_KEY)}"
)


# =========================================================
# GROQ CLIENT INITIALIZATION
# =========================================================

CLIENT = Groq(
    api_key=GROQ_API_KEY
)

LOGGER.info(
    f"Groq client initialized with model: {MODEL_NAME}"
)


# =========================================================
# CLEAN JSON RESPONSE
# =========================================================

def clean_json_response(
    text: str
) -> str:

    cleaned = text.strip()

    if cleaned.startswith("```json"):

        cleaned = cleaned.removeprefix(
            "```json"
        )

    elif cleaned.startswith("```"):

        cleaned = cleaned.removeprefix(
            "```"
        )

    if cleaned.endswith("```"):

        cleaned = cleaned.removesuffix(
            "```"
        )

    return cleaned.strip()


# =========================================================
# GENERATE RAW TEXT RESPONSE
# =========================================================

def generate_text_response(
    prompt: str
) -> str:

    try:

        LOGGER.info(
            "Sending request to Groq"
        )

        response = CLIENT.chat.completions.create(
            model=MODEL_NAME,
            temperature=TEMPERATURE,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        LOGGER.info(
            "Groq response received"
        )

        raw_output = (
            response
            .choices[0]
            .message
            .content
        )

        if not raw_output:

            LOGGER.error(
                "Groq returned empty response"
            )

            raise ValueError(
                "Empty AI response"
            )

        LOGGER.info(
            f"AI output preview: "
            f"{raw_output[:200]}"
        )

        return raw_output

    except Exception:

        LOGGER.exception(
            "[ai_client] Text generation failed"
        )

        raise


# =========================================================
# GENERATE STRUCTURED JSON RESPONSE
# =========================================================

def generate_json_response(
    prompt: str
) -> dict[str, Any]:

    try:

        raw_output = generate_text_response(
            prompt
        )

        cleaned_output = clean_json_response(
            raw_output
        )

        LOGGER.info(
            f"Cleaned JSON preview: "
            f"{cleaned_output[:200]}"
        )

        parsed_output = json.loads(
            cleaned_output
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

        return parsed_output

    except json.JSONDecodeError:

        LOGGER.exception(
            "[ai_client] JSON parsing failed"
        )

        raise

    except Exception:

        LOGGER.exception(
            "[ai_client] JSON generation failed"
        )

        raise