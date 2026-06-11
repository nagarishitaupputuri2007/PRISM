# backend/routers/analyze.py
# PRISM 2.3 — Production Pipeline Orchestrator

"""
PRISM pipeline orchestration layer.

Responsibilities:
- request validation
- orchestration
- execution tracking
- caching
- structured logging
- pipeline timing
- response formatting
- request tracing

This layer DOES NOT:
- execute AI logic directly
- perform domain reasoning
- calculate scores

Those responsibilities belong to:
- engines/
- utils/
"""

from backend.core.logging import (
    get_logger
)
import time
import uuid
from collections.abc import (
    Awaitable,
    Callable
)
from dataclasses import dataclass
from typing import Any

from fastapi import (
    APIRouter,
    HTTPException,
    status
)

from backend.engines.decision_engine import (
    generate_decisions
)

from backend.engines.problem_engine import (
    detect_problems
)

from backend.engines.root_cause_engine import (
    analyze_root_causes
)

from backend.engines.product_engine import (
    get_product_understanding
)

from backend.engines.simulation_engine import (
    generate_user_simulation
)

from backend.models.schemas import (
    APIResponse,
    AnalyzeRequest,
    PRISMAnalysisResponse
)

from backend.services.cache import (
    get_cache,
    set_cache
)

from backend.core.metrics import (
    track_pipeline_success,
    track_pipeline_failure
)



# =========================================================
# LOGGER CONFIGURATION
# =========================================================

LOGGER = get_logger(__name__)


# =========================================================
# ROUTER CONFIGURATION
# =========================================================

router = APIRouter(
    prefix="/analyze",
    tags=["PRISM Analysis"]
)


# =========================================================
# PIPELINE STAGE MODEL
# =========================================================
@dataclass
class PipelineStage:

    name: str

    handler: Callable[..., Awaitable[Any]]

# =========================================================
# STAGE METRICS MODEL
# =========================================================
@dataclass
class StageMetric:

    stage_name: str

    duration_seconds: float

    success: bool

# =========================================================
# REQUEST ID GENERATOR
# =========================================================

def generate_request_id() -> str:

    return (
        f"req_"
        f"{uuid.uuid4().hex[:8]}"
    )


# =========================================================
# STAGE EXECUTOR
# =========================================================

