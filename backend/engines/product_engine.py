# backend/engines/product_engine.py
# PRISM 2.1 — Product Understanding Engine

import json
import os
from typing import Any

import google.generativeai as genai
from dotenv import load_dotenv
from pydantic import ValidationError

from models.schemas import ProductUnderstanding

# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

# =========================================================
# GEMINI CONFIGURATION
# =========================================================

genai.configure(
    api_key=os.getenv("GEMINI_API_KEY")
)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash"
)

# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are PRISM, an advanced AI-powered product intelligence system.

Your task is to analyze digital products and return structured
product understanding in strict JSON format.

RULES:
- Return ONLY valid JSON
- No markdown
- No explanations
- No extra commentary
- No hallucinated statistics
- Keep outputs concise and realistic
- Lower confidence when uncertain
"""

# =========================================================
# PROMPT BUILDER
# =========================================================

def build_prompt(product_name: str) -> str:

    return f"""
{SYSTEM_PROMPT}

Analyze the following product:

PRODUCT:
{product_name}

Return STRICT JSON in this exact structure:

{{
  "product_name": "string",
  "category": "string",
  "target_users": ["string"],
  "core_features": ["string"],
  "value_prop": "string",
  "business_model": "string",
  "competitors": ["string"],
  "confidence_score": 0.0,
  "confidence_level": "high"
}}

IMPORTANT:
- confidence_score must be between 0 and 1
- confidence_level must match confidence_score
- If uncertain, reduce confidence
"""

# =========================================================
# CLEAN JSON RESPONSE
# =========================================================

def clean_json_response(text: str) -> str:

    text = text.strip()

    # Remove opening markdown block
    if text.startswith("```json"):
        text = text[7:]

    elif text.startswith("```"):
        text = text[3:]

    # Remove closing markdown block
    if text.endswith("```"):
        text = text[:-3]

    return text.strip()

# =========================================================
# MAIN ENGINE FUNCTION
# =========================================================

async def get_product_understanding(
    product_name: str
) -> ProductUnderstanding:

    try:

        # -------------------------------------------------
        # BUILD PROMPT
        # -------------------------------------------------

        prompt = build_prompt(product_name)

        # -------------------------------------------------
        # GEMINI REQUEST
        # -------------------------------------------------

        response = model.generate_content(
            prompt
        )

        # -------------------------------------------------
        # RAW OUTPUT
        # -------------------------------------------------

        raw_output = response.text

        if not raw_output:
            raise ValueError(
                "Gemini returned empty response"
            )

        # -------------------------------------------------
        # CLEAN RESPONSE
        # -------------------------------------------------

        cleaned_output = clean_json_response(
            raw_output
        )

        # -------------------------------------------------
        # PARSE JSON
        # -------------------------------------------------

        parsed_output: dict[str, Any] = json.loads(
            cleaned_output
        )

        # -------------------------------------------------
        # VALIDATE OUTPUT
        # -------------------------------------------------

        validated_output = ProductUnderstanding(
            **parsed_output
        )

        return validated_output

    # =====================================================
    # JSON ERROR
    # =====================================================

    except json.JSONDecodeError as error:

        print(
            f"[product_engine] JSON parsing error: {error}"
        )

    # =====================================================
    # VALIDATION ERROR
    # =====================================================

    except ValidationError as error:

        print(
            f"[product_engine] Schema validation error: {error}"
        )

    # =====================================================
    # GENERAL ERROR
    # =====================================================

    except Exception as error:

        print(
            f"[product_engine] Unexpected error: {error}"
        )

    # =====================================================
    # FALLBACK RESPONSE
    # =====================================================

    return ProductUnderstanding(
        product_name=product_name,
        category="Unknown",
        target_users=["general users"],
        core_features=["core functionality"],
        value_prop="Analysis unavailable",
        business_model="Unknown",
        competitors=[],
        confidence_score=0.1,
        confidence_level="low"
    )