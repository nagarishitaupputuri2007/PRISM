# backend/engines/problem_engine.py
# PRISM 2.1 — UX Problem Detection Engine

"""
This engine converts behavioral simulations
into structured UX and product problems.

Responsibilities:
- friction pattern detection
- UX issue classification
- evidence mapping
- severity estimation
- business impact tagging

This engine DOES NOT:
- generate solutions
- prioritize fixes
- calculate RICE scores
- rank recommendations

Those responsibilities belong to the
decision engine and scoring layer.
"""

import logging
from typing import Any

from pydantic import ValidationError

from models.schemas import (
    DetectedProblem,
    ProblemEvidence,
    ProblemOutput,
    ProductUnderstanding,
    SimulationOutput
)
from utils.ai_client import generate_json_response


# =========================================================
# LOGGER CONFIGURATION
# =========================================================

LOGGER = logging.getLogger(__name__)


# =========================================================
# REQUIRED PROBLEM TYPES
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


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are PRISM, an advanced UX problem detection system.

Your task:
Analyze behavioral user simulations and detect
realistic product and UX problems.

You must:
- identify meaningful friction patterns
- classify problems accurately
- attach evidence
- estimate severity realistically
- connect business impact logically

STRICT RULES:
- Return ONLY valid JSON
- Do NOT wrap JSON in markdown
- No explanations
- No fake analytics
- No invented statistics
- No exaggerated severity
- No duplicate problems
- Problems must be grounded in journey evidence

VALID PROBLEM TYPES:
1. CHECKOUT_COMPLEXITY
2. NAVIGATION_CONFUSION
3. DECISION_OVERLOAD
4. PERFORMANCE_LATENCY
5. TRUST_SECURITY_CONCERN
6. ONBOARDING_DROP_OFF
7. RETENTION_DECLINE
"""


# =========================================================
# PROMPT BUILDER
# =========================================================

def build_prompt(
    product: ProductUnderstanding,
    simulation: SimulationOutput
) -> str:

    return f"""
{SYSTEM_PROMPT}

PRODUCT INFORMATION:

Product Name:
{product.product_name}

Category:
{product.category}

USER SIMULATION DATA:
{simulation.model_dump_json(indent=2)}

Return STRICT JSON in this exact structure:

{{
  "problems": [
    {{
      "id": "prob_001",
      "problem_type": "NAVIGATION_CONFUSION",
      "description": "Users struggle to locate onboarding actions during early setup.",
      "severity": 7,
      "affected_persona": "first_time_user",
      "evidence": {{
        "persona_type": "first_time_user",
        "journey_step": 2,
        "step_action": "Attempted account setup",
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
- Generate 3 to 8 realistic problems
- Problems must directly connect to journey evidence
- Severity must be between 1 and 10
- Avoid duplicate problem descriptions
- Use realistic UX reasoning
- Churned users should contribute retention issues
- First-time users should contribute onboarding issues
- Business impact must logically match the problem
"""


# =========================================================
# DESCRIPTION NORMALIZER
# =========================================================

def normalize_description(
    description: str
) -> str:

    return (
        description
        .strip()
        .lower()
    )


# =========================================================
# PROBLEM VALIDATION
# =========================================================

def validate_problem_output(
    problem_output: ProblemOutput
) -> ProblemOutput:

    seen_problem_ids = set()

    seen_descriptions = set()

    validated_problems = []

    for problem in problem_output.problems:

        # -------------------------------------------------
        # UNIQUE PROBLEM IDS
        # -------------------------------------------------

        if problem.id in seen_problem_ids:

            raise ValueError(
                f"Duplicate problem id detected: {problem.id}"
            )

        seen_problem_ids.add(
            problem.id
        )

        # -------------------------------------------------
        # UNIQUE DESCRIPTIONS
        # -------------------------------------------------

        normalized_description = (
            normalize_description(
                problem.description
            )
        )

        if (
            normalized_description
            in seen_descriptions
        ):

            raise ValueError(
                "Duplicate problem descriptions detected"
            )

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
                f"Invalid problem type: {problem.problem_type}"
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

        # -------------------------------------------------
        # PERSONA CONSISTENCY
        # -------------------------------------------------

        if (
            problem.affected_persona
            != problem.evidence.persona_type
        ):

            raise ValueError(
                "Problem persona mismatch detected"
            )

        # -------------------------------------------------
        # SEVERITY SANITY CHECK
        # -------------------------------------------------

        if (
            problem.severity >= 9
            and problem.evidence.confusion_level <= 2
        ):

            raise ValueError(
                "Severity level appears unrealistic"
            )

        validated_problems.append(
            problem
        )

    return ProblemOutput(
        problems=validated_problems
    )


# =========================================================
# FALLBACK RESPONSE
# =========================================================

def build_fallback_response() -> ProblemOutput:

    LOGGER.warning(
        "Using fallback problem response"
    )

    fallback_problem = DetectedProblem(
        id="prob_fallback_001",
        problem_type="NAVIGATION_CONFUSION",
        description=(
            "Insufficient simulation data prevented "
            "reliable UX problem detection."
        ),
        severity=3,
        affected_persona="first_time_user",
        evidence=ProblemEvidence(
            persona_type="first_time_user",
            journey_step=1,
            step_action="Opened product",
            confusion_level=2,
            is_drop_off_step=False,
            drop_off_reason=None
        ),
        confidence_level="low",
        business_impact="engagement"
    )

    return ProblemOutput(
        problems=[fallback_problem]
    )


# =========================================================
# MAIN ENGINE FUNCTION
# =========================================================

async def detect_problems(
    product: ProductUnderstanding,
    simulation: SimulationOutput
) -> ProblemOutput:

    try:

        LOGGER.info(
            f"Detecting UX problems for: {product.product_name}"
        )

        # -------------------------------------------------
        # BUILD AI PROMPT
        # -------------------------------------------------

        prompt = build_prompt(
            product,
            simulation
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

        validated_output = ProblemOutput(
            **parsed_output
        )

        # -------------------------------------------------
        # BUSINESS VALIDATION
        # -------------------------------------------------

        validated_output = validate_problem_output(
            validated_output
        )

        LOGGER.info(
            "Problem detection completed successfully"
        )

        return validated_output

    # =====================================================
    # SCHEMA VALIDATION ERROR
    # =====================================================

    except ValidationError as error:

        LOGGER.error(
            f"[problem_engine] Schema validation failed: {error}"
        )

    # =====================================================
    # GENERAL ENGINE ERROR
    # =====================================================

    except Exception as error:

        LOGGER.error(
            f"[problem_engine] Engine execution failed: {error}"
        )

    # =====================================================
    # FALLBACK RESPONSE
    # =====================================================

    return build_fallback_response()