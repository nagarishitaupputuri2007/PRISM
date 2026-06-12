# backend/engines/simulation_engine.py
# PRISM 2.5 — Enterprise Behavioral Simulation Engine

"""
PRISM Behavioral User Simulation Engine.

Responsibilities:
- behavioral journey simulation
- emotional state generation
- friction discovery
- drop-off reasoning
- UX interaction modeling
- persona normalization
- simulation validation
- fallback resilience

This layer DOES NOT:
- detect UX problems
- calculate scores
- rank decisions
- orchestrate routing

Those responsibilities belong to:
- routers/
- utils/
- downstream engines
"""

from typing import Any

from pydantic import ValidationError

from backend.models.schemas import (
    JourneyStep,
    PersonaSimulation,
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
# REQUIRED PERSONAS
# =========================================================

REQUIRED_PERSONAS = {
    "first_time_user",
    "power_user",
    "churned_user"
}


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
You are PRISM, an advanced behavioral UX simulation system.

Your task:
Simulate realistic user journeys for digital products.

You must generate:
- believable user behavior
- realistic emotions
- logical friction points
- reasonable drop-off causes
- concise UX observations

STRICT RULES:
- Return ONLY valid JSON
- Do NOT wrap JSON in markdown
- No explanations
- No fake analytics
- No invented statistics
- No unrealistic storytelling
- Keep simulations grounded and concise
- Confusion levels must be between 1 and 5
- Satisfaction score must be between 0 and 10

PERSONAS:
1. first_time_user
2. power_user
3. churned_user
"""


# =========================================================
# PROMPT BUILDER
# =========================================================

def build_prompt(
    product: ProductUnderstanding
) -> str:

    return f"""
{SYSTEM_PROMPT}

PRODUCT INFORMATION:

Product Name:
{product.product_name}

Category:
{product.category}

Target Users:
{product.target_users}

Core Features:
{product.core_features}

Value Proposition:
{product.value_prop}

Business Model:
{product.business_model}

Competitors:
{product.competitors}

Return STRICT JSON in this exact structure:

{{
  "personas": [
    {{
      "persona": "first_time_user",
      "journey_steps": [
        {{
          "step": 1,
          "action": "string",
          "emotion": "string",
          "confusion_level": 1,
          "time_spent_seconds": 30,
          "confidence_level": "medium",
          "evidence_type": "behavioral"
        }}
      ],
      "friction_points": [
        "string"
      ],
      "drop_off_reason": "string",
      "satisfaction_score": 5.5
    }}
  ]
}}

IMPORTANT:
- Simulate ALL three personas
- Each persona must appear EXACTLY once
- Journey steps should feel realistic
- Each persona should have 4 to 7 journey steps
- Avoid repetitive emotions
- Friction points must align with journey behavior
- Churned users should demonstrate stronger friction
- Power users should show lower confusion
- First-time users should show onboarding friction
"""


# =========================================================
# PERSONA NORMALIZATION
# =========================================================

def normalize_persona(
    persona: PersonaSimulation
) -> PersonaSimulation:
    """
    Normalize simulation values safely.
    """

    normalized_steps = []

    for step in persona.journey_steps:

        normalized_steps.append(

            step.model_copy(
                update={

                    "confusion_level": max(
                        1,
                        min(
                            step.confusion_level,
                            5
                        )
                    ),

                    "time_spent_seconds": max(
                        1,
                        step.time_spent_seconds
                    )
                }
            )
        )

    satisfaction_score = max(
        0.0,
        min(
            persona.satisfaction_score,
            10.0
        )
    )

    return persona.model_copy(
        update={
            "journey_steps":
                normalized_steps,

            "satisfaction_score":
                satisfaction_score
        }
    )

# =========================================================
# AI OUTPUT NORMALIZATION
# =========================================================

VALID_EVIDENCE_TYPES = {
    "search": "behavioral",
    "creation": "behavioral",
    "interaction": "behavioral",
    "navigation": "behavioral",
    "social": "behavioral",
    "analytics": "behavioral",
    "error": "behavioral",
    "transactional": "behavioral"
}


def normalize_raw_simulation_payload(
    payload: dict[str, Any]
) -> dict[str, Any]:
    """
    Normalize raw AI payload BEFORE schema validation.
    """

    personas = payload.get(
        "personas",
        []
    )

    for persona in personas:

        for step in persona.get(
            "journey_steps",
            []
        ):

            evidence_type = (
                step.get(
                    "evidence_type"
                )
            )

            step[
                "evidence_type"
            ] = (
                VALID_EVIDENCE_TYPES.get(
                    evidence_type,
                    evidence_type
                )
            )

    return payload

# =========================================================
# SIMULATION VALIDATION
# =========================================================

def validate_simulation_output(
    simulation: SimulationOutput
) -> SimulationOutput:
    """
    Validate behavioral simulation integrity.
    """

    personas = {
        persona.persona
        for persona in simulation.personas
    }

    # -----------------------------------------------------
    # REQUIRED PERSONAS
    # -----------------------------------------------------

    missing_personas = (
        REQUIRED_PERSONAS
        - personas
    )

    if missing_personas:

        raise ValueError(
            f"Missing personas: "
            f"{missing_personas}"
        )

    # -----------------------------------------------------
    # DUPLICATE PERSONAS
    # -----------------------------------------------------

    if len(personas) != len(
        simulation.personas
    ):

        raise ValueError(
            "Duplicate personas detected"
        )

    # -----------------------------------------------------
    # JOURNEY VALIDATION
    # -----------------------------------------------------

    for persona in simulation.personas:

        if len(persona.journey_steps) < 4:

            raise ValueError(
                f"{persona.persona} must contain "
                f"at least 4 journey steps"
            )

        # -------------------------------------------------
        # FRICTION VALIDATION
        # -------------------------------------------------

        if len(persona.friction_points) < 1:

            raise ValueError(
                f"{persona.persona} must contain "
                f"at least 1 friction point"
            )

        # -------------------------------------------------
        # CHURN VALIDATION
        # -------------------------------------------------

        if (
            persona.persona
            == "churned_user"
            and not persona.drop_off_reason
        ):

            raise ValueError(
                "Churned user requires "
                "drop_off_reason"
            )

        # -------------------------------------------------
        # STEP VALIDATION
        # -------------------------------------------------

        for step in persona.journey_steps:

            if (
                step.confusion_level < 1
                or step.confusion_level > 5
            ):

                raise ValueError(
                    f"Invalid confusion level "
                    f"for {persona.persona}"
                )

            if step.time_spent_seconds < 1:

                raise ValueError(
                    f"Invalid time spent "
                    f"for {persona.persona}"
                )

    return simulation

# =========================================================
# NORMALIZATION
# =========================================================

def normalize_simulation(
    simulation: SimulationOutput
) -> SimulationOutput:
    """
    Normalize all personas safely.
    """

    normalized_personas = [

        normalize_persona(
            persona
        )

        for persona
        in simulation.personas
    ]

    return SimulationOutput(
        personas=normalized_personas
    )


# =========================================================
# FALLBACK RESPONSE
# =========================================================

def build_fallback_response() -> SimulationOutput:
    """
    Build resilient fallback simulation.
    """

    LOGGER.warning(
        "Using fallback simulation response"
    )

    increment_counter(
        "simulation_engine_fallbacks"
    )

    fallback_step = JourneyStep(
        step=1,
        action="Opened product",
        emotion="neutral",
        confusion_level=2,
        time_spent_seconds=15,
        confidence_level="low",
        evidence_type="inferred"
    )

    fallback_personas = []

    for persona_type in REQUIRED_PERSONAS:

        fallback_personas.append(

            PersonaSimulation(
                persona=persona_type,
                journey_steps=[
                    fallback_step
                ],
                friction_points=[
                    "Limited simulation data"
                ],
                drop_off_reason=(
                    "Simulation unavailable"
                ),
                satisfaction_score=3.0
            )
        )

    return SimulationOutput(
        personas=fallback_personas
    )


# =========================================================
# MAIN ENGINE FUNCTION
# =========================================================

async def generate_user_simulation(
    product: ProductUnderstanding
) -> SimulationOutput:
    """
    Generate behavioral UX simulation.
    """

    try:

        LOGGER.info(
            f"Generating behavioral simulation "
            f"for: {product.product_name}"
        )

        increment_counter(
            "simulation_engine_requests"
        )

        # -------------------------------------------------
        # BUILD PROMPT
        # -------------------------------------------------

        prompt = build_prompt(
            product
        )

        # -------------------------------------------------
        # AI GENERATION
        # -------------------------------------------------

        parsed_output: dict[str, Any] = (
            generate_json_response(
                prompt
            )
        )

        parsed_output = (
            normalize_raw_simulation_payload(
                parsed_output
            )
        )

        # -------------------------------------------------
        # PYDANTIC VALIDATION
        # -------------------------------------------------

        validated_output = (
            SimulationOutput(
                **parsed_output
            )
        )

        # -------------------------------------------------
        # BUSINESS VALIDATION
        # -------------------------------------------------

        validated_output = (
            validate_simulation_output(
                validated_output
            )
        )

        # -------------------------------------------------
        # NORMALIZATION
        # -------------------------------------------------

        normalized_output = (
            normalize_simulation(
                validated_output
            )
        )

        LOGGER.info(
            "Behavioral simulation generated successfully"
        )

        return normalized_output

    # =====================================================
    # VALIDATION FAILURE
    # =====================================================

    except ValidationError as error:

        increment_counter(
            "simulation_engine_validation_failures"
        )

        LOGGER.error(
            f"[simulation_engine] "
            f"Schema validation failed: "
            f"{error}"
        )

    # =====================================================
    # GENERAL FAILURE
    # =====================================================

    except Exception as error:

        increment_counter(
            "simulation_engine_failures"
        )

        LOGGER.error(
            f"[simulation_engine] "
            f"Engine execution failed: "
            f"{error}"
        )

    # =====================================================
    # FALLBACK RESPONSE
    # =====================================================

    return build_fallback_response()