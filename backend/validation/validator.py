# backend/utils/validator.py
# PRISM 2.1 — Business Validation Layer

"""
This module handles business-level validation for AI outputs.

IMPORTANT:
Pydantic validates:
- structure
- types
- ranges

This validator handles:
- logical consistency
- business sanity
- AI quality checks
- response completeness
"""

import logging

from backend.models.schemas import ProductUnderstanding


# =========================================================
# LOGGER CONFIGURATION
# =========================================================

LOGGER = logging.getLogger(__name__)


# =========================================================
# VALIDATION CONSTANTS
# =========================================================

MIN_FEATURE_COUNT = 1
MAX_FEATURE_COUNT = 15

MIN_TARGET_USERS = 1
MAX_TARGET_USERS = 10

MAX_COMPETITORS = 15

MIN_CATEGORY_LENGTH = 2

MIN_VALUE_PROP_LENGTH = 10
MAX_VALUE_PROP_LENGTH = 300


# =========================================================
# CONFIDENCE THRESHOLDS
# =========================================================

CONFIDENCE_THRESHOLDS = {
    "low": 0.30,
    "high": 0.75
}


# =========================================================
# GENERIC TEXT VALIDATOR
# =========================================================

def is_valid_text(
    value: str
) -> bool:

    return (
        isinstance(value, str)
        and bool(value.strip())
    )


# =========================================================
# TEXT NORMALIZER
# =========================================================

def normalize_text(
    value: str
) -> str:

    return (
        value.strip()
        .lower()
    )


# =========================================================
# LIST SANITIZER
# =========================================================

def sanitize_string_list(
    items: list[str],
    max_items: int
) -> list[str]:

    seen = set()

    cleaned_items = []

    for item in items:

        # -------------------------------------------------
        # SKIP INVALID VALUES
        # -------------------------------------------------

        if not is_valid_text(item):
            continue

        normalized = normalize_text(
            item
        )

        # -------------------------------------------------
        # SKIP DUPLICATES
        # -------------------------------------------------

        if normalized in seen:
            continue

        seen.add(
            normalized
        )

        cleaned_items.append(
            item.strip()
        )

    return cleaned_items[:max_items]


# =========================================================
# CONFIDENCE VALIDATION
# =========================================================

def validate_confidence_alignment(
    confidence_score: float,
    confidence_level: str
) -> bool:

    high_threshold = (
        CONFIDENCE_THRESHOLDS["high"]
    )

    low_threshold = (
        CONFIDENCE_THRESHOLDS["low"]
    )

    if confidence_score >= high_threshold:

        return confidence_level == "high"

    if confidence_score >= low_threshold:

        return confidence_level == "medium"

    return confidence_level == "low"


# =========================================================
# PRODUCT UNDERSTANDING VALIDATOR
# =========================================================

def validate_product_understanding(
    product: ProductUnderstanding
) -> ProductUnderstanding:

    LOGGER.info(
        "Running business validation "
        "for product understanding"
    )

    # =====================================================
    # PRODUCT NAME VALIDATION
    # =====================================================

    if not is_valid_text(
        product.product_name
    ):

        raise ValueError(
            "Invalid product name"
        )

    # =====================================================
    # CATEGORY VALIDATION
    # =====================================================

    if (
        not is_valid_text(product.category)
        or len(product.category.strip())
        < MIN_CATEGORY_LENGTH
    ):

        raise ValueError(
            "Invalid product category"
        )

    # =====================================================
    # TARGET USERS VALIDATION
    # =====================================================

    sanitized_target_users = sanitize_string_list(
        product.target_users,
        MAX_TARGET_USERS
    )

    if (
        len(sanitized_target_users)
        < MIN_TARGET_USERS
    ):

        raise ValueError(
            "At least one target user is required"
        )

    # =====================================================
    # CORE FEATURES VALIDATION
    # =====================================================

    sanitized_core_features = sanitize_string_list(
        product.core_features,
        MAX_FEATURE_COUNT
    )

    if (
        len(sanitized_core_features)
        < MIN_FEATURE_COUNT
    ):

        raise ValueError(
            "At least one core feature is required"
        )

    # =====================================================
    # VALUE PROPOSITION VALIDATION
    # =====================================================

    if (
        not is_valid_text(product.value_prop)
        or len(product.value_prop.strip())
        < MIN_VALUE_PROP_LENGTH
        or len(product.value_prop.strip())
        > MAX_VALUE_PROP_LENGTH
    ):

        raise ValueError(
            "Invalid value proposition"
        )

    # =====================================================
    # BUSINESS MODEL VALIDATION
    # =====================================================

    if not is_valid_text(
        product.business_model
    ):

        raise ValueError(
            "Invalid business model"
        )

    # =====================================================
    # COMPETITOR VALIDATION
    # =====================================================

    sanitized_competitors = sanitize_string_list(
        product.competitors,
        MAX_COMPETITORS
    )

    # -----------------------------------------------------
    # PREVENT EMPTY COMPETITOR LIST
    # -----------------------------------------------------

    if not sanitized_competitors:

        sanitized_competitors = [
            "Unknown Competitor"
        ]

    # -----------------------------------------------------
    # AI HALLUCINATION PROTECTION
    # -----------------------------------------------------

    normalized_product_name = normalize_text(
        product.product_name
    )

    for competitor in sanitized_competitors:

        if (
            normalize_text(competitor)
            == normalized_product_name
        ):

            raise ValueError(
                "Product cannot compete with itself"
            )

    # =====================================================
    # CONFIDENCE ALIGNMENT VALIDATION
    # =====================================================

    if not validate_confidence_alignment(
        product.confidence_score,
        product.confidence_level
    ):

        raise ValueError(
            "Confidence score and confidence "
            "level mismatch"
        )

    # =====================================================
    # APPLY SANITIZED VALUES
    # =====================================================

    validated_product = product.model_copy(
        update={
            "target_users": sanitized_target_users,
            "core_features": sanitized_core_features,
            "competitors": sanitized_competitors
        }
    )

    # =====================================================
    # VALIDATION SUMMARY LOGGING
    # =====================================================

    LOGGER.info(
        f"Validated product: "
        f"{product.product_name} | "
        f"Features={len(sanitized_core_features)} | "
        f"Users={len(sanitized_target_users)}"
    )

    # =====================================================
    # SUCCESS
    # =====================================================

    LOGGER.info(
        "Product understanding validation successful"
    )

    return validated_product