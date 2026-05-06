# backend/models/schemas.py
# PRISM 2.1 — Production Schema Layer

from datetime import datetime, UTC
from typing import List, Optional, Literal

from pydantic import BaseModel, Field, ConfigDict


# =========================================================
# SHARED TYPES
# =========================================================

ConfidenceLevel = Literal[
    "high",
    "medium",
    "low"
]

PersonaType = Literal[
    "first_time_user",
    "power_user",
    "churned_user"
]

EvidenceType = Literal[
    "pattern_based",
    "behavioral",
    "inferred"
]

BusinessImpactType = Literal[
    "conversion",
    "retention",
    "acquisition",
    "engagement"
]

ProblemType = Literal[
    "CHECKOUT_COMPLEXITY",
    "NAVIGATION_CONFUSION",
    "DECISION_OVERLOAD",
    "PERFORMANCE_LATENCY",
    "TRUST_SECURITY_CONCERN",
    "ONBOARDING_DROP_OFF",
    "RETENTION_DECLINE"
]

ImpactType = Literal[
    "benchmark_based",
    "estimated",
    "inferred"
]

EffortLevel = Literal[
    "Low",
    "Medium",
    "High"
]


# =========================================================
# BASE MODEL
# =========================================================

class PRISMBaseModel(BaseModel):

    model_config = ConfigDict(
        extra="ignore",
        validate_assignment=True,
        str_strip_whitespace=True
    )


# =========================================================
# REQUEST MODELS
# =========================================================

class AnalyzeRequest(PRISMBaseModel):

    product_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Name of the product to analyze"
    )


# =========================================================
# PRODUCT UNDERSTANDING
# =========================================================

class ProductUnderstanding(PRISMBaseModel):

    product_name: str = Field(..., min_length=1)

    category: str = Field(..., min_length=1)

    target_users: List[str]

    core_features: List[str]

    value_prop: str = Field(..., min_length=1)

    business_model: str = Field(..., min_length=1)

    competitors: List[str]

    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0
    )

    confidence_level: ConfidenceLevel


# =========================================================
# USER SIMULATION
# =========================================================

class JourneyStep(PRISMBaseModel):

    step: int = Field(
        ...,
        ge=1
    )

    action: str = Field(
        ...,
        min_length=1
    )

    emotion: str = Field(
        ...,
        min_length=1
    )

    confusion_level: int = Field(
        ...,
        ge=1,
        le=5
    )

    time_spent_seconds: int = Field(
        ...,
        ge=0
    )

    confidence_level: ConfidenceLevel

    evidence_type: EvidenceType


class PersonaSimulation(PRISMBaseModel):

    persona: PersonaType

    journey_steps: List[JourneyStep]

    friction_points: List[str]

    drop_off_reason: Optional[str] = None

    satisfaction_score: float = Field(
        ...,
        ge=0.0,
        le=10.0
    )


class SimulationOutput(PRISMBaseModel):

    personas: List[PersonaSimulation]


# =========================================================
# PROBLEM DETECTION
# =========================================================

class ProblemEvidence(PRISMBaseModel):

    persona_type: PersonaType

    journey_step: int = Field(
        ...,
        ge=1
    )

    step_action: str = Field(
        ...,
        min_length=1
    )

    confusion_level: int = Field(
        ...,
        ge=1,
        le=5
    )

    is_drop_off_step: bool

    drop_off_reason: Optional[str] = None


class DetectedProblem(PRISMBaseModel):

    id: str = Field(
        ...,
        min_length=1
    )

    problem_type: ProblemType

    description: str = Field(
        ...,
        min_length=1
    )

    severity: int = Field(
        ...,
        ge=1,
        le=10
    )

    affected_persona: PersonaType

    evidence: ProblemEvidence

    confidence_level: ConfidenceLevel

    business_impact: BusinessImpactType


class ProblemOutput(PRISMBaseModel):

    problems: List[DetectedProblem]


# =========================================================
# DECISION ENGINE
# =========================================================

class DecisionTrace(PRISMBaseModel):

    persona: PersonaType

    step: int = Field(
        ...,
        ge=1
    )

    friction: str = Field(
        ...,
        min_length=1
    )

    problem_id: str = Field(
        ...,
        min_length=1
    )

    problem_type: ProblemType


class Decision(PRISMBaseModel):

    priority_rank: Optional[int] = None

    action: str = Field(
        ...,
        min_length=1
    )

    expected_impact: str = Field(
        ...,
        min_length=1
    )

    impact_range: str = Field(
        ...,
        min_length=1
    )

    impact_type: ImpactType

    effort_level: EffortLevel

    reach: float = Field(
        ...,
        ge=1,
        le=10
    )

    impact: float = Field(
        ...,
        ge=1,
        le=10
    )

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0
    )

    effort: float = Field(
        ...,
        ge=1,
        le=10
    )

    rice_score: Optional[float] = None

    confidence_level: ConfidenceLevel

    implementation_hint: str = Field(
        ...,
        min_length=1
    )

    trace: DecisionTrace


# =========================================================
# HEALTH SCORE
# =========================================================

class HealthDimensions(PRISMBaseModel):

    ux: float = Field(
        ...,
        ge=0,
        le=100
    )

    features: float = Field(
        ...,
        ge=0,
        le=100
    )

    onboarding: float = Field(
        ...,
        ge=0,
        le=100
    )

    retention: float = Field(
        ...,
        ge=0,
        le=100
    )

    trust: float = Field(
        ...,
        ge=0,
        le=100
    )


class DecisionOutput(PRISMBaseModel):

    decisions: List[Decision]

    product_health_score: Optional[float] = None

    health_dimensions: Optional[
        HealthDimensions
    ] = None


# =========================================================
# FINAL RESPONSE
# =========================================================

class PRISMAnalysisResponse(
    PRISMBaseModel
):

    product: ProductUnderstanding

    simulation: SimulationOutput

    problems: ProblemOutput

    decisions: DecisionOutput

    analyzed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    pipeline_version: str = "2.1"


# =========================================================
# API RESPONSE WRAPPER
# =========================================================

class APIResponse(PRISMBaseModel):

    status: Literal[
        "success",
        "error"
    ]

    data: Optional[
        PRISMAnalysisResponse
    ] = None

    message: Optional[str] = None