# backend/engines/decision_engine.py
# PRISM 2.5 — Enterprise Decision Intelligence Engine

"""
PRISM decision intelligence engine.

Responsibilities:
- recommendation generation
- implementation reasoning
- decision traceability
- health dimension estimation
- deterministic scoring integration
- output normalization
- validation hardening
- fallback resilience

This engine DOES NOT:
- calculate raw RICE formulas
- orchestrate pipeline stages

Those responsibilities belong to:
- utils/scoring.py
- routers/analyze.py
"""

from typing import Any

from pydantic import ValidationError

from backend.models.schemas import (
    Decision,
    DecisionOutput,
    DecisionTrace,
    HealthDimensions,
    ProblemOutput,
    ProductUnderstanding,
    SimulationOutput,
    RootCauseOutput
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

from backend.scoring.scoring import (
    attach_scores_to_decisions,
    calculate_health_score,
    normalize_health_dimensions
)


# =========================================================
# LOGGER
# =========================================================

LOGGER = get_logger(__name__)


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are PRISM,
an advanced product decision intelligence engine.

Your task:
Transform validated UX problems
into realistic product recommendations.

STRICT RULES:
- Return ONLY valid JSON
- Do NOT wrap JSON in markdown
- No explanations
- No fake analytics
- No unrealistic impact claims
- No duplicate recommendations
- Every decision MUST map to a problem
- Recommendations must be actionable
- Implementation hints must remain concise

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
    problems: ProblemOutput,
    root_causes: RootCauseOutput
) -> str:
    """
    Build AI decision prompt.
    """

    return f"""
{SYSTEM_PROMPT}

PRODUCT:
{product.model_dump_json(indent=2)}

SIMULATION:
{simulation.model_dump_json(indent=2)}

PROBLEMS:
{problems.model_dump_json(indent=2)}

ROOT CAUSES:
{root_causes.model_dump_json(indent=2)}

Return STRICT JSON:

{{
  "decisions": [
    {{
      "action": "Reduce onboarding fields from 7 to 3",

      "root_cause":
      "Users encounter excessive friction before receiving value",

      "business_outcome":
      "Increase activation rate",

      "success_metric":
      "Activation Rate",

      "decision_rationale":
      "First-time users consistently abandon onboarding before completing account creation",

      "expected_impact":
      "Reduce onboarding abandonment",

      "impact_range":
      "10-20%",

      "impact_type":
      "estimated",

      "effort_level":
      "Medium",

      "reach": 8,

      "impact": 7,

      "confidence": 0.82,

      "effort": 5,

      "confidence_level":
      "high",

      "implementation_hint":
      "Reduce unnecessary setup steps.",

      "trace": {{
        "persona": "first_time_user",
        "step": 2,
        "friction": "Users struggled during onboarding",
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
- Generate between 3 and 6 decisions
- Recommendations must remain realistic
- Avoid duplicate actions
- Effort should align with implementation complexity
- Impact estimates should remain believable
- Health dimensions must stay between 0 and 100
- Every decision must explain the root cause
- Every decision must define a business outcome
- Every decision must define a measurable success metric
- Every decision must include decision rationale
- Root causes must be specific and actionable
- Avoid generic recommendations
- Success metrics must be measurable
- Business outcomes must align with the referenced problem
"""

# =========================================================
# NORMALIZATION HELPERS
# =========================================================

def normalize_action(
    action: str
) -> str:
    """
    Normalize action text.
    """

    return (
        action.strip()
        .lower()
    )


# =========================================================
# DECISION NORMALIZATION
# =========================================================

def normalize_decision(
    decision: Decision
) -> Decision:
    """
    Normalize decision safely.
    """

    normalized_reach = max(
        1.0,
        min(decision.reach, 10.0)
    )

    normalized_impact = max(
        1.0,
        min(decision.impact, 10.0)
    )

    normalized_effort = max(
        1.0,
        min(decision.effort, 10.0)
    )

    normalized_confidence = max(
        0.0,
        min(decision.confidence, 1.0)
    )

    return decision.model_copy(
        update={

            "reach":
                normalized_reach,

            "impact":
                normalized_impact,

            "effort":
                normalized_effort,

            "confidence":
                normalized_confidence
        }
    )


# =========================================================
# OUTPUT NORMALIZATION
# =========================================================

def normalize_decision_output(
    decision_output: DecisionOutput
) -> DecisionOutput:
    """
    Normalize all decisions safely.
    """

    normalized_decisions = [

        normalize_decision(
            decision
        )

        for decision
        in decision_output.decisions
    ]

    normalized_dimensions = None

    if decision_output.health_dimensions:

        normalized_dimensions = (
            normalize_health_dimensions(
                decision_output
                .health_dimensions
            )
        )

    return DecisionOutput(
        decisions=normalized_decisions,
        health_dimensions=normalized_dimensions
    )


