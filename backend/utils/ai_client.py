# backend/utils/ai_client.py
# PRISM 2.1 — Centralized Gemini AI Client

import json
import logging
import os
from typing import Any

import google.generativeai as genai
from dotenv import load_dotenv


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
# GEMINI CONFIGURATION
# =========================================================

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

MODEL_NAME = "models/gemini-1.0-pro"

GENERATION_CONFIG = {
    "temperature": 0.2
}


# =========================================================
# API KEY VALIDATION
# =========================================================

if not GEMINI_API_KEY:

    raise ValueError(
        "Missing GEMINI_API_KEY in environment variables"
    )

LOGGER.info(
    f"GEMINI_API_KEY loaded: {bool(GEMINI_API_KEY)}"
)


# =========================================================
# GEMINI INITIALIZATION
# =========================================================

genai.configure(
    api_key=GEMINI_API_KEY
)

MODEL = genai.GenerativeModel(
    model_name=MODEL_NAME
)

LOGGER.info(
    f"Gemini model initialized: {MODEL_NAME}"
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
            "Sending request to Gemini"
        )

        response = MODEL.generate_content(
            prompt,
            generation_config=GENERATION_CONFIG
        )

        LOGGER.info(
            "Gemini response received"
        )

        raw_output = getattr(
            response,
            "text",
            None
        )

        if not raw_output:

            LOGGER.error(
                f"Empty Gemini response object: {response}"
            )

            raise ValueError(
                "Gemini returned empty response"
            )

        LOGGER.info(
            f"Gemini output preview: "
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