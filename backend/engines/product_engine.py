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

from backend.knowledge.product_registry import (
    get_known_product
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
    product_name: str,
    known_product: dict | None
) -> str:
    
    knowledge_context = ""

    if known_product:

        knowledge_context = f"""
    KNOWN PRODUCT DATA:

    Name:
    {known_product["name"]}

    Category:
    {known_product["category"]}
    """

    return f"""
{SYSTEM_PROMPT}

Analyze the following product:
{knowledge_context}

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

    try:

        confidence_score = float(
            payload.get(
                "confidence_score",
                0.5
            )
        )

    except (
        TypeError,
        ValueError
    ):

        confidence_score = 0.5
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
        category="Unverified Product",
        target_users=[
            "general users"
        ],
        core_features=[
            "core functionality",
            "basic service",
            "primary workflow"
        ],
        value_prop="Analysis unavailable",
        business_model="Unknown",
        competitors=[
            "unknown competitor"
        ],
        confidence_score=0.1,
        confidence_level="low"
    )

# =========================================================
# BUSINESS VALIDATION
# =========================================================

def validate_product_understanding(
    product: ProductUnderstanding,
    requested_product: str
) -> ProductUnderstanding:
    """
    Validate generated product understanding.
    """

    # -----------------------------------------------------
    # Confidence threshold
    # -----------------------------------------------------

    if product.confidence_score < 0.30:

        raise ValueError(
            "Confidence score too low"
        )

    # -----------------------------------------------------
    # Category validation
    # -----------------------------------------------------
    if (
        not product.category
        or product.category.lower()
        in {
            "unknown",
            "unverified product"
        }
    ):

        raise ValueError(
            "Invalid category"
        )

    # -----------------------------------------------------
    # Core feature validation
    # -----------------------------------------------------

    if len(product.core_features) < 3:

        raise ValueError(
            "Insufficient core features"
        )

    # -----------------------------------------------------
    # Competitor validation
    # -----------------------------------------------------

    if len(product.competitors) < 1:

        raise ValueError(
            "Insufficient competitors"
        )

    # -----------------------------------------------------
    # Product name validation
    # -----------------------------------------------------

    requested = (
        requested_product
        .strip()
        .lower()
    )

    returned = (
        product.product_name
        .strip()
        .lower()
    )

    if (
        requested not in returned
        and returned not in requested
    ):

        raise ValueError(
            "Product name mismatch"
        )


    return product

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

        known_product = (
            get_known_product(
                product_name
            )
        )

        prompt = build_prompt(
            product_name,
            known_product
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

        validated_output = (
            validate_product_understanding(
                validated_output,
                product_name
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
    # BUSINESS VALIDATION FAILURE
    # =====================================================

    except ValueError as error:

        increment_counter(
            "product_engine_business_validation_failures"
        )

        LOGGER.error(
            f"[product_engine] "
            f"Business validation failed: "
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