# backend/utils/performance.py
# PRISM 2.5 — Enterprise Performance Infrastructure

"""
Centralized performance infrastructure for PRISM.

Responsibilities:
- async timeout protection
- stage timing
- performance tracking
- bottleneck detection
- execution profiling
- orchestration observability

This layer DOES NOT:
- execute AI logic
- contain routing logic
- perform business reasoning

Those responsibilities belong to:
- routers/
- engines/
- utils/
"""

import asyncio
import time
from collections.abc import Awaitable
from dataclasses import (
    dataclass,
    field
)
from typing import Any

from backend.core.logging import (
    get_logger
)

from backend.core.metrics import (
    add_duration,
    increment_counter
)


# =========================================================
# LOGGER
# =========================================================

LOGGER = get_logger(__name__)


# =========================================================
# PERFORMANCE CONFIGURATION
# =========================================================

DEFAULT_STAGE_TIMEOUT_SECONDS = 90

SLOW_STAGE_THRESHOLD_SECONDS = 5.0


# =========================================================
# STAGE PERFORMANCE MODEL
# =========================================================

@dataclass
class StagePerformance:

    stage_name: str

    duration_seconds: float

    success: bool

    timed_out: bool = False

    error_message: str | None = None


# =========================================================
# PIPELINE PERFORMANCE MODEL
# =========================================================

@dataclass
class PipelinePerformanceTracker:

    started_at: float = field(
        default_factory=time.perf_counter
    )

    completed_stages: list[
        StagePerformance
    ] = field(
        default_factory=list
    )

    # -----------------------------------------------------
    # SUCCESSFUL STAGE
    # -----------------------------------------------------

    def add_successful_stage(
        self,
        stage_name: str,
        duration_seconds: float
    ) -> None:

        performance = StagePerformance(
            stage_name=stage_name,
            duration_seconds=duration_seconds,
            success=True
        )

        self.completed_stages.append(
            performance
        )

        increment_counter(
            "successful_stages"
        )

        add_duration(
            "total_stage_time",
            duration_seconds
        )

        LOGGER.info(
            f"[Performance] "
            f"{stage_name} completed "
            f"in {duration_seconds:.2f}s"
        )

        if (
            duration_seconds
            >= SLOW_STAGE_THRESHOLD_SECONDS
        ):

            LOGGER.warning(
                f"[Performance] "
                f"Slow stage detected: "
                f"{stage_name} "
                f"({duration_seconds:.2f}s)"
            )

    # -----------------------------------------------------
    # FAILED STAGE
    # -----------------------------------------------------

    def add_failed_stage(
        self,
        stage_name: str,
        duration_seconds: float,
        error_message: str
    ) -> None:

        performance = StagePerformance(
            stage_name=stage_name,
            duration_seconds=duration_seconds,
            success=False,
            error_message=error_message
        )

        self.completed_stages.append(
            performance
        )

        increment_counter(
            "failed_stages"
        )

        LOGGER.error(
            f"[Performance] "
            f"{stage_name} failed "
            f"after {duration_seconds:.2f}s"
        )

    # -----------------------------------------------------
    # TIMEOUT STAGE
    # -----------------------------------------------------

    def add_timeout_stage(
        self,
        stage_name: str,
        duration_seconds: float
    ) -> None:

        performance = StagePerformance(
            stage_name=stage_name,
            duration_seconds=duration_seconds,
            success=False,
            timed_out=True,
            error_message="Stage timeout exceeded"
        )

        self.completed_stages.append(
            performance
        )

        increment_counter(
            "timed_out_stages"
        )

        LOGGER.error(
            f"[Performance] "
            f"{stage_name} timed out "
            f"after {duration_seconds:.2f}s"
        )

    # -----------------------------------------------------
    # TOTAL DURATION
    # -----------------------------------------------------

    @property
    def total_duration_seconds(
        self
    ) -> float:

        return (
            time.perf_counter()
            - self.started_at
        )

    # -----------------------------------------------------
    # PERFORMANCE SUMMARY
    # -----------------------------------------------------

    def build_summary(
        self
    ) -> dict[str, Any]:

        successful_stages = sum(
            1
            for stage
            in self.completed_stages
            if stage.success
        )

        failed_stages = sum(
            1
            for stage
            in self.completed_stages
            if not stage.success
        )

        timed_out_stages = sum(
            1
            for stage
            in self.completed_stages
            if stage.timed_out
        )

        slowest_stage = None

        if self.completed_stages:

            slowest_stage = max(
                self.completed_stages,
                key=lambda stage: (
                    stage.duration_seconds
                )
            )

        return {

            "total_duration_seconds": round(
                self.total_duration_seconds,
                2
            ),

            "total_stages": len(
                self.completed_stages
            ),

            "successful_stages":
                successful_stages,

            "failed_stages":
                failed_stages,

            "timed_out_stages":
                timed_out_stages,

            "slowest_stage": (

                {
                    "stage_name":
                        slowest_stage.stage_name,

                    "duration_seconds":
                        round(
                            slowest_stage
                            .duration_seconds,
                            2
                        )
                }

                if slowest_stage
                else None
            ),

            "stages": [

                {
                    "stage_name":
                        stage.stage_name,

                    "duration_seconds":
                        round(
                            stage
                            .duration_seconds,
                            2
                        ),

                    "success":
                        stage.success,

                    "timed_out":
                        stage.timed_out,

                    "error_message":
                        stage.error_message
                }

                for stage
                in self.completed_stages
            ]
        }


# =========================================================
# TIMEOUT EXECUTOR
# =========================================================

async def execute_with_timeout(
    coroutine: Awaitable[Any],
    timeout_seconds: int = (
        DEFAULT_STAGE_TIMEOUT_SECONDS
    )
) -> Any:
    """
    Execute async coroutine
    with timeout protection.
    """

    return await asyncio.wait_for(
        coroutine,
        timeout=timeout_seconds
    )


# =========================================================
# TRACKED STAGE EXECUTION
# =========================================================

async def execute_tracked_stage(
    tracker: PipelinePerformanceTracker,
    stage_name: str,
    coroutine: Awaitable[Any],
    timeout_seconds: int = (
        DEFAULT_STAGE_TIMEOUT_SECONDS
    )
) -> Any:
    """
    Execute tracked pipeline stage with:
    - timeout protection
    - structured logging
    - performance tracking
    """

    stage_start = (
        time.perf_counter()
    )

    try:

        LOGGER.info(
            f"[Performance] "
            f"Executing stage: "
            f"{stage_name}"
        )

        result = await execute_with_timeout(
            coroutine,
            timeout_seconds
        )

        duration = (
            time.perf_counter()
            - stage_start
        )

        tracker.add_successful_stage(
            stage_name,
            duration
        )

        return result

    # -----------------------------------------------------
    # TIMEOUT FAILURE
    # -----------------------------------------------------

    except asyncio.TimeoutError:

        duration = (
            time.perf_counter()
            - stage_start
        )

        tracker.add_timeout_stage(
            stage_name,
            duration
        )

        raise TimeoutError(
            f"{stage_name} exceeded "
            f"{timeout_seconds}s timeout"
        )

    # -----------------------------------------------------
    # GENERAL FAILURE
    # -----------------------------------------------------

    except Exception as error:

        duration = (
            time.perf_counter()
            - stage_start
        )

        tracker.add_failed_stage(
            stage_name,
            duration,
            str(error)
        )

        raise