# backend/models/schemas.py
# PRISM 2.2 — Enterprise Schema Layer

from datetime import (
    UTC,
    datetime
)
from enum import Enum
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator
)


# =========================================================
# ENUM TYPES
# =========================================================

class ConfidenceLevel(
    str,
    Enum
):

    HIGH = "high"

    MEDIUM = "medium"

    LOW = "low"


class PersonaType(
    str,
    Enum
):

    FIRST_TIME_USER = (
        "first_time_user"
    )

    POWER_USER = (
        "power_user"
    )

    CHURNED_USER = (
        "churned_user"
    )


class EvidenceType(
    str,
    Enum
):

    PATTERN_BASED = (
        "pattern_based"
    )

    BEHAVIORAL = (
        "behavioral"
    )

    INFERRED = (
        "inferred"
    )


class BusinessImpactType(
    str,
    Enum
):

    CONVERSION = (
        "conversion"
    )

    RETENTION = (
        "retention"
    )

    ACQUISITION = (
        "acquisition"
    )

    ENGAGEMENT = (
        "engagement"
    )


class ProblemType(
    str,
    Enum
):

    CHECKOUT_COMPLEXITY = (
        "CHECKOUT_COMPLEXITY"
    )

    NAVIGATION_CONFUSION = (
        "NAVIGATION_CONFUSION"
    )

    DECISION_OVERLOAD = (
        "DECISION_OVERLOAD"
    )

    PERFORMANCE_LATENCY = (
        "PERFORMANCE_LATENCY"
    )

    TRUST_SECURITY_CONCERN = (
        "TRUST_SECURITY_CONCERN"
    )

    ONBOARDING_DROP_OFF = (
        "ONBOARDING_DROP_OFF"
    )

    RETENTION_DECLINE = (
        "RETENTION_DECLINE"
    )


class ImpactType(
    str,
    Enum
):

    BENCHMARK_BASED = (
        "benchmark_based"
    )

    ESTIMATED = (
        "estimated"
    )

    INFERRED = (
        "inferred"
    )


class EffortLevel(
    str,
    Enum
):

    LOW = "Low"

    MEDIUM = "Medium"

    HIGH = "High"


# =========================================================
# BASE MODEL
# =========================================================

class PRISMBaseModel(
    BaseModel
):

    model_config = ConfigDict(
        extra="ignore",
        validate_assignment=True,
        str_strip_whitespace=True,
        use_enum_values=True,
        populate_by_name=True
    )


# =========================================================
# REQUEST MODELS
# =========================================================

class AnalyzeRequest(
    PRISMBaseModel
):

    product_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description=(
            "Name of the product "
            "to analyze"
        ),
        examples=["Spotify"]
    )

# =========================================================
# PRODUCT VERIFICATION
# =========================================================

class ProductVerification(
    PRISMBaseModel
):

    verified: bool

    canonical_name: str = Field(
        ...,
        min_length=1
    )

    category: str = Field(
        ...,
        min_length=1
    )

    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0
    )

    verification_reason: str = Field(
        ...,
        min_length=5
    )

# =========================================================
# PRODUCT UNDERSTANDING
# =========================================================

class ProductUnderstanding(
    PRISMBaseModel
):

    product_name: str = Field(
        ...,
        min_length=1
    )

    category: str = Field(
        ...,
        min_length=1
    )

    target_users: list[str]

    core_features: list[str]

    value_prop: str = Field(
        ...,
        min_length=1
    )

    business_model: str = Field(
        ...,
        min_length=1
    )

    competitors: list[str]

    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0
    )

    confidence_level: ConfidenceLevel

    @field_validator(
        "target_users",
        "core_features",
        "competitors"
    )
    @classmethod
    def validate_non_empty_lists(
        cls,
        value: list[str]
    ) -> list[str]:

        if not value:

            raise ValueError(
                "List cannot be empty"
            )

        return value


# =========================================================
# USER SIMULATION
# =========================================================

class JourneyStep(
    PRISMBaseModel
):

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