# =========================================================
# DECISION VALIDATION
# =========================================================

def validate_decision_output(
    decision_output: DecisionOutput,
    problems: ProblemOutput,
    root_causes: RootCauseOutput
) -> DecisionOutput:
    """
    Validate generated decisions.
    """

    if not decision_output.decisions:

        raise ValueError(
            "No decisions generated"
        )

    if (
        decision_output.health_dimensions
        is None
    ):

        raise ValueError(
            "Health dimensions missing"
        )

    valid_problem_ids = {

        problem.id

        for problem
        in problems.problems
    }
    root_cause_map = {

        root_cause.problem_id:
            root_cause.root_cause

        for root_cause
        in root_causes.root_causes
    }
    seen_actions = set()

    seen_traces = set()

    validated_decisions = []

    for decision in (
        decision_output.decisions
    ):

        # -------------------------------------------------
        # ACTION DEDUPLICATION
        # -------------------------------------------------

        normalized_action = (
            normalize_action(
                decision.action
            )
        )

        if (
            normalized_action
            in seen_actions
        ):

            LOGGER.warning(
                f"Duplicate action removed: "
                f"{decision.action}"
            )

            increment_counter(
                "decision_engine_duplicate_actions"
            )

            continue

        seen_actions.add(
            normalized_action
        )

        # -------------------------------------------------
        # TRACE DEDUPLICATION
        # -------------------------------------------------

        trace_key = (
            decision.trace.problem_id,
            decision.trace.persona,
            decision.trace.step
        )

        if trace_key in seen_traces:

            LOGGER.warning(
                "Duplicate trace removed"
            )

            increment_counter(
                "decision_engine_duplicate_traces"
            )

            continue

        seen_traces.add(
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
                f"Unknown problem id referenced: "
                f"{decision.trace.problem_id}"
            )

        # -------------------------------------------------
        # ACTION QUALITY
        # -------------------------------------------------

        if (
            len(
                decision.action.strip()
            )
            < 12
        ):

            raise ValueError(
                "Decision action too short"
            )
        # -------------------------------------------------
        # ROOT CAUSE QUALITY
        # -------------------------------------------------
        if (
            len(
                decision.root_cause.strip()
            )
            < 15
        ):

            raise ValueError(
                "Root cause too short"
            )
        # -------------------------------------------------
        # BUSINESS OUTCOME QUALITY
        # -------------------------------------------------

        if (
            len(
                decision.business_outcome.strip()
            )
            < 5
        ):

            raise ValueError(
                "Business outcome too short"
            )
        # -------------------------------------------------
        # SUCCESS METRIC QUALITY
        # -------------------------------------------------

        if (
            len(
                decision.success_metric.strip()
            )
            < 3
        ):

            raise ValueError(
                "Success metric too short"
            )
        # -------------------------------------------------
        # DECISION RATIONALE QUALITY
        # -------------------------------------------------

        if (
            len(
                decision.decision_rationale.strip()
            )
            < 15
        ):

            raise ValueError(
                "Decision rationale too short"
            )
        
        # -------------------------------------------------
        # ROOT CAUSE CONSISTENCY
        # -------------------------------------------------

        if (
            decision.trace.problem_id
            not in root_cause_map
        ):

            raise ValueError(
                "Missing root cause mapping"
            )
        # -------------------------------------------------
        # IMPLEMENTATION QUALITY
        # -------------------------------------------------

        if (
            len(
                decision
                .implementation_hint
                .strip()
            )
            < 10
        ):

            raise ValueError(
                "Implementation hint too short"
            )

        # -------------------------------------------------
        # IMPACT RANGE FORMAT
        # -------------------------------------------------

        if "%" not in (
            decision.impact_range
        ):

            raise ValueError(
                "Impact range missing percentage"
            )

        # -------------------------------------------------
        # IMPACT SANITY CHECK
        # -------------------------------------------------

        if (
            decision.impact >= 9
            and decision.effort <= 2
            and decision.confidence >= 0.95
        ):

            raise ValueError(
                "Unrealistic decision scoring"
            )

        # -------------------------------------------------
        # EFFORT CONSISTENCY
        # -------------------------------------------------

        if (
            decision.effort_level == "Low"
            and decision.effort >= 8
        ):

            raise ValueError(
                "Effort level mismatch"
            )

        validated_decisions.append(
            decision
        )

    if not validated_decisions:

        raise ValueError(
            "No valid decisions generated"
        )

    return DecisionOutput(
        decisions=validated_decisions,
        health_dimensions=(
            decision_output
            .health_dimensions
        )
    )


