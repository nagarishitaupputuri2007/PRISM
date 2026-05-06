# backend/engines/simulation_engine.py
# PRISM 2.1 — Behavioral User Simulation Engine

"""
This engine simulates realistic user journeys
across multiple persona types.

Responsibilities:
- behavioral journey simulation
- emotional state generation
- friction discovery
- drop-off reasoning
- UX interaction modeling

This engine DOES NOT:
- detect problems
- assign severity
- calculate scores
- rank decisions

Those responsibilities belong to later stages
in the PRISM pipeline.
"""

import logging
from typing import Any

from pydantic import ValidationError

from models.schemas import (
    JourneyStep,
    PersonaSimulation,
    ProductUnderstanding,
    SimulationOutput
)
from utils.ai_client import generate_json_response


# =========================================================
# LOGGER CONFIGURATION
# =========================================================

LOGGER = logging.getLogger(__name__)


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
# SIMULATION VALIDATION
# =========================================================

def validate_simulation_output(
    simulation: SimulationOutput
) -> SimulationOutput:

    personas = {
        persona.persona
        for persona in simulation.personas
    }

    # -----------------------------------------------------
    # ENSURE ALL PERSONAS EXIST
    # -----------------------------------------------------

    missing_personas = (
        REQUIRED_PERSONAS - personas
    )

    if missing_personas:

        raise ValueError(
            f"Missing personas: {missing_personas}"
        )

    # -----------------------------------------------------
    # ENSURE NO DUPLICATES
    # -----------------------------------------------------

    if len(personas) != len(
        simulation.personas
    ):

        raise ValueError(
            "Duplicate personas detected"
        )

    return simulation


# =========================================================
# FALLBACK RESPONSE
# =========================================================

def build_fallback_response() -> SimulationOutput:

    LOGGER.warning(
        "Using fallback simulation response"
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
                journey_steps=[fallback_step],
                friction_points=[
                    "Limited simulation data"
                ],
                drop_off_reason="Simulation unavailable",
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

    try:

        LOGGER.info(
            f"Generating behavioral simulation for: {product.product_name}"
        )

        # -------------------------------------------------
        # BUILD AI PROMPT
        # -------------------------------------------------

        prompt = build_prompt(
            product
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

        validated_output = SimulationOutput(
            **parsed_output
        )

        # -------------------------------------------------
        # BUSINESS VALIDATION
        # -------------------------------------------------

        validated_output = validate_simulation_output(
            validated_output
        )

        LOGGER.info(
            "Behavioral simulation generated successfully"
        )

        return validated_output

    # =====================================================
    # SCHEMA VALIDATION ERROR
    # =====================================================

    except ValidationError as error:

        LOGGER.error(
            f"[simulation_engine] Schema validation failed: {error}"
        )

    # =====================================================
    # GENERAL ENGINE ERROR
    # =====================================================

    except Exception as error:

        LOGGER.error(
            f"[simulation_engine] Engine execution failed: {error}"
        )

    # =====================================================
    # FALLBACK RESPONSE
    # =====================================================

    return build_fallback_response()