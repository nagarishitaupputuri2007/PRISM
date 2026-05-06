# backend/engines/product_engine.py
# PRISM 2.1 — Product Understanding Engine

import logging
from typing import Any

from pydantic import ValidationError

from models.schemas import ProductUnderstanding
from utils.ai_client import generate_json_response


# =========================================================
# LOGGER CONFIGURATION
# =========================================================

LOGGER = logging.getLogger(__name__)


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are PRISM, an advanced AI-powered product intelligence system.

Your task:
Analyze digital products and return structured
product understanding in strict JSON format.

RULES:
- Return ONLY valid JSON
- Do NOT wrap JSON in markdown
- No explanations
- No extra commentary
- No hallucinated statistics
- Keep outputs concise and realistic
- Lower confidence when uncertain
"""


# =========================================================
# PROMPT BUILDER
# =========================================================

def build_prompt(
    product_name: str
) -> str:

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
# FALLBACK RESPONSE
# =========================================================

def build_fallback_response(
    product_name: str
) -> ProductUnderstanding:

    LOGGER.warning(
        "Using fallback product understanding response"
    )

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


# =========================================================
# MAIN ENGINE FUNCTION
# =========================================================

async def get_product_understanding(
    product_name: str
) -> ProductUnderstanding:

    try:

        LOGGER.info(
            f"Generating product understanding for: {product_name}"
        )

        # -------------------------------------------------
        # BUILD AI PROMPT
        # -------------------------------------------------

        prompt = build_prompt(
            product_name
        )

        # -------------------------------------------------
        # GENERATE STRUCTURED RESPONSE
        # -------------------------------------------------

        parsed_output: dict[str, Any] = (
            generate_json_response(prompt)
        )

        # -------------------------------------------------
        # PYDANTIC VALIDATION
        # -------------------------------------------------

        validated_output = ProductUnderstanding(
            **parsed_output
        )

        LOGGER.info(
            "Product understanding generated successfully"
        )

        return validated_output

    # =====================================================
    # SCHEMA VALIDATION ERROR
    # =====================================================

    except ValidationError as error:

        LOGGER.error(
            f"[product_engine] Schema validation failed: {error}"
        )

    # =====================================================
    # GENERAL ENGINE ERROR
    # =====================================================

    except Exception as error:

        LOGGER.error(
            f"[product_engine] Engine execution failed: {error}"
        )

    # =====================================================
    # FALLBACK RESPONSE
    # =====================================================

    return build_fallback_response(
        product_name
    )