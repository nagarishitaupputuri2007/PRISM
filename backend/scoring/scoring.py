# backend/utils/scoring.py
# PRISM 2.7 — Enterprise Deterministic Scoring Engine

"""
Deterministic scoring system for PRISM.

Responsibilities:
- RICE scoring
- score normalization
- health scoring
- deterministic ranking
- explainable prioritization
- scoring observability

AI is responsible for:
- reasoning
- simulations
- recommendations

Python is responsible for:
- deterministic scoring
- ranking consistency
- prioritization logic
- normalization
"""

from collections.abc import Sequence

from backend.models.schemas import (
    Decision,
    HealthDimensions
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
# GLOBAL SCORING CONSTANTS
# =========================================================

MIN_SCORE = 0.0

MAX_HEALTH_SCORE = 100.0

MIN_RICE_INPUT = 1.0

MAX_RICE_INPUT = 10.0

DEFAULT_PRECISION = 2


# =========================================================
# HEALTH WEIGHT CONFIGURATION
# =========================================================

DEFAULT_HEALTH_WEIGHTS = {

    "ux": 0.25,

    "features": 0.20,

    "onboarding": 0.20,

    "retention": 0.20,

    "trust": 0.15
}


# =========================================================
# HEALTH WEIGHT VALIDATION
# =========================================================

def validate_health_weights(
    weights: dict[str, float]
) -> None:
    """
    Validate health scoring weights.
    """

    required_keys = {

        "ux",
        "features",
        "onboarding",
        "retention",
        "trust"
    }

    missing_keys = (
        required_keys
        - set(weights.keys())
    )

    if missing_keys:

        raise ValueError(
            f"Missing health weights: "
            f"{missing_keys}"
        )


# =========================================================
# GENERIC HELPERS
# =========================================================

def clamp(
    value: float,
    minimum: float,
    maximum: float
) -> float:
    """
    Keep numeric value within bounds.
    """

    return max(
        minimum,
        min(value, maximum)
    )


def round_score(
    value: float,
    precision: int = DEFAULT_PRECISION
) -> float:
    """
    Standardized score rounding.
    """

    return round(
        value,
        precision
    )


# =========================================================
# SCORE NORMALIZATION
# =========================================================

def normalize_rice_inputs(
    reach: float,
    impact: float,
    confidence: float,
    effort: float
) -> tuple[
    float,
    float,
    float,
    float
]:
    """
    Normalize RICE inputs.
    """

    normalized_reach = clamp(
        reach,
        MIN_RICE_INPUT,
        MAX_RICE_INPUT
    )

    normalized_impact = clamp(
        impact,
        MIN_RICE_INPUT,
        MAX_RICE_INPUT
    )

    normalized_confidence = clamp(
        confidence,
        0.0,
        1.0
    )

    normalized_effort = clamp(
        effort,
        MIN_RICE_INPUT,
        MAX_RICE_INPUT
    )

    return (
        normalized_reach,
        normalized_impact,
        normalized_confidence,
        normalized_effort
    )


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
    Deterministic RICE formula.

    (Reach × Impact × Confidence)
    / Effort
    """

    (
        reach,
        impact,
        confidence,
        effort
    ) = normalize_rice_inputs(
        reach,
        impact,
        confidence,
        effort
    )

    rice_score = (
        reach
        * impact
        * confidence
    ) / effort

    return round_score(
        rice_score
    )


# =========================================================
# HEALTH SCORING
# =========================================================

def calculate_health_score(
    dimensions: HealthDimensions,
    weights: dict[
        str,
        float
    ] | None = None
) -> float:
    """
    Calculate weighted health score.
    """

    scoring_weights = (
        weights
        or DEFAULT_HEALTH_WEIGHTS
    )

    validate_health_weights(
        scoring_weights
    )

    total_weight = sum(
        scoring_weights.values()
    )

    if total_weight <= 0:

        raise ValueError(
            "Health score weights "
            "must sum to a positive value"
        )

    weighted_score = (

        dimensions.ux
        * scoring_weights["ux"]

        + dimensions.features
        * scoring_weights["features"]

        + dimensions.onboarding
        * scoring_weights["onboarding"]

        + dimensions.retention
        * scoring_weights["retention"]

        + dimensions.trust
        * scoring_weights["trust"]
    )

    normalized_score = (
        weighted_score
        / total_weight
    )

    normalized_score = clamp(
        normalized_score,
        MIN_SCORE,
        MAX_HEALTH_SCORE
    )

    return round_score(
        normalized_score
    )


# =========================================================
# HEALTH NORMALIZATION
# =========================================================

def normalize_health_dimensions(
    dimensions: HealthDimensions
) -> HealthDimensions:
    """
    Normalize health dimensions.
    """

    return dimensions.model_copy(
        update={

            "ux": clamp(
                dimensions.ux,
                MIN_SCORE,
                MAX_HEALTH_SCORE
            ),

            "features": clamp(
                dimensions.features,
                MIN_SCORE,
                MAX_HEALTH_SCORE
            ),

            "onboarding": clamp(
                dimensions.onboarding,
                MIN_SCORE,
                MAX_HEALTH_SCORE
            ),

            "retention": clamp(
                dimensions.retention,
                MIN_SCORE,
                MAX_HEALTH_SCORE
            ),

            "trust": clamp(
                dimensions.trust,
                MIN_SCORE,
                MAX_HEALTH_SCORE
            )
        }
    )


# =========================================================
# SINGLE DECISION SCORING
# =========================================================

def score_decision(
    decision: Decision
) -> Decision:
    """
    Attach deterministic RICE score.
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


# =========================================================
# SORTING STRATEGY
# =========================================================

def sort_decisions(
    decisions: list[Decision]
) -> list[Decision]:
    """
    Deterministic ranking strategy.
    """

    return sorted(
        decisions,
        key=lambda item: (

            item.rice_score or 0.0,

            item.confidence,

            item.impact
        ),
        reverse=True
    )


# =========================================================
# PRIORITY ASSIGNMENT
# =========================================================

def assign_priority_ranks(
    decisions: list[Decision]
) -> list[Decision]:
    """
    Assign priority rankings.
    """

    ranked_output = []

    for index, decision in enumerate(
        decisions,
        start=1
    ):

        ranked_output.append(

            decision.model_copy(
                update={
                    "priority_rank": index
                }
            )
        )

    return ranked_output


# =========================================================
# BULK DECISION SCORING
# =========================================================

def score_decisions(
    decisions: Sequence[Decision]
) -> list[Decision]:
    """
    Full deterministic scoring pipeline.
    """

    increment_counter(
        "decision_scoring_requests"
    )

    if not decisions:

        LOGGER.warning(
            "No decisions supplied for scoring"
        )

        return []

    scored_decisions = [

        score_decision(
            decision
        )

        for decision in decisions
    ]

    sorted_decisions = (
        sort_decisions(
            scored_decisions
        )
    )

    ranked_decisions = (
        assign_priority_ranks(
            sorted_decisions
        )
    )

    increment_counter(
        "decision_scoring_completed"
    )

    LOGGER.info(
        f"Decision scoring completed "
        f"for {len(ranked_decisions)} decisions"
    )

    return ranked_decisions


# =========================================================
# PUBLIC API
# =========================================================

def attach_scores_to_decisions(
    decisions: Sequence[Decision]
) -> list[Decision]:
    """
    Public scoring entrypoint.
    """

    return score_decisions(
        decisions
    )