async def execute_stage(
    request_id: str,
    stage: PipelineStage,
    stage_position: int,
    total_stages: int,
    stage_metrics: list[StageMetric],
    *args: Any
) -> Any:
    """
    Execute pipeline stage with:
    - timing
    - request tracing
    - structured logs
    - reusable orchestration
    """

    LOGGER.info(
        f"[{request_id}] "
        f"[Stage {stage_position}/{total_stages}] "
        f"Starting: {stage.name}"
    )

    stage_start = (
        time.perf_counter()
    )

    try:

        result = await stage.handler(
            *args
        )

        duration = (
            time.perf_counter()
            - stage_start
        )

        stage_metrics.append(
            StageMetric(
                stage_name=stage.name,
                duration_seconds=duration,
                success=True
            )
        )

        LOGGER.info(
            f"[{request_id}] "
            f"[Stage {stage_position}/{total_stages}] "
            f"Completed: {stage.name} "
            f"({duration:.2f}s)"
        )

        return result

    except Exception:

        duration = (
            time.perf_counter()
            - stage_start
        )

        stage_metrics.append(
            StageMetric(
                stage_name=stage.name,
                duration_seconds=duration,
                success=False
            )
        )

        LOGGER.exception(
            f"[{request_id}] "
            f"Stage failed: {stage.name}"
        )

        raise


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

    request_id = (
        generate_request_id()
    )

    pipeline_start = (
        time.perf_counter()
    )

    stage_metrics: list[
        StageMetric
    ] = []

    product_name = (
        request.product_name
        .strip()
    )

    # =====================================================
    # INPUT VALIDATION
    # =====================================================

    if not product_name:

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail={
                "status": "error",
                "message": (
                    "Product name cannot be empty"
                )
            }
        )

    normalized_product = (
        product_name.lower()
    )

    LOGGER.info(
        f"[{request_id}] "
        f"Starting PRISM analysis for: "
        f"{product_name}"
    )

    try:

        # =================================================
        # CACHE CHECK
        # =================================================

        cached_response = get_cache(
            normalized_product
        )

        if cached_response:

            LOGGER.info(
                f"[{request_id}] "
                f"Cache hit for: "
                f"{product_name}"
            )

            total_duration = (
                time.perf_counter()
                - pipeline_start
            )

            track_pipeline_success(
                total_duration
            )

            return APIResponse(
                status="success",
                data=cached_response,
                message=(
                    "Analysis retrieved from cache"
                )
            )
        # =================================================
        # PIPELINE DEFINITION
        # =================================================

        stages = [

            PipelineStage(
                name="Product Understanding",
                handler=get_product_understanding
            ),

            PipelineStage(
                name="Behavioral Simulation",
                handler=generate_user_simulation
            ),

            PipelineStage(
                name="Problem Detection",
                handler=detect_problems
            ),

            PipelineStage(
                name="Root Cause Analysis",
                handler=analyze_root_causes
            ),

            PipelineStage(
                name="Decision Intelligence",
                handler=generate_decisions
            )
        ]

        total_stages = len(
            stages
        )   

        # =================================================
        # STAGE 1 — PRODUCT UNDERSTANDING
        # =================================================

        product_output = (
            await execute_stage(
                request_id,
                stages[0],
                1,
                total_stages,
                stage_metrics,
                product_name
            )
        )

        # =================================================
        # STAGE 2 — USER SIMULATION
        # =================================================

        simulation_output = (
            await execute_stage(
                request_id,
                stages[1],
                2,
                total_stages,
                stage_metrics,
                product_output
            )
        )

        # =================================================
        # STAGE 3 — PROBLEM DETECTION
        # =================================================

        problem_output = (
            await execute_stage(
                request_id,
                stages[2],
                3,
                total_stages,
                stage_metrics,
                product_output,
                simulation_output
            )
        )
        # =================================================
        # STAGE 4 — ROOT CAUSE ANALYSIS
        # =================================================

        root_cause_output = (

            await execute_stage(
                request_id,
                stages[3],
                4,
                total_stages,
                stage_metrics,
                product_output,
                problem_output
            )
        )

        # =================================================
        # STAGE 5 — DECISION GENERATION
        # =================================================

        decision_output = (

            await execute_stage(
                request_id,
                stages[4],
                5,
                total_stages,
                stage_metrics,
                product_output,
                simulation_output,
                problem_output,
                root_cause_output
            )
        )

        # =================================================
        # RESPONSE ASSEMBLY
        # =================================================

        final_response = (
            PRISMAnalysisResponse(
                product=product_output,
                simulation=simulation_output,
                problems=problem_output,
                root_causes=root_cause_output,
                decisions=decision_output,
                pipeline_version="2.5"
            )
        )

        # =================================================
        # CACHE STORAGE
        # =================================================

        set_cache(
            normalized_product,
            final_response
        )

        LOGGER.info(
            f"[{request_id}] "
            f"Analysis cached successfully"
        )

        # =================================================
        # PIPELINE METRICS
        # =================================================

        total_duration = (
            time.perf_counter()
            - pipeline_start
        )

        successful_stages = sum(
            1
            for metric in stage_metrics
            if metric.success
        )

        LOGGER.info(
            f"[{request_id}] "
            f"Pipeline completed successfully"
        )

        LOGGER.info(
            f"[{request_id}] "
            f"Total duration: "
            f"{total_duration:.2f}s"
        )

        LOGGER.info(
            f"[{request_id}] "
            f"Completed stages: "
            f"{successful_stages}/{total_stages}"
        )

        for metric in stage_metrics:

            LOGGER.info(
                f"[{request_id}] "
                f"Metric | "
                f"Stage={metric.stage_name} | "
                f"Duration={metric.duration_seconds:.2f}s | "
                f"Success={metric.success}"
            )

        # =================================================
        # SUCCESS RESPONSE
        # =================================================
        track_pipeline_success(
            total_duration
        )

        return APIResponse(
            status="success",
            data=final_response,
            message=(
                "Analysis completed successfully"
            )
        )

    # =====================================================
    # HTTP FAILURES
    # =====================================================

    except HTTPException:

        raise

    # =====================================================
    # PIPELINE FAILURES
    # =====================================================

    except Exception as error:
        track_pipeline_failure()
        
        LOGGER.exception(
            f"[{request_id}] "
            f"Pipeline failed: {error}"
        )

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail={
                "status": "error",
                "message": (
                    "PRISM analysis pipeline failed"
                )
            }
        )