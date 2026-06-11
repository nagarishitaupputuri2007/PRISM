# backend/engines/product_engine.py
# PRISM 2.5 — Enterprise Product Understanding Engine

"""
PRISM Product Understanding Engine.

Responsibilities:
- product intelligence generation
- structured AI prompting
- response normalization
- schema validation
- confidence normalization
- fallback protection

This layer DOES NOT:
- orchestrate pipeline stages
- perform routing
- calculate scoring

Those responsibilities belong to:
- routers/
- utils/
"""

from typing import Any

from pydantic import ValidationError

from backend.models.schemas import (
    ProductUnderstanding
)

from backend.services.ai_client import (
    generate_json_response
)

from backend.core.logging import (
    get_logger
)

from backend.core.metrics import (
    increment_counter
)


# =========================================================
# LOGGER
# =========================================================

LOGGER = get_logger(__name__)


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
# CONFIDENCE NORMALIZATION
# =========================================================

def normalize_confidence_level(
    confidence_score: float
) -> str:
    """
    Normalize confidence level
    from numeric score.
    """

    if confidence_score >= 0.8:

        return "high"

    if confidence_score >= 0.5:

        return "medium"

    return "low"


# =========================================================
# RESPONSE NORMALIZATION
# =========================================================

def normalize_response(
    payload: dict[str, Any]
) -> dict[str, Any]:
    """
    Normalize AI response safely.
    """

    confidence_score = float(
        payload.get(
            "confidence_score",
            0.5
        )
    )

    confidence_score = max(
        0.0,
        min(confidence_score, 1.0)
    )

    payload[
        "confidence_score"
    ] = confidence_score

    payload[
        "confidence_level"
    ] = normalize_confidence_level(
        confidence_score
    )

    return payload


# =========================================================
# FALLBACK RESPONSE
# =========================================================

def build_fallback_response(
    product_name: str
) -> ProductUnderstanding:
    """
    Build safe fallback response.
    """

    LOGGER.warning(
        "Using fallback product understanding response"
    )

    increment_counter(
        "product_engine_fallbacks"
    )

    return ProductUnderstanding(
        product_name=product_name,
        category="Unknown",
        target_users=[
            "general users"
        ],
        core_features=[
            "core functionality"
        ],
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
    """
    Generate structured product understanding.
    """

    try:

        LOGGER.info(
            f"Generating product understanding "
            f"for: {product_name}"
        )

        increment_counter(
            "product_engine_requests"
        )

        # -------------------------------------------------
        # BUILD PROMPT
        # -------------------------------------------------

        prompt = build_prompt(
            product_name
        )

        # -------------------------------------------------
        # AI GENERATION
        # -------------------------------------------------

        parsed_output: dict[str, Any] = (
            generate_json_response(
                prompt
            )
        )

        # -------------------------------------------------
        # NORMALIZATION
        # -------------------------------------------------

        normalized_output = (
            normalize_response(
                parsed_output
            )
        )

        # -------------------------------------------------
        # PYDANTIC VALIDATION
        # -------------------------------------------------

        validated_output = (
            ProductUnderstanding(
                **normalized_output
            )
        )

        LOGGER.info(
            "Product understanding generated successfully"
        )

        return validated_output

    # =====================================================
    # VALIDATION FAILURE
    # =====================================================

    except ValidationError as error:

        increment_counter(
            "product_engine_validation_failures"
        )

        LOGGER.error(
            f"[product_engine] "
            f"Schema validation failed: "
            f"{error}"
        )

    # =====================================================
    # GENERAL FAILURE
    # =====================================================

    except Exception as error:

        increment_counter(
            "product_engine_failures"
        )

        LOGGER.error(
            f"[product_engine] "
            f"Engine execution failed: "
            f"{error}"
        )

    # =====================================================
    # FALLBACK RESPONSE
    # =====================================================

    return build_fallback_response(
        product_name
    )