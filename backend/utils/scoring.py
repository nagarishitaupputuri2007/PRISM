# backend/utils/scoring.py
# PRISM 2.1 — Deterministic Scoring Layer

"""
This module contains all deterministic scoring logic for PRISM.

AI is responsible for:
- product reasoning
- persona simulation
- problem discovery
- decision drafting

Python is responsible for:
- RICE scoring
- health score calculation
- decision ranking
- score normalization
"""

import logging
from typing import Sequence

from models.schemas import Decision, HealthDimensions


# =========================================================
# LOGGER CONFIGURATION
# =========================================================

LOGGER = logging.getLogger(__name__)


# =========================================================
# DEFAULT HEALTH WEIGHTS
# =========================================================

DEFAULT_HEALTH_WEIGHTS = {
    "ux": 0.25,
    "features": 0.20,
    "onboarding": 0.20,
    "retention": 0.20,
    "trust": 0.15,
}


# =========================================================
# GENERIC HELPERS
# =========================================================

def clamp(
    value: float,
    minimum: float,
    maximum: float
) -> float:
    """
    Keep a numeric value within a safe range.
    """
    return max(
        minimum,
        min(value, maximum)
    )


def round_score(
    value: float,
    digits: int = 2
) -> float:
    """
    Round scores consistently across the system.
    """
    return round(value, digits)


# =========================================================
# RICE SCORING
# =========================================================

def calculate_rice_score(
    reach: float,
    impact: float,
    confidence: float,
    effort: float
) -> float:
    """
    Calculate deterministic RICE score.

    Formula:
        RICE = (Reach × Impact × Confidence) / Effort
    """

    # -----------------------------------------------------
    # SAFETY NORMALIZATION
    # -----------------------------------------------------

    reach = clamp(reach, 1.0, 10.0)
    impact = clamp(impact, 1.0, 10.0)
    confidence = clamp(confidence, 0.0, 1.0)
    effort = clamp(effort, 1.0, 10.0)

    # -----------------------------------------------------
    # RICE FORMULA
    # -----------------------------------------------------

    rice_score = (
        reach
        * impact
        * confidence
    ) / effort

    return round_score(
        rice_score
    )


# =========================================================
# HEALTH SCORE
# =========================================================

def calculate_health_score(
    dimensions: HealthDimensions,
    weights: dict[str, float] | None = None
) -> float:
    """
    Calculate weighted overall product health score.
    """

    score_weights = (
        weights
        or DEFAULT_HEALTH_WEIGHTS
    )

    total_weight = sum(
        score_weights.values()
    )

    if total_weight <= 0:

        raise ValueError(
            "Health score weights must sum to a positive value"
        )

    weighted_score = (
        dimensions.ux * score_weights["ux"]
        + dimensions.features * score_weights["features"]
        + dimensions.onboarding * score_weights["onboarding"]
        + dimensions.retention * score_weights["retention"]
        + dimensions.trust * score_weights["trust"]
    )

    normalized_score = (
        weighted_score / total_weight
    )

    normalized_score = clamp(
        normalized_score,
        0.0,
        100.0
    )

    return round_score(
        normalized_score
    )


# =========================================================
# HEALTH DIMENSION NORMALIZATION
# =========================================================

def normalize_health_dimensions(
    dimensions: HealthDimensions
) -> HealthDimensions:
    """
    Ensure health dimensions stay within 0-100.
    """

    return dimensions.model_copy(
        update={
            "ux": clamp(dimensions.ux, 0.0, 100.0),
            "features": clamp(dimensions.features, 0.0, 100.0),
            "onboarding": clamp(dimensions.onboarding, 0.0, 100.0),
            "retention": clamp(dimensions.retention, 0.0, 100.0),
            "trust": clamp(dimensions.trust, 0.0, 100.0),
        }
    )


# =========================================================
# DECISION SCORING
# =========================================================

def score_decision(
    decision: Decision
) -> Decision:
    """
    Attach deterministic RICE score
    to a single decision.
    """

    rice_score = calculate_rice_score(
        reach=decision.reach,
        impact=decision.impact,
        confidence=decision.confidence,
        effort=decision.effort
    )

    return decision.model_copy(
        update={
            "rice_score": rice_score
        }
    )


def score_decisions(
    decisions: Sequence[Decision]
) -> list[Decision]:
    """
    Score and rank decisions by descending RICE score.
    """

    scored_decisions = [
        score_decision(decision)
        for decision in decisions
    ]

    # -----------------------------------------------------
    # STABLE SORTING
    # -----------------------------------------------------

    scored_decisions.sort(
        key=lambda item: (
            item.rice_score or 0.0,
            item.confidence
        ),
        reverse=True
    )

    ranked_decisions = []

    for index, decision in enumerate(
        scored_decisions,
        start=1
    ):

        ranked_decisions.append(
            decision.model_copy(
                update={
                    "priority_rank": index
                }
            )
        )

    LOGGER.info(
        "Decision scoring completed successfully"
    )

    return ranked_decisions


# =========================================================
# PUBLIC HELPER
# =========================================================

def attach_scores_to_decisions(
    decisions: Sequence[Decision]
) -> list[Decision]:
    """
    Public scoring helper for engines.

    Responsibilities:
    - score decisions
    - rank decisions
    - return clean immutable output
    """

    return score_decisions(
        decisions
    )