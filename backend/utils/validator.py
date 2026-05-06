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
from typing import List

from models.schemas import ProductUnderstanding


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

LOW_CONFIDENCE_THRESHOLD = 0.30
HIGH_CONFIDENCE_THRESHOLD = 0.75


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
# LIST SANITIZER
# =========================================================

def sanitize_string_list(
    items: List[str],
    max_items: int
) -> List[str]:

    seen = set()

    cleaned_items = []

    for item in items:

        # Skip invalid entries
        if not is_valid_text(item):
            continue

        normalized = item.strip().lower()

        # Skip duplicates
        if normalized in seen:
            continue

        seen.add(normalized)

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

    if confidence_score >= HIGH_CONFIDENCE_THRESHOLD:
        return confidence_level == "high"

    if confidence_score >= LOW_CONFIDENCE_THRESHOLD:
        return confidence_level == "medium"

    return confidence_level == "low"


# =========================================================
# PRODUCT UNDERSTANDING VALIDATOR
# =========================================================

def validate_product_understanding(
    product: ProductUnderstanding
) -> ProductUnderstanding:

    LOGGER.info(
        "Running business validation for product understanding"
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

    # =====================================================
    # CONFIDENCE ALIGNMENT VALIDATION
    # =====================================================

    if not validate_confidence_alignment(
        product.confidence_score,
        product.confidence_level
    ):

        raise ValueError(
            "Confidence score and confidence level mismatch"
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
    # SUCCESS
    # =====================================================

    LOGGER.info(
        "Product understanding validation successful"
    )

    return validated_product