# =========================================================
# FALLBACK RESPONSE
# =========================================================

def build_fallback_response() -> DecisionOutput:
    """
    Build resilient fallback decision response.
    """

    LOGGER.warning(
        "Using fallback decision response"
    )

    increment_counter(
        "decision_engine_fallbacks"
    )

    fallback_decision = (
        Decision(
            action=(
                "Review onboarding and "
                "navigation experience"
            ),

            root_cause=(
                "Insufficient behavioral evidence "
                "was available"
            ),

            business_outcome=(
                "Improve user engagement"
            ),

            success_metric=(
                "Engagement Rate"
            ),

            decision_rationale=(
                "Fallback recommendation generated "
                "due to unavailable decision "
                "intelligence data."
            ),

            expected_impact=(
                "Improve overall user engagement"
            ),

            impact_range="5-10%",

            impact_type="estimated",

            effort_level="Medium",

            reach=5,

            impact=5,

            confidence=0.4,

            effort=5,

            confidence_level="low",

            implementation_hint=(
                "Perform additional UX analysis "
                "before implementation."
            ),

            trace=DecisionTrace(
                persona="first_time_user",

                step=1,

                friction=(
                    "Insufficient behavioral data"
                ),

                problem_id="prob_fallback_001",

                problem_type=
                    "NAVIGATION_CONFUSION"
            )
        )
    )

    fallback_dimensions = (

        HealthDimensions(
            ux=50,
            features=50,
            onboarding=50,
            retention=50,
            trust=50
        )
    )

    scored_decisions = (
        attach_scores_to_decisions(
            [fallback_decision]
        )
    )

    health_score = (
        calculate_health_score(
            fallback_dimensions
        )
    )

    return DecisionOutput(
        decisions=scored_decisions,
        product_health_score=health_score,
        health_dimensions=fallback_dimensions
    )


# =========================================================
# MAIN ENGINE
# =========================================================

async def generate_decisions(
    product: ProductUnderstanding,
    simulation: SimulationOutput,
    problems: ProblemOutput,
    root_causes: RootCauseOutput
) -> DecisionOutput:
    """
    Generate realistic product decisions.
    """

    try:

        LOGGER.info(
            f"Generating decisions for: "
            f"{product.product_name}"
        )

        increment_counter(
            "decision_engine_requests"
        )

        # -------------------------------------------------
        # BUILD PROMPT
        # -------------------------------------------------

        prompt = build_prompt(
            product,
            simulation,
            problems,
            root_causes
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
        # PYDANTIC VALIDATION
        # -------------------------------------------------

        validated_output = (

            DecisionOutput(
                **parsed_output
            )
        )

        # -------------------------------------------------
        # NORMALIZATION
        # -------------------------------------------------

        normalized_output = (
            normalize_decision_output(
                validated_output
            )
        )

        # -------------------------------------------------
        # BUSINESS VALIDATION
        # -------------------------------------------------

        final_output = (
            validate_decision_output(
                normalized_output,
                problems,
                root_causes
            )
        )

        # -------------------------------------------------
        # DETERMINISTIC SCORING
        # -------------------------------------------------

        scored_decisions = (
            attach_scores_to_decisions(
                final_output.decisions
            )
        )

        # -------------------------------------------------
        # HEALTH SCORE
        # -------------------------------------------------

        health_score = None

        if (
            final_output
            .health_dimensions
        ):

            health_score = (

                calculate_health_score(
                    final_output
                    .health_dimensions
                )
            )

        LOGGER.info(
            "Decision generation completed successfully"
        )

        return DecisionOutput(

            decisions=scored_decisions,

            product_health_score=
                health_score,

            health_dimensions=(
                final_output
                .health_dimensions
            )
        )

    # =====================================================
    # SCHEMA FAILURE
    # =====================================================

    except ValidationError as error:

        increment_counter(
            "decision_engine_validation_failures"
        )

        LOGGER.error(
            f"[decision_engine] "
            f"Schema validation failed: "
            f"{error}"
        )

    # =====================================================
    # ENGINE FAILURE
    # =====================================================

    except Exception as error:

        increment_counter(
            "decision_engine_failures"
        )

        LOGGER.error(
            f"[decision_engine] "
            f"Execution failed: "
            f"{error}"
        )

    # =====================================================
    # FALLBACK
    # =====================================================

    return build_fallback_response()