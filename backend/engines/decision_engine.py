# backend/engines/decision_engine.py
# PRISM 2.1 — Product Decision Intelligence Engine

"""
This engine transforms validated UX problems
into structured product decisions.

Responsibilities:
- recommendation generation
- action planning
- implementation guidance
- expected impact reasoning
- traceable decision mapping

This engine DOES NOT:
- calculate RICE scores
- rank decisions
- calculate health scores

Those responsibilities belong to:
utils/scoring.py
"""

import logging
from typing import Any

from pydantic import ValidationError

from models.schemas import (
    Decision,
    DecisionOutput,
    DecisionTrace,
    HealthDimensions,
    ProblemOutput,
    ProductUnderstanding,
    SimulationOutput
)
from utils.ai_client import generate_json_response
from utils.scoring import (
    attach_scores_to_decisions,
    calculate_health_score,
    normalize_health_dimensions
)


# =========================================================
# LOGGER CONFIGURATION
# =========================================================

LOGGER = logging.getLogger(__name__)


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are PRISM, an advanced product decision intelligence system.

Your task:
Convert UX problems into realistic product decisions.

You must:
- generate practical recommendations
- connect decisions directly to problems
- estimate realistic impact
- estimate reasonable implementation effort
- provide concise implementation guidance

STRICT RULES:
- Return ONLY valid JSON
- Do NOT wrap JSON in markdown
- No explanations
- No fake analytics
- No invented statistics
- No unrealistic business claims
- No duplicate decisions
- Every decision must map to a specific problem
- Recommendations must be actionable
- Keep implementation hints concise

IMPORTANT:
- AI DOES NOT calculate RICE scores
- AI DOES NOT assign rankings
- AI ONLY provides structured reasoning
"""


# =========================================================
# PROMPT BUILDER
# =========================================================

def build_prompt(
    product: ProductUnderstanding,
    simulation: SimulationOutput,
    problems: ProblemOutput
) -> str:

    return f"""
{SYSTEM_PROMPT}

PRODUCT INFORMATION:

Product Name:
{product.product_name}

Category:
{product.category}

SIMULATION DATA:
{simulation.model_dump_json(indent=2)}

PROBLEM DATA:
{problems.model_dump_json(indent=2)}

Return STRICT JSON in this exact structure:

{{
  "decisions": [
    {{
      "action": "Simplify onboarding flow into fewer steps",
      "expected_impact": "Reduce onboarding abandonment",
      "impact_range": "10-25%",
      "impact_type": "estimated",
      "effort_level": "Medium",
      "reach": 8,
      "impact": 7,
      "confidence": 0.82,
      "effort": 5,
      "confidence_level": "high",
      "implementation_hint": "Reduce unnecessary setup inputs and add progress indicators.",
      "trace": {{
        "persona": "first_time_user",
        "step": 2,
        "friction": "Users struggled during onboarding setup",
        "problem_id": "prob_001",
        "problem_type": "ONBOARDING_DROP_OFF"
      }}
    }}
  ],
  "health_dimensions": {{
    "ux": 72,
    "features": 80,
    "onboarding": 61,
    "retention": 58,
    "trust": 74
  }}
}}