class PersonaSimulation(
    PRISMBaseModel
):

    persona: PersonaType

    journey_steps: list[
        JourneyStep
    ]

    friction_points: list[str]

    drop_off_reason: (
        Optional[str]
    ) = None

    satisfaction_score: float = Field(
        ...,
        ge=0.0,
        le=10.0
    )

    @field_validator(
        "journey_steps"
    )
    @classmethod
    def validate_journey_steps(
        cls,
        value: list[JourneyStep]
    ) -> list[JourneyStep]:

        if not value:

            raise ValueError(
                "Journey steps cannot be empty"
            )

        return value


class SimulationOutput(
    PRISMBaseModel
):

    personas: list[
        PersonaSimulation
    ]


# =========================================================
# PROBLEM DETECTION
# =========================================================

class ProblemEvidence(
    PRISMBaseModel
):

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

    drop_off_reason: (
        Optional[str]
    ) = None


class DetectedProblem(
    PRISMBaseModel
):

    id: str = Field(
        ...,
        min_length=1
    )

    problem_type: ProblemType

    description: str = Field(
        ...,
        min_length=10
    )

    severity: int = Field(
        ...,
        ge=1,
        le=10
    )

    affected_persona: PersonaType

    evidence: ProblemEvidence

    confidence_level: ConfidenceLevel

    business_impact: (
        BusinessImpactType
    )


class ProblemOutput(
    PRISMBaseModel
):

    problems: list[
        DetectedProblem
    ]

# =========================================================
# ROOT CAUSE ANALYSIS
# =========================================================

class RootCause(
    PRISMBaseModel
):

    problem_id: str = Field(
        ...,
        min_length=1
    )

    problem_type: ProblemType

    root_cause: str = Field(
        ...,
        min_length=15
    )

    evidence_summary: str = Field(
        ...,
        min_length=10
    )

    confidence_level: ConfidenceLevel

class RootCauseOutput(
    PRISMBaseModel
):

    root_causes: list[
        RootCause
    ]

# =========================================================
# DECISION ENGINE
# =========================================================

class DecisionTrace(
    PRISMBaseModel
):

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



class Decision(
    PRISMBaseModel
):

    priority_rank: (
        Optional[int]
    ) = None

    action: str = Field(
        ...,
        min_length=3
    )
    root_cause: str = Field(
        ...,
        min_length=10,
        description=(
            "Underlying reason why "
            "the problem occurs"
        )
    )

    business_outcome: str = Field(
        ...,
        min_length=5,
        description=(
            "Expected business outcome "
            "if implemented"
        )
    )

    success_metric: str = Field(
        ...,
        min_length=3,
        description=(
            "Primary metric expected "
            "to improve"
        )
    )

    decision_rationale: str = Field(
        ...,
        min_length=10,
        description=(
            "Evidence-based reasoning "
            "behind this recommendation"
        )
    )

    expected_impact: str = Field(
        ...,
        min_length=3
    )

    impact_range: str = Field(
        ...,
        min_length=3
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

    rice_score: (
        Optional[float]
    ) = None

    confidence_level: (
        ConfidenceLevel
    )

    implementation_hint: str = Field(
        ...,
        min_length=5
    )

    trace: DecisionTrace



# =========================================================
# HEALTH SCORE
# =========================================================

class HealthDimensions(
    PRISMBaseModel
):

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


class DecisionOutput(
    PRISMBaseModel
):

    decisions: list[
        Decision
    ]

    product_health_score: (
        Optional[float]
    ) = None

    health_dimensions: (
        Optional[
            HealthDimensions
        ]
    ) = None


# =========================================================
# FINAL RESPONSE
# =========================================================

class PRISMAnalysisResponse(
    PRISMBaseModel
):

    product: ProductUnderstanding

    simulation: SimulationOutput

    problems: ProblemOutput

    root_causes: RootCauseOutput

    decisions: DecisionOutput

    analyzed_at: datetime = Field(
        default_factory=lambda:
        datetime.now(UTC)
    )

    pipeline_version: str = (
        "2.5"
    )

# =========================================================
# API RESPONSE
# =========================================================

class APIResponse(
    PRISMBaseModel
):

    status: str

    data: Optional[
        PRISMAnalysisResponse
    ] = None

    message: Optional[str] = None