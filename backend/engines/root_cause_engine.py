from typing import Any

from pydantic import ValidationError

from backend.models.schemas import (
    ProductUnderstanding,
    ProblemOutput,
    RootCause,
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

LOGGER = get_logger(__name__)

# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are PRISM,
an advanced root cause analysis engine.

Your task:
Analyze validated UX problems and identify
the most likely underlying causes.

STRICT RULES:
- Return ONLY valid JSON
- No markdown
- No explanations
- No duplicate root causes
- Root causes must be evidence-based
- Root causes must be actionable
- Root causes must explain WHY the problem exists
- Keep responses concise and realistic
"""

# =========================================================
# PROMPT BUILDER
# =========================================================

def build_prompt(
    product: ProductUnderstanding,
    problems: ProblemOutput
) -> str:

    return f"""
{SYSTEM_PROMPT}

PRODUCT:

{product.model_dump_json(indent=2)}

PROBLEMS:

{problems.model_dump_json(indent=2)}

Return STRICT JSON:

{{
  "root_causes": [
    {{
      "problem_id": "prob_001",
      "problem_type": "ONBOARDING_DROP_OFF",
      "root_cause": "Users are required to complete too many setup steps before experiencing value.",
      "evidence_summary": "First-time users consistently abandon onboarding after several high-friction actions.",
      "confidence_level": "high"
    }}
  ]
}}

IMPORTANT:
- Generate one root cause for every problem
- problem_id must match the referenced problem
- Root causes must explain WHY the issue occurs
- Avoid generic statements
- Evidence summaries must reference observed behavior
"""

# =========================================================
# NORMALIZATION
# =========================================================

def normalize_root_cause(
    root_cause: RootCause
) -> RootCause:

    return root_cause.model_copy(
        update={

            "root_cause":
                root_cause.root_cause.strip(),

            "evidence_summary":
                root_cause.evidence_summary.strip()
        }
    )

# =========================================================
# OUTPUT NORMALIZATION
# =========================================================

def normalize_root_cause_output(
    output: RootCauseOutput
) -> RootCauseOutput:

    return RootCauseOutput(

        root_causes=[

            normalize_root_cause(
                root_cause
            )

            for root_cause
            in output.root_causes
        ]
    )

# =========================================================
# VALIDATION
# =========================================================

def validate_root_causes(
    output: RootCauseOutput,
    problems: ProblemOutput
) -> RootCauseOutput:
    """
    Validate root cause integrity.
    """

    valid_problem_ids = {

        problem.id

        for problem
        in problems.problems
    }

    problem_type_map = {

        problem.id:
            problem.problem_type

        for problem
        in problems.problems
    }

    seen_problem_ids = set()

    for root_cause in output.root_causes:

        # -------------------------------------------------
        # VALID PROBLEM ID
        # -------------------------------------------------

        if (
            root_cause.problem_id
            not in valid_problem_ids
        ):

            raise ValueError(
                f"Unknown problem id: "
                f"{root_cause.problem_id}"
            )

        # -------------------------------------------------
        # PROBLEM TYPE CONSISTENCY
        # -------------------------------------------------

        if (
            root_cause.problem_type
            != problem_type_map[
                root_cause.problem_id
            ]
        ):

            raise ValueError(
                f"Problem type mismatch for "
                f"{root_cause.problem_id}"
            )

        # -------------------------------------------------
        # DUPLICATE ROOT CAUSE
        # -------------------------------------------------

        if (
            root_cause.problem_id
            in seen_problem_ids
        ):

            raise ValueError(
                f"Duplicate root cause for: "
                f"{root_cause.problem_id}"
            )

        seen_problem_ids.add(
            root_cause.problem_id
        )

        # -------------------------------------------------
        # ROOT CAUSE QUALITY
        # -------------------------------------------------

        if len(
            root_cause.root_cause.strip()
        ) < 15:

            raise ValueError(
                "Root cause too short"
            )

        # -------------------------------------------------
        # EVIDENCE QUALITY
        # -------------------------------------------------

        if len(
            root_cause.evidence_summary.strip()
        ) < 10:

            raise ValueError(
                "Evidence summary too short"
            )

        # -------------------------------------------------
        # ROOT CAUSE SHOULD NOT EQUAL EVIDENCE
        # -------------------------------------------------

        if (
            root_cause.root_cause.strip().lower()
            ==
            root_cause.evidence_summary.strip().lower()
        ):

            raise ValueError(
                "Root cause duplicates evidence"
            )

        # -------------------------------------------------
        # CONFIDENCE VALIDATION
        # -------------------------------------------------

        if (
            root_cause.confidence_level
            not in {
                "high",
                "medium",
                "low"
            }
        ):

            raise ValueError(
                "Invalid confidence level"
            )

    # -----------------------------------------------------
    # COVERAGE CHECK
    # -----------------------------------------------------

    missing_problem_ids = (
        valid_problem_ids
        - seen_problem_ids
    )

    if missing_problem_ids:

        raise ValueError(
            f"Missing root causes for: "
            f"{missing_problem_ids}"
        )

    return output

# =========================================================
# FALLBACK RESPONSE
# =========================================================

def build_fallback_response(
    problems: ProblemOutput
) -> RootCauseOutput:

    LOGGER.warning(
        "Using fallback root cause response"
    )

    increment_counter(
        "root_cause_engine_fallbacks"
    )

    fallback_root_causes = []

    for problem in problems.problems:

        fallback_root_causes.append(

            RootCause(
                problem_id=problem.id,

                problem_type=
                    problem.problem_type,

                root_cause=(
                    "Insufficient evidence "
                    "to determine a reliable "
                    "root cause."
                ),

                evidence_summary=(
                    "Root cause analysis "
                    "was unavailable."
                ),

                confidence_level="low"
            )
        )

    return RootCauseOutput(
        root_causes=fallback_root_causes
    )

# =========================================================
# MAIN ENGINE
# =========================================================

async def analyze_root_causes(
    product: ProductUnderstanding,
    problems: ProblemOutput
) -> RootCauseOutput:
    """
    Generate validated root causes
    for detected UX problems.
    """

    try:

        LOGGER.info(
            f"Generating root causes for: "
            f"{product.product_name}"
        )

        increment_counter(
            "root_cause_engine_requests"
        )

        # ---------------------------------------------
        # BUILD PROMPT
        # ---------------------------------------------

        prompt = build_prompt(
            product,
            problems
        )

        # ---------------------------------------------
        # AI GENERATION
        # ---------------------------------------------

        parsed_output: dict[str, Any] = (
            generate_json_response(
                prompt
            )
        )

        # ---------------------------------------------
        # PYDANTIC VALIDATION
        # ---------------------------------------------

        validated_output = (
            RootCauseOutput(
                **parsed_output
            )
        )

        # ---------------------------------------------
        # NORMALIZATION
        # ---------------------------------------------

        normalized_output = (
            normalize_root_cause_output(
                validated_output
            )
        )

        # ---------------------------------------------
        # BUSINESS VALIDATION
        # ---------------------------------------------

        final_output = (
            validate_root_causes(
                normalized_output,
                problems
            )
        )

        LOGGER.info(
            "Root cause analysis completed successfully"
        )

        return final_output

    # =============================================
    # SCHEMA FAILURE
    # =============================================

    except ValidationError as error:

        increment_counter(
            "root_cause_engine_validation_failures"
        )

        LOGGER.error(
            f"[root_cause_engine] "
            f"Schema validation failed: "
            f"{error}"
        )

    # =============================================
    # ENGINE FAILURE
    # =============================================

    except Exception as error:

        increment_counter(
            "root_cause_engine_failures"
        )

        LOGGER.error(
            f"[root_cause_engine] "
            f"Execution failed: "
            f"{error}"
        )

    # =============================================
    # FALLBACK
    # =============================================

    return build_fallback_response(
        problems
    )