IMPORTANT:
- Generate 3 to 8 realistic decisions
- Every decision must connect to a problem
- Avoid duplicate recommendations
- Recommendations must be actionable
- Health dimension scores must stay between 0 and 100
- Impact ranges should feel realistic
- Effort levels must align with implementation complexity
"""


# =========================================================
# ACTION NORMALIZER
# =========================================================

def normalize_action(
    action: str
) -> str:

    return (
        action
        .strip()
        .lower()
    )


# =========================================================
# DECISION VALIDATION
# =========================================================

def validate_decision_output(
    decision_output: DecisionOutput,
    problems: ProblemOutput
) -> DecisionOutput:

    if not decision_output.decisions:

        raise ValueError(
            "No decisions generated"
        )

    seen_actions = set()

    seen_problem_traces = set()

    validated_decisions = []

    valid_problem_ids = {
        problem.id
        for problem in problems.problems
    }

    for decision in decision_output.decisions:

        # -------------------------------------------------
        # UNIQUE ACTIONS
        # -------------------------------------------------

        normalized_action = normalize_action(
            decision.action
        )

        if normalized_action in seen_actions:

            raise ValueError(
                "Duplicate decision actions detected"
            )

        seen_actions.add(
            normalized_action
        )

        # -------------------------------------------------
        # TRACE UNIQUENESS
        # -------------------------------------------------

        trace_key = (
            decision.trace.problem_id,
            decision.trace.persona,
            decision.trace.step
        )

        if trace_key in seen_problem_traces:

            raise ValueError(
                "Duplicate decision traces detected"
            )

        seen_problem_traces.add(
            trace_key
        )

        # -------------------------------------------------
        # VALID PROBLEM LINKAGE
        # -------------------------------------------------

        if (
            decision.trace.problem_id
            not in valid_problem_ids
        ):

            raise ValueError(
                f"Decision references unknown problem id: "
                f"{decision.trace.problem_id}"
            )

        # -------------------------------------------------
        # ACTION QUALITY
        # -------------------------------------------------

        if len(decision.action.strip()) < 15:

            raise ValueError(
                "Decision action too short"
            )

        # -------------------------------------------------
        # IMPLEMENTATION QUALITY
        # -------------------------------------------------

        if len(decision.implementation_hint.strip()) < 10:

            raise ValueError(
                "Implementation hint too short"
            )

        # -------------------------------------------------
        # IMPACT RANGE FORMAT
        # -------------------------------------------------

        if "%" not in decision.impact_range:

            raise ValueError(
                "Impact range must contain percentage"
            )

        # -------------------------------------------------
        # IMPACT SANITY VALIDATION
        # -------------------------------------------------

        if (
            decision.impact >= 9
            and decision.effort <= 2
            and decision.confidence >= 0.95
        ):

            raise ValueError(
                "Decision impact appears unrealistic"
            )

        validated_decisions.append(
            decision
        )

    # -----------------------------------------------------
    # HEALTH DIMENSION NORMALIZATION
    # -----------------------------------------------------

    normalized_dimensions = None

    if decision_output.health_dimensions:

        normalized_dimensions = (
            normalize_health_dimensions(
                decision_output.health_dimensions
            )
        )

    return DecisionOutput(
        decisions=validated_decisions,
        health_dimensions=normalized_dimensions
    )


# =========================================================
# FALLBACK RESPONSE
# =========================================================

def build_fallback_response() -> DecisionOutput:

    LOGGER.warning(
        "Using fallback decision response"
    )

    fallback_decision = Decision(
        action="Review onboarding and navigation experience",
        expected_impact="Improve general user engagement",
        impact_range="5-10%",
        impact_type="estimated",
        effort_level="Medium",
        reach=5,
        impact=5,
        confidence=0.4,
        effort=5,
        confidence_level="low",
        implementation_hint=(
            "Perform additional UX analysis before implementation."
        ),
        trace=DecisionTrace(
            persona="first_time_user",
            step=1,
            friction="Insufficient behavioral data",
            problem_id="prob_fallback_001",
            problem_type="NAVIGATION_CONFUSION"
        )
    )

    fallback_dimensions = HealthDimensions(
        ux=50,
        features=50,
        onboarding=50,
        retention=50,
        trust=50
    )

    scored_decisions = attach_scores_to_decisions(
        [fallback_decision]
    )

    health_score = calculate_health_score(
        fallback_dimensions
    )

    return DecisionOutput(
        decisions=scored_decisions,
        product_health_score=health_score,
        health_dimensions=fallback_dimensions
    )


# =========================================================
# MAIN ENGINE FUNCTION
# =========================================================

async def generate_decisions(
    product: ProductUnderstanding,
    simulation: SimulationOutput,
    problems: ProblemOutput
) -> DecisionOutput:

    try:

        LOGGER.info(
            f"Generating decisions for: {product.product_name}"
        )

        # -------------------------------------------------
        # BUILD AI PROMPT
        # -------------------------------------------------

        prompt = build_prompt(
            product,
            simulation,
            problems
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

        validated_output = DecisionOutput(
            **parsed_output
        )

        # -------------------------------------------------
        # BUSINESS VALIDATION
        # -------------------------------------------------

        validated_output = validate_decision_output(
            validated_output,
            problems
        )

        # -------------------------------------------------
        # DETERMINISTIC SCORING
        # -------------------------------------------------

        scored_decisions = (
            attach_scores_to_decisions(
                validated_output.decisions
            )
        )

        # -------------------------------------------------
        # HEALTH SCORE CALCULATION
        # -------------------------------------------------

        health_score = None

        if validated_output.health_dimensions:

            health_score = calculate_health_score(
                validated_output.health_dimensions
            )

        LOGGER.info(
            "Decision generation completed successfully"
        )

        return DecisionOutput(
            decisions=scored_decisions,
            product_health_score=health_score,
            health_dimensions=validated_output.health_dimensions
        )

    # =====================================================
    # SCHEMA VALIDATION ERROR
    # =====================================================

    except ValidationError as error:

        LOGGER.error(
            f"[decision_engine] Schema validation failed: {error}"
        )

    # =====================================================
    # GENERAL ENGINE ERROR
    # =====================================================

    except Exception as error:

        LOGGER.error(
            f"[decision_engine] Engine execution failed: {error}"
        )

    # =====================================================
    # FALLBACK RESPONSE
    # =====================================================

    return build_fallback_response()