# backend/engines/problem_engine.py
# PRISM 2.5 — Enterprise UX Problem Detection Engine

"""
PRISM UX problem detection engine.

Responsibilities:
- friction pattern detection
- UX issue classification
- evidence mapping
- severity estimation
- business impact tagging
- AI output normalization
- fallback resilience
- deterministic validation

This engine DOES NOT:
- generate solutions
- prioritize decisions
- calculate RICE scores

Those responsibilities belong to:
- decision_engine.py
- scoring.py
"""

from typing import Any

from pydantic import ValidationError

from backend.models.schemas import (
    DetectedProblem,
    ProblemEvidence,
    ProblemOutput,
    ProductUnderstanding,
    SimulationOutput
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
# VALID ENUMS
# =========================================================

VALID_PROBLEM_TYPES = {
    "CHECKOUT_COMPLEXITY",
    "NAVIGATION_CONFUSION",
    "DECISION_OVERLOAD",
    "PERFORMANCE_LATENCY",
    "TRUST_SECURITY_CONCERN",
    "ONBOARDING_DROP_OFF",
    "RETENTION_DECLINE"
}

VALID_BUSINESS_IMPACTS = {
    "conversion",
    "retention",
    "acquisition",
    "engagement"
}


# =========================================================
# NORMALIZATION HELPERS
# =========================================================

def normalize_text(
    value: str
) -> str:
    """
    Normalize text safely.
    """

    return (
        value.strip()
        .lower()
    )


def normalize_business_impact(
    value: str
) -> str:
    """
    Normalize hallucinated
    AI business impact values.
    """

    normalized = normalize_text(
        value
    )

    synonym_map = {

        "revenue":
            "conversion",

        "sales":
            "conversion",

        "monetization":
            "conversion",

        "growth":
            "acquisition",

        "user_growth":
            "acquisition",

        "stickiness":
            "retention",

        "subscriptions":
            "retention",

        "trust":
            "engagement",

        "usage":
            "engagement"
    }

    normalized = synonym_map.get(
        normalized,
        normalized
    )

    if (
        normalized
        not in VALID_BUSINESS_IMPACTS
    ):

        LOGGER.warning(
            f"Invalid business impact detected: "
            f"{value}"
        )

        increment_counter(
            "problem_engine_invalid_business_impacts"
        )

        return "engagement"

    return normalized


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are PRISM,
an advanced UX problem detection engine.

Your task:
Analyze behavioral simulations
and identify realistic UX problems.

STRICT RULES:
- Return ONLY valid JSON
- Do NOT wrap JSON in markdown
- No explanations
- No duplicate problems
- No fake analytics
- No invented metrics
- Problems MUST be grounded in evidence
- Business impact MUST use valid enum values

VALID PROBLEM TYPES:
1. CHECKOUT_COMPLEXITY
2. NAVIGATION_CONFUSION
3. DECISION_OVERLOAD
4. PERFORMANCE_LATENCY
5. TRUST_SECURITY_CONCERN
6. ONBOARDING_DROP_OFF
7. RETENTION_DECLINE

VALID BUSINESS IMPACTS:
1. conversion
2. retention
3. acquisition
4. engagement
"""


# =========================================================
# PROMPT BUILDER
# =========================================================

def build_prompt(
    product: ProductUnderstanding,
    simulation: SimulationOutput
) -> str:
    """
    Build AI problem-detection prompt.
    """

    return f"""
{SYSTEM_PROMPT}

PRODUCT:
{product.model_dump_json(indent=2)}

SIMULATION:
{simulation.model_dump_json(indent=2)}

Return STRICT JSON:

{{
  "problems": [
    {{
      "id": "prob_001",
      "problem_type": "NAVIGATION_CONFUSION",
      "description": "Users struggle to locate important onboarding actions.",
      "severity": 7,
      "affected_persona": "first_time_user",
      "evidence": {{
        "persona_type": "first_time_user",
        "journey_step": 2,
        "step_action": "Attempted onboarding",
        "confusion_level": 4,
        "is_drop_off_step": false,
        "drop_off_reason": null
      }},
      "confidence_level": "high",
      "business_impact": "conversion"
    }}
  ]
}}

IMPORTANT:
- Generate between 3 and 6 problems
- Avoid duplicate UX observations
- Problems must map to evidence
- Severity must remain realistic
- High confusion should align with high severity
- Churned users should contribute retention issues
- First-time users should contribute onboarding issues
"""


# =========================================================
# PROBLEM NORMALIZATION
# =========================================================

def normalize_problem(
    problem: DetectedProblem
) -> DetectedProblem:
    """
    Normalize problem safely.
    """

    normalized_severity = max(
        1,
        min(problem.severity, 10)
    )

    normalized_business_impact = (
        normalize_business_impact(
            problem.business_impact
        )
    )

    return problem.model_copy(
        update={

            "severity":
                normalized_severity,

            "business_impact":
                normalized_business_impact
        }
    )


# =========================================================
# OUTPUT NORMALIZATION
# =========================================================

def normalize_problem_output(
    problem_output: ProblemOutput
) -> ProblemOutput:
    """
    Normalize entire problem output.
    """

    normalized_problems = [

        normalize_problem(
            problem
        )

        for problem
        in problem_output.problems
    ]

    return ProblemOutput(
        problems=normalized_problems
    )


# =========================================================
# PROBLEM VALIDATION
# =========================================================

def validate_problem_output(
    problem_output: ProblemOutput
) -> ProblemOutput:
    """
    Validate UX problem integrity.
    """

    validated_problems = []

    seen_problem_ids = set()

    seen_descriptions = set()

    for problem in problem_output.problems:

        # -------------------------------------------------
        # UNIQUE IDS
        # -------------------------------------------------

        if problem.id in seen_problem_ids:

            raise ValueError(
                f"Duplicate problem id: "
                f"{problem.id}"
            )

        seen_problem_ids.add(
            problem.id
        )

        # -------------------------------------------------
        # DEDUPLICATED DESCRIPTIONS
        # -------------------------------------------------

        normalized_description = (
            normalize_text(
                problem.description
            )
        )

        if (
            normalized_description
            in seen_descriptions
        ):

            LOGGER.warning(
                f"Duplicate problem description: "
                f"{problem.description}"
            )

            increment_counter(
                "problem_engine_duplicate_descriptions"
            )

            continue

        seen_descriptions.add(
            normalized_description
        )

        # -------------------------------------------------
        # VALID PROBLEM TYPE
        # -------------------------------------------------

        if (
            problem.problem_type
            not in VALID_PROBLEM_TYPES
        ):

            raise ValueError(
                f"Invalid problem type: "
                f"{problem.problem_type}"
            )

        # -------------------------------------------------
        # PERSONA CONSISTENCY
        # -------------------------------------------------

        if (
            problem.affected_persona
            != problem.evidence.persona_type
        ):

            raise ValueError(
                "Affected persona mismatch"
            )

        # -------------------------------------------------
        # SEVERITY SANITY CHECK
        # -------------------------------------------------

        confusion_level = (
            problem
            .evidence
            .confusion_level
        )

        if (
            confusion_level >= 4
            and problem.severity < 5
        ):

            raise ValueError(
                "Severity too low for high confusion"
            )


        # -------------------------------------------------
        # DESCRIPTION QUALITY
        # -------------------------------------------------

        if (
            len(problem.description.strip())
            < 15
        ):

            raise ValueError(
                "Problem description too short"
            )

        validated_problems.append(
            problem
        )

    if not validated_problems:

        raise ValueError(
            "No valid problems generated"
        )

    return ProblemOutput(
        problems=validated_problems
    )


# =========================================================
# FALLBACK RESPONSE
# =========================================================

def build_fallback_response() -> ProblemOutput:
    """
    Build resilient fallback response.
    """

    LOGGER.warning(
        "Using fallback problem response"
    )

    increment_counter(
        "problem_engine_fallbacks"
    )

    fallback_problem = (

        DetectedProblem(
            id="prob_fallback_001",

            problem_type=
                "NAVIGATION_CONFUSION",

            description=(
                "Reliable UX problem detection "
                "was unavailable for this analysis."
            ),

            severity=3,

            affected_persona=
                "first_time_user",

            evidence=ProblemEvidence(

                persona_type=
                    "first_time_user",

                journey_step=1,

                step_action=
                    "Opened product",

                confusion_level=2,

                is_drop_off_step=False,

                drop_off_reason=None
            ),

            confidence_level="low",

            business_impact=
                "engagement"
        )
    )

    return ProblemOutput(
        problems=[
            fallback_problem
        ]
    )


# =========================================================
# MAIN ENGINE
# =========================================================

async def detect_problems(
    product: ProductUnderstanding,
    simulation: SimulationOutput
) -> ProblemOutput:
    """
    Detect realistic UX problems.
    """

    try:

        LOGGER.info(
            f"Detecting UX problems for: "
            f"{product.product_name}"
        )

        increment_counter(
            "problem_engine_requests"
        )

        # -------------------------------------------------
        # BUILD PROMPT
        # -------------------------------------------------

        prompt = build_prompt(
            product,
            simulation
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
        # OUTPUT NORMALIZATION
        # -------------------------------------------------

        for problem in parsed_output.get(
            "problems",
            []
        ):

            evidence = problem.setdefault(
                "evidence",
                {}
            )

            if evidence.get(
                "persona_type"
            ) is None:

                evidence[
                    "persona_type"
                ] = problem.get(
                    "affected_persona",
                    "first_time_user"
                )

            if evidence.get(
                "journey_step"
            ) is None:

                evidence[
                    "journey_step"
                ] = 1

            if evidence.get(
                "step_action"
            ) is None:

                evidence[
                    "step_action"
                ] = "Unknown action"

            if evidence.get(
                "confusion_level"
            ) is None:

                evidence[
                    "confusion_level"
                ] = 1

            if evidence.get(
                "is_drop_off_step"
            ) is None:

                evidence[
                    "is_drop_off_step"
                ] = False

            if evidence.get(
                "drop_off_reason"
            ) is None:

                evidence[
                    "drop_off_reason"
                ] = None

            if (
                "business_impact"
                in problem
            ):

                problem[
                    "business_impact"
                ] = normalize_business_impact(
                    problem[
                        "business_impact"
                    ]
                )

        # -------------------------------------------------
        # PYDANTIC VALIDATION
        # -------------------------------------------------

        validated_output = (

            ProblemOutput(
                **parsed_output
            )
        )

        # -------------------------------------------------
        # NORMALIZATION
        # -------------------------------------------------

        normalized_output = (
            normalize_problem_output(
                validated_output
            )
        )

        # -------------------------------------------------
        # BUSINESS VALIDATION
        # -------------------------------------------------

        final_output = (
            validate_problem_output(
                normalized_output
            )
        )

        LOGGER.info(
            "Problem detection completed successfully"
        )

        return final_output

    # =====================================================
    # SCHEMA FAILURE
    # =====================================================

    except ValidationError as error:

        increment_counter(
            "problem_engine_validation_failures"
        )

        LOGGER.error(
            f"[problem_engine] "
            f"Schema validation failed: "
            f"{error}"
        )

    # =====================================================
    # ENGINE FAILURE
    # =====================================================

    except Exception as error:

        increment_counter(
            "problem_engine_failures"
        )

        LOGGER.error(
            f"[problem_engine] "
            f"Execution failed: "
            f"{error}"
        )

    # =====================================================
    # FALLBACK
    # =====================================================

    return build_fallback_response()