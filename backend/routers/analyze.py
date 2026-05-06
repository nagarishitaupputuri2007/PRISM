# backend/routers/analyze.py
# PRISM 2.1 — Analysis Pipeline Router

"""
This router orchestrates the complete PRISM pipeline.

Pipeline Flow:
1. Product Understanding
2. Behavioral Simulation
3. Problem Detection
4. Decision Intelligence
5. Final Structured Response

Responsibilities:
- request validation
- pipeline orchestration
- structured logging
- API response consistency
- failure isolation

This router DOES NOT:
- contain AI logic
- calculate scores directly
- perform business reasoning

Those responsibilities belong to:
- engines/
- utils/
"""

import logging
import time

from fastapi import (
    APIRouter,
    HTTPException,
    status
)

from engines.decision_engine import (
    generate_decisions
)
from engines.problem_engine import (
    detect_problems
)
from engines.product_engine import (
    get_product_understanding
)
from engines.simulation_engine import (
    generate_user_simulation
)

from models.schemas import (
    APIResponse,
    AnalyzeRequest,
    PRISMAnalysisResponse
)


# =========================================================
# LOGGER CONFIGURATION
# =========================================================

LOGGER = logging.getLogger(__name__)


# =========================================================
# ROUTER CONFIGURATION
# =========================================================

router = APIRouter(
    prefix="/analyze",
    tags=["PRISM Analysis"]
)


# =========================================================
# ANALYSIS ENDPOINT
# =========================================================

@router.post(
    "",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK
)
async def analyze_product(
    request: AnalyzeRequest
) -> APIResponse:

    pipeline_start = time.perf_counter()

    product_name = (
        request.product_name.strip()
    )

    if not product_name:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "Product name cannot be empty"
            }
        )

    LOGGER.info(
        f"Starting PRISM analysis for: {product_name}"
    )

    try:

        # =================================================
        # STEP 1 — PRODUCT UNDERSTANDING
        # =================================================

        stage_start = time.perf_counter()

        LOGGER.info(
            "Step 1/4 — Product understanding"
        )

        product_output = (
            await get_product_understanding(
                product_name
            )
        )

        LOGGER.info(
            f"Product understanding completed in "
            f"{time.perf_counter() - stage_start:.2f}s"
        )

        # =================================================
        # STEP 2 — USER SIMULATION
        # =================================================

        stage_start = time.perf_counter()

        LOGGER.info(
            "Step 2/4 — Behavioral simulation"
        )

        simulation_output = (
            await generate_user_simulation(
                product_output
            )
        )

        LOGGER.info(
            f"Behavioral simulation completed in "
            f"{time.perf_counter() - stage_start:.2f}s"
        )

        # =================================================
        # STEP 3 — PROBLEM DETECTION
        # =================================================

        stage_start = time.perf_counter()

        LOGGER.info(
            "Step 3/4 — Problem detection"
        )

        problem_output = (
            await detect_problems(
                product_output,
                simulation_output
            )
        )

        LOGGER.info(
            f"Problem detection completed in "
            f"{time.perf_counter() - stage_start:.2f}s"
        )

        # =================================================
        # STEP 4 — DECISION INTELLIGENCE
        # =================================================

        stage_start = time.perf_counter()

        LOGGER.info(
            "Step 4/4 — Decision generation"
        )

        decision_output = (
            await generate_decisions(
                product_output,
                simulation_output,
                problem_output
            )
        )

        LOGGER.info(
            f"Decision generation completed in "
            f"{time.perf_counter() - stage_start:.2f}s"
        )

        # =================================================
        # FINAL RESPONSE ASSEMBLY
        # =================================================

        final_response = (
            PRISMAnalysisResponse(
                product=product_output,
                simulation=simulation_output,
                problems=problem_output,
                decisions=decision_output,
                pipeline_version="2.1"
            )
        )

        total_duration = (
            time.perf_counter() - pipeline_start
        )

        LOGGER.info(
            f"PRISM analysis completed successfully "
            f"for: {product_name} "
            f"in {total_duration:.2f}s"
        )

        return APIResponse(
            status="success",
            data=final_response,
            message="Analysis completed successfully"
        )

    # =====================================================
    # HTTP ERROR HANDLING
    # =====================================================

    except HTTPException:

        raise

    # =====================================================
    # UNEXPECTED PIPELINE FAILURE
    # =====================================================

    except Exception as error:

        LOGGER.exception(
            f"[analyze_router] Pipeline failed: {error}"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": (
                    "PRISM analysis pipeline failed"
                )
            }
        )